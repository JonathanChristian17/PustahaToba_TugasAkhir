"""API HTTP lokal tipis yang menghubungkan React (04) ke Backend R50 (02) dan Modul Transliterasi (03)."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np

WEB_APP_ROOT = Path(__file__).resolve().parents[1]
REPO_PROGRAM = WEB_APP_ROOT.parent
PACKAGE_02 = REPO_PROGRAM / "01_model"
BACKEND_APP_DIR = PACKAGE_02 / "aplikasi"
DEV_03 = REPO_PROGRAM / "02_transliteration"
MODULE_03_DIR = DEV_03 / "02_MODUL_TRANSLITERASI"
LEXICON_V2_PATH = DEV_03 / "01_ATURAN/KOSAKATA_EKSTERNAL/kosakata_toba_v2.json"

for path in (BACKEND_APP_DIR, MODULE_03_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import backend as pkg02_backend  # noqa: E402
import visual as pkg02_visual  # noqa: E402
import susun_prediksi  # noqa: E402
from transliterasi import Transliterator  # noqa: E402
from collections import OrderedDict  # noqa: E402

HOST = os.environ.get("PUSTAHA_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT") or os.environ.get("PUSTAHA_API_PORT", "8503"))
_PREDICTOR = None
_PREDICTOR_LOCK = threading.Lock()
_RENDER_CACHE: OrderedDict[str, dict] = OrderedDict()
_RENDER_LOCK = threading.Lock()
_LEXICON_V2 = json.loads(LEXICON_V2_PATH.read_text(encoding="utf-8"))
_RULES_ENGINE = Transliterator()

_SAMPLE_MAP = {
    "P07_N10": (10, WEB_APP_ROOT / "public/samples/ID010_P07_N10_010.png"),
    "P07_N08": (8, WEB_APP_ROOT / "public/samples/ID008_P07_N08_008.png"),
    "P07_N19": (19, WEB_APP_ROOT / "public/samples/ID019_P07_N19_019.png"),
    "P10_N06": (37, WEB_APP_ROOT / "public/samples/ID037_P10_N06_006.png"),
}


def _cache_put(key: str, rgb: np.ndarray, items: list[dict]) -> None:
    with _RENDER_LOCK:
        _RENDER_CACHE[key] = {"rgb": rgb, "items": copy.deepcopy(items)}
        _RENDER_CACHE.move_to_end(key)
        while len(_RENDER_CACHE) > 16:
            _RENDER_CACHE.popitem(last=False)


def _load_sample_adapted(image_id: int) -> list[dict]:
    meta_path = PACKAGE_02 / "eksperimen/DATASET/testing/instances.json"
    if not meta_path.is_file():
        meta_path = PACKAGE_02 / "eksperimen/hasil_evaluasi_R50_30epoch/instances_acuan.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    preds = json.loads(
        (PACKAGE_02 / "eksperimen/hasil_evaluasi_R50_30epoch/predictions.json").read_text(encoding="utf-8")
    )
    names = {c["id"]: c["name"] for c in meta["categories"]}
    testing_dir = DEV_03 / "04_PENGUJIAN"
    if str(testing_dir) not in sys.path:
        sys.path.insert(0, str(testing_dir))
    from uji_testing_tersimpan import adapt_predictions  # noqa: E402

    raw_pairs = [(i, p) for i, p in enumerate(preds) if p["image_id"] == image_id]
    adapted = adapt_predictions(raw_pairs, names)
    num = 0
    for item, (_, orig) in zip(adapted, raw_pairs):
        item["segmentation"] = orig.get("segmentation")
        if item["displayed"]:
            num += 1
            item["display_number"] = num
    return adapted


def _get_render_entry(cache_key: str) -> dict | None:
    with _RENDER_LOCK:
        if cache_key in _RENDER_CACHE:
            _RENDER_CACHE.move_to_end(cache_key)
            return _RENDER_CACHE[cache_key]
    if cache_key in _SAMPLE_MAP:
        image_id, img_path = _SAMPLE_MAP[cache_key]
        if img_path.is_file():
            rgb = pkg02_backend.decode_upload(img_path.read_bytes())
            adapted = _load_sample_adapted(image_id)
            visible = [it for it in adapted if it["displayed"]]
            _cache_put(cache_key, rgb, visible)
            return _RENDER_CACHE.get(cache_key)
    return None


def render_overlay_png_bytes(
    cache_key: str,
    mode: str = "Mask + Bbox",
    opacity: float = 0.65,
    focus: int | None = None,
) -> bytes:
    """Render overlay Detectron2/visual.py langsung dengan warna unik tiap instansi khusus pada mask."""
    entry = _get_render_entry(cache_key)
    if entry is None:
        raise KeyError("Citra tidak ditemukan di cache render sesi; unggah atau proses ulang citra.")
    opacity_clamped = max(0.05, min(0.95, float(opacity)))
    safe_mode = "Mask + Bbox" if mode == "raw_image" else mode
    original, overlay, _ = pkg02_visual.render_pair(
        entry["rgb"],
        entry["items"],
        mode=safe_mode,
        opacity=opacity_clamped,
        focus=focus,
    )
    target_img = original if mode == "raw_image" else overlay
    return pkg02_backend.png_bytes(target_img)


def get_predictor():
    global _PREDICTOR
    with _PREDICTOR_LOCK:
        if _PREDICTOR is None:
            _PREDICTOR = pkg02_backend.Predictor()
        return _PREDICTOR


def mask_to_pct_polygons(segmentation: dict, img_h: int, img_w: int) -> list[list[list[float]]]:
    """Ekstrak poligon terluar RLE mask dalam koordinat persen 0..100 untuk overlay SVG."""
    if not segmentation or img_h <= 0 or img_w <= 0:
        return []
    from pycocotools import mask as mask_utils

    bitmap = mask_utils.decode(segmentation).astype(np.uint8)
    contours, _ = cv2.findContours(bitmap, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    polys = []
    for cnt in contours:
        if len(cnt) < 3 or cv2.contourArea(cnt) < 4:
            continue
        eps = 0.008 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, eps, True)
        pts = [
            [
                round(float(p[0][0]) / img_w * 100.0, 2),
                round(float(p[0][1]) / img_h * 100.0, 2),
            ]
            for p in approx
        ]
        if len(pts) >= 3:
            polys.append(pts)
    return polys


def build_predict_payload(
    rgb: np.ndarray,
    raw_result: dict,
    model_identity: dict,
    lexicon: dict | None = None,
    include_research_exports: bool = True,
) -> dict:
    """Jalankan arrange() pada salinan hasil inferensi tanpa mutasi prediksi asli."""
    snapshot = copy.deepcopy(raw_result)
    lex = _LEXICON_V2 if lexicon is None else lexicon
    translit = susun_prediksi.arrange(snapshot, lexicon=lex)

    h, w = raw_result["input_hw"]
    visible_preds = pkg02_backend.displayed(raw_result)
    detections_ui = []
    for item in visible_preds:
        x1, y1, x2, y2 = item["bbox_xyxy"]
        cid = item["category_id"]
        label = item["class_label"]
        pretty = label.replace("ina_", "").replace("anak_", "").replace("_", " ").title()
        if label.startswith("ina_") and len(pretty) <= 3:
            pretty = pretty.capitalize()
        detections_ui.append(
            {
                "id": item["instance_id"],
                "instance_id": item["instance_id"],
                "display_number": item["display_number"],
                "category_id": cid,
                "cls": pretty,
                "rawClass": label,
                "kind": "Ina" if cid < 19 else "Anak",
                "score": item["score"],
                "bbox_xyxy": list(item["bbox_xyxy"]),
                "box": [
                    round(x1 / w * 100.0, 2),
                    round(y1 / h * 100.0, 2),
                    round((x2 - x1) / w * 100.0, 2),
                    round((y2 - y1) / h * 100.0, 2),
                ],
                "polygons": mask_to_pct_polygons(item.get("segmentation"), h, w),
            }
        )

    exports = {}
    if include_research_exports and rgb is not None:
        files = pkg02_backend.export_files(rgb, raw_result, mode="Mask + Bbox")
        exports = {
            "overlay_png_b64": base64.b64encode(files["overlay.png"]).decode("ascii"),
            "predictions_json_text": files["predictions.json"].decode("utf-8"),
            "karakter_csv_text": files["karakter.csv"].decode("utf-8-sig"),
        }

    # Normalisasi tuple ke JSON-safe list agar konsisten dengan ekspor JSON
    translit_safe = json.loads(json.dumps(translit, ensure_ascii=False))

    return {
        "source_name": raw_result.get("source_name"),
        "source_sha256": raw_result.get("source_sha256"),
        "input_hw": raw_result.get("input_hw"),
        "display_threshold": raw_result.get("display_threshold", pkg02_backend.DISPLAY_THRESHOLD),
        "inference_seconds": raw_result.get("inference_seconds_excluding_load_and_resize"),
        "model_identity": {
            **dict(model_identity),
            "architecture": raw_result.get("model", "Mask R-CNN ResNet-50-FPN"),
            "dataset_version": raw_result.get("dataset_version"),
        },
        "lexicon": {
            "language": lex.get("language"),
            "source": lex.get("source"),
            "revision": lex.get("revision"),
            "license": lex.get("license"),
            "file": LEXICON_V2_PATH.name,
        },
        "detections": detections_ui,
        "displayed_count": len(visible_preds),
        "raw_prediction_count": len(raw_result.get("predictions", [])),
        "raw_predictions_source": [
            {
                "instance_id": p["instance_id"],
                "display_number": p.get("display_number"),
                "category_id": p["category_id"],
                "class_label": p["class_label"],
                "score": p["score"],
                "bbox_xyxy": list(p["bbox_xyxy"]),
                "displayed": p["displayed"],
            }
            for p in raw_result.get("predictions", [])
        ],
        "transliteration": translit_safe,
        "research_exports": exports,
    }


def _json_response(handler: BaseHTTPRequestHandler, status: int, data: dict) -> None:
    body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


class PustahaApiHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "service": "pustaha-toba-api",
                    "health": "/api/health",
                    "module_version": susun_prediksi.VERSION,
                },
            )
            return
        if self.path == "/api/health":
            plan, _names = pkg02_backend.verify_artifacts()
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "backend_loaded": _PREDICTOR is not None,
                    "model_identity": {
                        "architecture": "Mask R-CNN ResNet-50-FPN",
                        "backbone_depth": plan["backbone_depth"],
                        "epochs": plan["epochs"],
                        "epoch": 28,
                        "checkpoint_sha256": pkg02_backend.CHECKPOINT_HASH,
                        "display_threshold": pkg02_backend.DISPLAY_THRESHOLD,
                    },
                    "module_version": susun_prediksi.VERSION,
                    "rules_version": _RULES_ENGINE.version,
                    "lexicon_file": LEXICON_V2_PATH.name,
                },
            )
            return
        _json_response(self, HTTPStatus.NOT_FOUND, {"error": "Endpoint tidak ditemukan."})

    def do_POST(self):
        if self.path == "/api/render":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                cache_key = str(body.get("cache_key") or "")
                mode = str(body.get("mode") or "Mask + Bbox")
                opacity = float(body.get("opacity", 0.65))
                focus = body.get("focus")
                focus_num = int(focus) if focus is not None else None
                png_data = render_overlay_png_bytes(cache_key, mode=mode, opacity=opacity, focus=focus_num)
                _json_response(
                    self,
                    HTTPStatus.OK,
                    {"overlay_png_b64": base64.b64encode(png_data).decode("ascii")},
                )
            except KeyError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"error": str(err)})
            except Exception as err:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"error": f"Render overlay gagal: {err}"})
            return

        if self.path == "/api/sample":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                sample_id = str(body.get("sample_id") or "")
                if sample_id not in _SAMPLE_MAP:
                    _json_response(self, HTTPStatus.NOT_FOUND, {"error": f"Sampel tidak dikenal: {sample_id}"})
                    return
                image_id, img_path = _SAMPLE_MAP[sample_id]
                img_bytes = img_path.read_bytes()
                rgb = pkg02_backend.decode_upload(img_bytes)
                adapted = _load_sample_adapted(image_id)
                raw_doc = {
                    "schema_version": 1,
                    "source_name": img_path.name,
                    "source_sha256": hashlib.sha256(img_bytes).hexdigest(),
                    "input_hw": list(rgb.shape[:2]),
                    "model": "Mask R-CNN ResNet-50-FPN",
                    "dataset_version": "Aksarabataktoba_1535_citra_4088_instansi",
                    "checkpoint_sha256": susun_prediksi.CHECKPOINT_HASH,
                    "display_threshold": pkg02_backend.DISPLAY_THRESHOLD,
                    "predictions": adapted,
                }
                _cache_put(sample_id, rgb, pkg02_backend.displayed(raw_doc))
                model_id = {
                    "backbone_depth": 50,
                    "epoch": 28,
                    "checkpoint_sha256": susun_prediksi.CHECKPOINT_HASH,
                    "training_run": "Aksarabataktoba_30_epoch_R50",
                }
                payload = build_predict_payload(rgb, raw_doc, model_id, include_research_exports=True)
                payload["cache_key"] = sample_id
                _json_response(self, HTTPStatus.OK, payload)
            except Exception as err:
                _json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Sampel gagal diproses: {err}"})
            return

        if self.path != "/api/predict":
            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "Endpoint tidak ditemukan."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)
            body = json.loads(raw_body.decode("utf-8"))
            filename = str(body.get("filename") or "unggahan.png")
            b64 = str(body.get("image_base64") or "")
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            img_bytes = base64.b64decode(b64)
            rgb = pkg02_backend.decode_upload(img_bytes)
            src_hash = hashlib.sha256(img_bytes).hexdigest()

            predictor = get_predictor()
            raw_result = predictor.predict(rgb, filename, src_hash)
            _cache_put(src_hash, rgb, pkg02_backend.displayed(raw_result))
            payload = build_predict_payload(rgb, raw_result, predictor.model_identity)
            payload["cache_key"] = src_hash
            _json_response(self, HTTPStatus.OK, payload)
        except ValueError as err:
            _json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(err)})
        except Exception as err:
            _json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Inferensi gagal: {err}"})


def main():
    server = ThreadingHTTPServer((HOST, PORT), PustahaApiHandler)
    print(f"Pustaha Toba API (R50 Ep.28 + Transliterasi {susun_prediksi.VERSION}) aktif di http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
