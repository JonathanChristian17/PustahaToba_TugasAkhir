"""Pengujian integrasi API backend (04_WEB_APP_BATAK_TOBA/server) dengan Paket 02 dan Modul 03."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_02 = ROOT.parent / "02_AKSARABATAKTOBA_TERBARU"
WEB_SERVER_DIR = ROOT.parent / "04_WEB_APP_BATAK_TOBA/server"
MODUL_DIR = ROOT / "02_MODUL_TRANSLITERASI"

for p in (WEB_SERVER_DIR, MODUL_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import api_server  # noqa: E402
import susun_prediksi  # noqa: E402
from uji_testing_tersimpan import adapt_predictions  # noqa: E402


def _dummy_seg(h=120, w=240):
    return {"size": [h, w], "counts": "eNqL0QAA"}


class TestWebReactBackendIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads(
            (PACKAGE_02 / "eksperimen/DATASET/testing/instances.json").read_text(encoding="utf-8")
        )
        cls.predictions = json.loads(
            (PACKAGE_02 / "eksperimen/hasil_evaluasi_R50_30epoch/predictions.json").read_text(
                encoding="utf-8"
            )
        )
        cls.names = {c["id"]: c["name"] for c in cls.meta["categories"]}
        cls.by_img = {im["id"]: im for im in cls.meta["images"]}
        cls.lexicon = json.loads(
            (ROOT / "01_ATURAN/KOSAKATA_EKSTERNAL/kosakata_toba_v2.json").read_text(
                encoding="utf-8"
            )
        )

    def _make_raw_doc(self, image_id, name="sample.png"):
        im = self.by_img[image_id]
        raw_pairs = [(i, p) for i, p in enumerate(self.predictions) if p["image_id"] == image_id]
        preds = adapt_predictions(raw_pairs, self.names)
        num = 0
        for p, (_, orig) in zip(preds, raw_pairs):
            p["segmentation"] = orig.get("segmentation") or _dummy_seg(im["height"], im["width"])
            if p["displayed"]:
                num += 1
                p["display_number"] = num
        return {
            "schema_version": 1,
            "source_name": name,
            "source_sha256": "0" * 64,
            "input_hw": [im["height"], im["width"]],
            "model": "Mask R-CNN ResNet-50-FPN",
            "dataset_version": "Aksarabataktoba_1535_citra_4088_instansi",
            "checkpoint_sha256": susun_prediksi.CHECKPOINT_HASH,
            "display_threshold": 0.50,
            "predictions": preds,
        }

    def test_api_payload_matches_direct_arrange_and_preserves_raw_predictions(self):
        model_id = {"backbone_depth": 50, "epoch": 28, "checkpoint_sha256": susun_prediksi.CHECKPOINT_HASH}
        for img_id in (94, 31, 49, 51):
            doc = self._make_raw_doc(img_id, f"uji_{img_id}.png")
            before = copy.deepcopy(doc)

            payload = api_server.build_predict_payload(
                None, doc, model_id, include_research_exports=False
            )
            direct = json.loads(
                json.dumps(
                    susun_prediksi.arrange(copy.deepcopy(doc), lexicon=self.lexicon),
                    ensure_ascii=False,
                )
            )

            self.assertEqual(payload["transliteration"], direct)
            self.assertEqual(doc, before)
            self.assertEqual(payload["model_identity"]["epoch"], 28)
            self.assertNotIn("cer", payload)
            self.assertNotIn("accuracy", payload)

    def test_zero_predictions_payload_clean_and_no_fake_text(self):
        doc = {
            "schema_version": 1,
            "source_name": "kosong.png",
            "source_sha256": "1" * 64,
            "input_hw": [120, 240],
            "model": "Mask R-CNN ResNet-50-FPN",
            "checkpoint_sha256": susun_prediksi.CHECKPOINT_HASH,
            "display_threshold": 0.50,
            "predictions": [
                {
                    "instance_id": 1,
                    "category_id": 0,
                    "class_label": "ina_a",
                    "score": 0.42,
                    "bbox_xyxy": [10.0, 10.0, 40.0, 50.0],
                    "segmentation": _dummy_seg(),
                    "displayed": False,
                }
            ],
        }
        payload = api_server.build_predict_payload(
            None, doc, {"backbone_depth": 50, "epoch": 28}, include_research_exports=False
        )
        self.assertEqual(payload["displayed_count"], 0)
        self.assertEqual(payload["transliteration"]["text_status"], "NO_PREDICTIONS")
        self.assertEqual(payload["transliteration"]["text_automatic"], "")

    def test_tied_confidence_and_unpaired_sign_handled_per_contract(self):
        def cid(lbl):
            return next(k for k, v in self.names.items() if v == lbl)

        doc = {
            "schema_version": 1,
            "source_name": "seri.png",
            "source_sha256": "2" * 64,
            "input_hw": [120, 240],
            "model": "Mask R-CNN ResNet-50-FPN",
            "checkpoint_sha256": susun_prediksi.CHECKPOINT_HASH,
            "display_threshold": 0.50,
            "predictions": [
                {
                    "instance_id": 1,
                    "display_number": 1,
                    "category_id": cid("ina_ha"),
                    "class_label": "ina_ha",
                    "score": 0.90,
                    "bbox_xyxy": [20.0, 30.0, 55.0, 70.0],
                    "displayed": True,
                },
                {
                    "instance_id": 2,
                    "display_number": 2,
                    "category_id": cid("ina_ba"),
                    "class_label": "ina_ba",
                    "score": 0.90,
                    "bbox_xyxy": [20.0, 30.0, 55.0, 70.0],
                    "displayed": True,
                },
                {
                    "instance_id": 3,
                    "display_number": 3,
                    "category_id": cid("anak_hauluan"),
                    "class_label": "anak_hauluan",
                    "score": 0.85,
                    "bbox_xyxy": [210.0, 35.0, 225.0, 55.0],
                    "displayed": True,
                },
            ],
        }
        payload = api_server.build_predict_payload(
            None, doc, {"backbone_depth": 50, "epoch": 28}, include_research_exports=False
        )
        tr = payload["transliteration"]
        self.assertEqual(tr["text_status"], "NEEDS_REVIEW")
        self.assertEqual(tr["text_automatic"], "[ha / ba]")
        self.assertTrue(
            any(a["anak_id"] == 3 and a["status"] == "UNPAIRED" for a in tr["assignments"])
        )

    def test_detectron_overlay_render_distinct_opacity_only_on_mask_without_mutation(self):
        doc = self._make_raw_doc(10, "ID010_P07_N10_010.png")
        before = copy.deepcopy(doc)
        png_low = api_server.render_overlay_png_bytes("P07_N10", mode="Mask", opacity=0.25, focus=None)
        png_high = api_server.render_overlay_png_bytes("P07_N10", mode="Mask", opacity=0.80, focus=1)
        png_bbox = api_server.render_overlay_png_bytes("P07_N10", mode="Mask + Bbox", opacity=0.65, focus=None)
        self.assertTrue(png_low.startswith(b"\x89PNG"))
        self.assertTrue(png_high.startswith(b"\x89PNG"))
        self.assertTrue(png_bbox.startswith(b"\x89PNG"))
        self.assertNotEqual(png_low, png_high)
        self.assertEqual(doc, before)


if __name__ == "__main__":
    unittest.main()
