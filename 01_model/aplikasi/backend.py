"""Inferensi citra tunggal dengan checkpoint R50 epoch 28 yang diverifikasi."""
import csv
import hashlib
import io
import json
import math
import sys
import threading
import time
import warnings
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

BASE = Path(__file__).resolve().parent
PACKAGE = BASE.parent
RUN = PACKAGE / "eksperimen/hasil_train_R50"
OUTPUT_ROOT = PACKAGE / "hasil_demo"
EXPECTED = json.loads((PACKAGE / "model/identitas.json").read_text(encoding="utf-8"))
CHECKPOINT_HASH = EXPECTED["checkpoint_sha256"]
FROZEN_HASH = EXPECTED["contract_sha256"]
MAX_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 20_000_000
DISPLAY_THRESHOLD = 0.5

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def decode_upload(payload):
    """Validasi ukuran, format, EXIF dan transparansi pada salinan input."""
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError("Ukuran berkas harus lebih dari 0 dan maksimal 20 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(payload)) as source:
                if source.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ValueError("Gunakan PNG, JPG, JPEG atau WebP.")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValueError("Gunakan citra statis satu frame.")
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError("Resolusi maksimal 20 megapiksel. Gunakan crop aksara yang lebih kecil.")
                oriented = ImageOps.exif_transpose(source).convert("RGBA")
                white = Image.new("RGBA", oriented.size, (255, 255, 255, 255))
                rgb = Image.alpha_composite(white, oriented).convert("RGB")
                return np.asarray(rgb).copy()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise ValueError("Berkas tidak dapat dibaca sebagai citra yang valid.") from error


def verify_artifacts():
    """Periksa bobot, seleksi validasi, konfigurasi dan kode tanpa membaca GT."""
    for relative, digest in EXPECTED["artifact_sha256"].items():
        if sha256(PACKAGE / relative) != digest:
            raise ValueError(f"Artefak model berubah: {relative}")
    if sha256(RUN / "model_best.pth") != CHECKPOINT_HASH:
        raise ValueError("Checkpoint tidak sesuai dengan model R50 terpilih.")
    contract = read_json(PACKAGE / "model/kontrak_run.json")
    history = read_json(PACKAGE / "model/riwayat.json")
    best = max(history, key=lambda row: row["validasi"]["AP"])
    if best["epoch"] != 28 or best["validasi"]["AP"] != EXPECTED["validation_AP"]:
        raise ValueError("Seleksi model berbeda dari riwayat validasi.")
    p = dict(contract["pengaturan"])
    if p["backbone_depth"] != 50 or p["epochs"] != 30:
        raise ValueError("Konfigurasi bukan R50 dengan pelatihan 30 epoch.")
    names = {c["id"]: c["name"] for c in read_json(PACKAGE / "model/class_map.json")}
    if set(names) != set(range(25)) or len(set(names.values())) != 25:
        raise ValueError("Peta kelas harus memuat 25 kelas dengan ID 0-24.")
    p["dataset_version"] = "Aksarabataktoba_1535_citra_4088_instansi"
    return p, names


class Predictor:
    """Pemuatan checkpoint hasil pelatihan; inferensi tidak memerlukan anotasi."""
    def __init__(self):
        import torch
        from detectron2.modeling import build_model
        self.plan, self.names = verify_artifacts()
        if not torch.cuda.is_available():
            raise RuntimeError("GPU CUDA belum tersedia. Gunakan environment penelitian pada WSL.")
        sys.path.insert(0, str(PACKAGE / "model/kode"))
        from normalisasi_model import config
        from resize_augmentasi import inference_input
        torch.set_num_threads(2)
        checkpoint = torch.load(RUN / "model_best.pth", map_location="cpu", weights_only=True)
        if checkpoint["epoch"] != 28 or checkpoint["smoke"] or checkpoint["validasi"]["AP"] != EXPECTED["validation_AP"]:
            raise ValueError("Identitas checkpoint berbeda dari model yang dipilih.")
        self.model = build_model(config(self.plan, device="cpu"))
        self.model.load_state_dict(checkpoint["model"], strict=True)
        del checkpoint
        self.model.to("cuda").eval()
        blocks = tuple(len(getattr(self.model.backbone.bottom_up, f"res{i}")) for i in range(2,6))
        if blocks != (3,4,6,3):
            raise ValueError("Backbone termuat bukan ResNet-50.")
        self.model_identity = {"backbone_depth":50,"epoch":28,"step":41748,
                               "blocks":list(blocks),"checkpoint_sha256":CHECKPOINT_HASH,
                               "training_run":"Aksarabataktoba_30_epoch_R50"}
        self.prepare = inference_input
        self.lock = threading.Lock()
        self.gpu = torch.cuda.get_device_name(0)

    def predict(self, rgb, source_name, source_hash):
        import torch
        from pycocotools import mask as mask_utils
        with self.lock:
            sample = self.prepare(rgb, 0, self.plan)
            if "instances" in sample or "annotations" in sample:
                raise RuntimeError("Input inferensi mengandung anotasi.")
            torch.cuda.synchronize()
            start = time.perf_counter()
            with torch.inference_mode():
                instances = self.model([sample])[0]["instances"].to("cpu")
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - start
        if instances.image_size != rgb.shape[:2]:
            raise RuntimeError("Ukuran mask keluaran tidak sama dengan input.")
        predictions = []
        for index in range(len(instances)):
            category = int(instances.pred_classes[index])
            score = float(instances.scores[index])
            box = instances.pred_boxes.tensor[index].tolist()
            bitmap = instances.pred_masks[index].numpy().astype(np.uint8)
            if category not in self.names or not math.isfinite(score) or not 0 <= score <= 1 or not np.isfinite(box).all():
                raise RuntimeError("Keluaran model tidak valid.")
            encoded = mask_utils.encode(np.asfortranarray(bitmap))
            encoded["counts"] = encoded["counts"].decode("ascii")
            predictions.append({"instance_id": index + 1, "category_id": category,
                                "class_label": self.names[category], "score": score,
                                "bbox_xyxy": box, "segmentation": encoded,
                                "displayed": score >= DISPLAY_THRESHOLD})
        number = 0
        for item in predictions:
            if item["displayed"]:
                number += 1
                item["display_number"] = number
        return {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_name": Path(source_name.replace("\\", "/")).name,
                "source_sha256": source_hash, "input_hw": list(rgb.shape[:2]),
                "model": "Mask R-CNN ResNet-50-FPN", "dataset_version": self.plan["dataset_version"],
                "training_run": RUN.name, "checkpoint_sha256": CHECKPOINT_HASH,
                "frozen_sha256": FROZEN_HASH, "gpu": self.gpu,
                "inference_seconds_excluding_load_and_resize": elapsed,
                "ap_score_threshold": self.plan["ap_score_threshold"], "display_threshold": DISPLAY_THRESHOLD,
                "nms_threshold": self.plan["nms_threshold"], "max_detections": self.plan["max_detections"],
                "ground_truth_used": False, "training_performed": False, "transliteration": False,
                "list_order": "model_confidence_order_not_reading_order",
                "displayed_instances": number,
                "class_counts": dict(Counter(p["class_label"] for p in predictions if p["displayed"])),
                "predictions": predictions}


def displayed(result):
    return [item for item in result["predictions"] if item["displayed"]]


def table_rows(result):
    return [{"No.": p["display_number"], "Kelas prediksi": p["class_label"],
             "Confidence (%)": p["score"] * 100,
             "Bounding box [x1, y1, x2, y2]": ", ".join(f"{v:.1f}" for v in p["bbox_xyxy"])}
            for p in displayed(result)]


def render_overlay(rgb, result, opacity=0.65, focus=None, mode="Mask + Bbox"):
    from visual import render_pair
    return render_pair(rgb, displayed(result), mode, opacity, focus=focus)[1]


def open_result_folder(path):
    """Buka direktori keluaran lokal hanya dari tindakan tombol pengguna."""
    import os
    import subprocess
    target = Path(path).resolve()
    root = OUTPUT_ROOT.resolve()
    if root not in target.parents or not target.is_dir():
        raise ValueError("Folder bukan keluaran aplikasi ini.")
    if os.name == "nt":
        os.startfile(str(target))
    else:
        explorer = Path("/mnt/c/Windows/explorer.exe")
        if not explorer.is_file():
            raise RuntimeError("Pembukaan folder memerlukan Windows/WSL lokal.")
        windows_path = subprocess.run(["wslpath", "-w", str(target)], check=True, capture_output=True, text=True).stdout.strip()
        subprocess.Popen([str(explorer), windows_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def png_bytes(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def export_files(rgb, result, opacity=0.65, mode="Mask + Bbox"):
    """Ekspor semua instance tampil; fokus layar tidak membuang instance."""
    text = io.StringIO(newline="")
    fields = ["nomor", "instance_id", "category_id", "class_label", "confidence", "x1", "y1", "x2", "y2"]
    writer = csv.DictWriter(text, fieldnames=fields)
    writer.writeheader()
    for p in displayed(result):
        writer.writerow({"nomor": p["display_number"], "instance_id": p["instance_id"],
                         "category_id": p["category_id"], "class_label": p["class_label"],
                         "confidence": p["score"], **dict(zip(["x1", "y1", "x2", "y2"], p["bbox_xyxy"]))})
    manifest = dict(result)
    manifest["overlay_opacity"] = opacity
    manifest["overlay_layout"] = "SPACED_CALLOUTS_V2"
    manifest["display_mode"] = mode
    from visual import render_pair
    _, overlay, layout = render_pair(rgb, displayed(result), mode, opacity)
    manifest["overlay_coordinate_offsets"] = layout
    manifest["coordinate_space"] = "input_rgb.png; overlay adds annotation margins without resizing input pixels"
    manifest["application_code_sha256"] = {name: sha256(BASE / name) for name in ["app.py", "backend.py", "visual.py"]}
    return {"input_rgb.png": png_bytes(Image.fromarray(rgb)),
            "overlay.png": png_bytes(overlay),
            "predictions.json": json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8"),
            "karakter.csv": text.getvalue().encode("utf-8-sig")}


def zip_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def save_result(files):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = OUTPUT_ROOT / stamp
    out.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        if name not in {"input_rgb.png", "overlay.png", "predictions.json", "karakter.csv"}:
            raise ValueError("Nama output tidak diizinkan.")
        (out / name).write_bytes(content)
    return out
