"""Bandingkan bacaan dengan acuan audit; GT hanya untuk diagnosis terpisah.

Tidak memuat model, menulis anotasi, atau memasukkan jawaban PDF ke mesin.
"""
import argparse
from collections import Counter
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT.parent / "02_AKSARABATAKTOBA_TERBARU"
BASELINE = ROOT / "05_HASIL/TESTING_131_20261117T102933620328Z"
sys.path.insert(0, str(ROOT / "02_MODUL_TRANSLITERASI"))
from susun_prediksi import arrange, CHECKPOINT_HASH, VERSION


def norm(value):
    return re.sub(r"\s+", "", value).casefold()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def gt_diagnostic(annotations, names):
    # score=1 hanya adaptor antarmuka internal, BUKAN confidence model.
    # Semua instansi GT disertakan; tidak ada confidence GT atau evaluasi baru.
    rows = []
    for annotation in annotations:
        x, y, w, h = annotation["bbox"]
        rows.append({"instance_id": annotation["id"],
                     "category_id": annotation["category_id"],
                     "class_label": names[annotation["category_id"]],
                     "bbox_xyxy": [x, y, x+w, y+h],
                     "score": 1.0, "displayed": True})
    return arrange({"checkpoint_sha256": CHECKPOINT_HASH,
                    "display_threshold": .5, "predictions": rows,
                    "input_kind": "GT_BBOX_DIAGNOSTIC_NOT_MODEL_OUTPUT; SCORE_IS_ADAPTER_PLACEHOLDER"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hasil", type=Path, required=True,
                        help="Folder hasil batch versi saat ini, sudah ada.")
    args = parser.parse_args()
    batch = args.hasil.resolve()
    out = batch / "AUDIT_BACAAN_DAN_GT"
    if out.exists():
        raise FileExistsError("Folder audit sudah ada; hasil lama tidak ditimpa.")
    meta_path = PACKAGE / "eksperimen/DATASET/testing/instances.json"
    reference_path = BASELINE / "AUDIT_TEKS_DAN_AKSARA/audit_terstruktur.json"
    source_paths = [meta_path, reference_path, batch/"RINGKASAN.json",
                    ROOT/"00_ACUAN/ITEM_RESPONDEN_V6.csv",
                    ROOT/"01_ATURAN/peta_aksara.json",
                    ROOT/"02_MODUL_TRANSLITERASI/susun_prediksi.py",
                    ROOT/"02_MODUL_TRANSLITERASI/transliterasi.py", Path(__file__).resolve()]
    protected = {str(p): sha(p) for p in source_paths}
    summary = read(batch/"RINGKASAN.json")
    if summary["version"] != VERSION or summary["checkpoint_sha256"] != CHECKPOINT_HASH:
        raise ValueError("Versi batch berbeda dari modul; buat batch baru dahulu.")
    metadata = read(meta_path)
    names = {c["id"]: c["name"] for c in metadata["categories"]}
    references = read(reference_path)
    out.mkdir()
    (out/"diagnosis_gt").mkdir()
    rows, detailed, articles, counts = [], [], [], Counter()
    known_reference_issues = {
        41: "GT tidak memuat Sihora untuk To pada acuan huta Toba (5 GT; rencana PDF 6).",
        49: "GT tidak memuat Haborotan untuk hu pada acuan aek ni huta (9 GT; rencana PDF 10).",
        54: "GT memuat Ina Da pada posisi ja dalam acuan jabu; susunan GT terbaca dabu.",
        98: "GT tidak memuat Haminsaran pada ang dalam acuan anggi (9 GT; rencana PDF 10).",
        119: "GT memuat Ina Ya dengan Hatadingan pada posisi me dalam acuan eme; terbaca ye/normalisasi e.",
        124: "GT memuat Pangolat pada Sa yang juga bertanda Sihora setelah pi; 11 GT, rencana PDF 10; kombinasi ambigu."
    }
    for previous in references:
        image_id = int(previous["image_id"])
        prediction = read(batch/"per_citra"/f"{image_id:03}.json")
        annotations = [a for a in metadata["annotations"] if a["image_id"] == image_id]
        diagnostic = gt_diagnostic(annotations, names)
        gt_text = diagnostic["text_automatic"]
        reference = previous["latin_acuan_pdf"]
        clean = not any(previous[key] for key in ("wrong_class", "missed_gt", "extra_predictions"))
        pred_same = norm(prediction["text_automatic"]) == norm(reference)
        gt_same = norm(gt_text) == norm(reference)
        before_same = norm(previous["hasil_otomatis"]) == norm(reference)
        regression = before_same and not pred_same
        notes = []
        if image_id in known_reference_issues:
            notes.append(known_reference_issues[image_id])
        if "buhu" in gt_text and "buku" in reference:
            notes.append("Ina Ha pada awal suku kata dibaca h menurut aturan Toba; ejaan buku pada PDF memerlukan keputusan ejaan/kosakata, bukan penggantian h ke k secara umum.")
        if not clean:
            notes.append("Prediksi memiliki salah kelas, GT terlewat, atau prediksi tambahan menurut evaluasi tersimpan; tidak dikoreksi menjadi GT.")
        if not gt_same and not notes:
            notes.append("PERLU_TINJAU: bacaan GT belum sesuai acuan.")
        row = {"image_id": image_id, "nama_citra": previous["nama_citra"],
               "responden": previous["responden"], "halaman_pdf": previous["halaman_pdf"],
               "latin_acuan_pdf": reference, "prediksi_sebelum": previous["hasil_otomatis"],
               "prediksi_sesudah": prediction["text_automatic"], "bacaan_GT_diagnostik": gt_text,
               "bersih_menurut_matching": clean, "sama_sebelum_tanpa_spasi": before_same,
               "sama_sesudah_tanpa_spasi": pred_same, "GT_sama_tanpa_spasi": gt_same,
               "regresi_teks": regression,
               "GT_id_dan_kelas": "; ".join(f'{a["id"]}:{names[a["category_id"]]}' for a in annotations),
               "catatan": " ".join(notes)}
        rows.append(row)
        counts["images"] += 1
        counts["pred_same_after_ignoring_spaces_case"] += pred_same
        counts["gt_diagnostic_same_ignoring_spaces_case"] += gt_same
        counts["reference_regressions"] += regression
        if clean:
            counts["clean_images"] += 1
            counts["clean_same_before"] += before_same
            counts["clean_same_after"] += pred_same
        if not gt_same:
            counts["gt_reference_discrepancies"] += image_id in known_reference_issues
            counts["gt_spelling_hk_discrepancies"] += "buhu" in gt_text and "buku" in reference
        gt_proof = {"kind": "GT_GEOMETRY_DIAGNOSTIC_NOT_INFERENCE",
                    "image_id": image_id, "annotation_source": str(meta_path),
                    "annotation_source_sha256": protected[str(meta_path)],
                    "annotations": annotations,
                    "adapter_note": "Score 1.0 di dalam adaptor hanyalah placeholder agar mesin memakai seluruh GT; bukan confidence, prediksi, atau hasil model. Tidak disimpan sebagai predictions.json.",
                    "text_literal": diagnostic["text_literal"], "text": gt_text,
                    "lines": diagnostic["lines"], "assignments": diagnostic["assignments"]}
        (out/"diagnosis_gt"/f"{image_id:03}.json").write_text(json.dumps(gt_proof, ensure_ascii=False, indent=2), encoding="utf-8")
        detailed.append({**row, "source_reference_status": previous["reference_status"],
                         "wrong_class": previous["wrong_class"], "missed_gt": previous["missed_gt"],
                         "extra_predictions": previous["extra_predictions"]})
        im = next(im for im in metadata["images"] if im["id"] == image_id)
        image = PACKAGE/"eksperimen/DATASET/testing"/im["file_name"]
        url = Path(os.path.relpath(image, out)).as_posix()
        articles.append(f'<article><h2>{image_id}. {html.escape(previous["nama_citra"])}</h2>'
                        f'<img loading="lazy" src="{html.escape(url, quote=True)}" alt="Citra asli">'
                        + ''.join(f'<p><b>{label}:</b><br><code>{html.escape(value)}</code></p>' for label,value in
                                  [("Acuan PDF",reference),("Sebelum",previous["hasil_otomatis"]),
                                   ("Sesudah",prediction["text_automatic"]),("Diagnostik dari GT",gt_text)])
                        + f'<p>{html.escape(row["catatan"])}</p><details><summary>ID anotasi</summary>{html.escape(row["GT_id_dan_kelas"])}</details></article>')
    with (out/"PERBANDINGAN_131.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/"BUKTI_PER_CITRA.json").write_text(json.dumps(detailed, ensure_ascii=False, indent=2), encoding="utf-8")
    unchanged = all(sha(Path(name)) == value for name,value in protected.items())
    report = {"version": VERSION, "counts": dict(counts), "source_hashes": protected,
              "sources_unchanged": unchanged,
              "scope": "DEVELOPMENT_COMPARISON_ON_ALREADY_INSPECTED_TESTING; NOT_INDEPENDENT_ACCURACY",
              "comparison": "Whitespace and case ignored; no claim of correct word boundaries or capitalization",
              "reference_status": "PDF item mapping and assistant visual review; not independent language-expert validation",
              "ground_truth_diagnostic": "GT bbox/class supplied only to isolate geometry/rule problems; never substituted for model predictions",
              "text_accuracy": None, "CER": None, "new_inference": False, "training": False}
    (out/"RINGKASAN_AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out/"TINJAU_BACAAN.html").write_text('<!doctype html><html lang="id"><meta charset="utf-8"><title>Audit bacaan dan GT</title>'
        '<style>body{font:17px system-ui;max-width:1100px;margin:auto;padding:24px;background:#f5f2ec}article{background:white;border:1px solid #bbb;padding:20px;margin:24px 0}img{max-width:100%;height:auto}code{font:22px monospace;white-space:pre-wrap}p{line-height:1.5}</style>'
        '<h1>Audit bacaan dan GT</h1><p>Perbandingan pengembangan dengan acuan PDF. Spasi dan kapital belum dipulihkan. Diagnosis GT terpisah dari prediksi model; angka kesesuaian bukan akurasi pengujian independen.</p>'
        + ''.join(articles)+'</html>', encoding="utf-8")
    print(json.dumps({"counts": dict(counts), "sources_unchanged": unchanged, "output":str(out)}, indent=2))
    if not unchanged:raise SystemExit(1)


if __name__ == "__main__":
    main()
