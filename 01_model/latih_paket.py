"""Peluncur training dengan dependensi lokal tanpa mengubah sumber eksperimen."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    control = argparse.ArgumentParser(add_help=False)
    control.add_argument("--mulai-training", action="store_true")
    control.add_argument("--stop-after-epoch", type=int, default=30)
    flags, remaining = control.parse_known_args()
    if flags.stop_after_epoch != 30:
        control.error("Pelatihan paket ditetapkan 30 epoch; --stop-after-epoch harus 30.")
    if "--help" not in remaining and "-h" not in remaining and "--smoke" not in remaining:
        remaining += ["--stop-after-epoch", "30"]
    inspection = "--audit-only" in remaining or "--check-resume" in remaining
    help_requested = "--help" in remaining or "-h" in remaining
    if not inspection and not flags.mulai_training and not help_requested:
        control.error("Gunakan --audit-only atau --check-resume untuk pemeriksaan; pelatihan memerlukan --mulai-training.")
    sys.path.insert(0, str(ROOT / "eksperimen"))
    sys.path.insert(0, str(ROOT / "pendukung"))
    import train_Aksarabataktoba as trainer
    trainer.PREVIOUS = ROOT / "pendukung"
    if not help_requested:
        manifest = json.loads((ROOT / "pendukung/ASAL_KONFIGURASI.json").read_text(encoding="utf-8"))
        config_path = trainer.PREVIOUS / "02_KONFIGURASI/eksperimen.json"
        if fingerprint(config_path) != manifest["sha256"]:
            raise ValueError("Konfigurasi pendukung berbeda dari salinan sumber.")
        parameters = json.loads(config_path.read_text(encoding="utf-8"))
        keys = ("epochs", "learning_rate", "momentum", "weight_decay", "warmup_steps",
                "lr_milestone_epochs", "lr_gamma", "amp", "amp_max_attempts")
        for run in ("hasil_train_R50", "hasil_train_R101"):
            contract = json.loads((ROOT / "eksperimen" / run / "kontrak_run.json").read_text(encoding="utf-8"))
            if any(parameters[key] != contract["pengaturan"][key] for key in keys):
                raise ValueError(f"Parameter pendukung berbeda dari kontrak {run}.")
        if parameters["epochs"] != 30:
            raise ValueError("Durasi pelatihan paket harus 30 epoch.")
        from batak import pretrained_r50, pretrained_r101
        for module, filename in (
            (pretrained_r50, "detectron2_mask_rcnn_R50_FPN_3x_f10217.pkl"),
            (pretrained_r101, "detectron2_mask_rcnn_R101_FPN_3x_a3ec72.pkl"),
        ):
            source = Path.home() / "skripsi-batak-toba/cache_torch/checkpoints" / filename
            if not source.is_file():
                raise FileNotFoundError(f"Bobot pralatih belum tersedia: {source}")
            if fingerprint(source) != module.SOURCE_SHA256:
                raise ValueError(f"SHA256 bobot pralatih tidak cocok: {filename}")
        print("LULUS: konfigurasi lokal dan SHA256 bobot COCO R50/R101 sesuai.", flush=True)
    sys.argv = [str(ROOT / "eksperimen/train_Aksarabataktoba.py"), *remaining]
    trainer.main()


if __name__ == "__main__":
    main()
