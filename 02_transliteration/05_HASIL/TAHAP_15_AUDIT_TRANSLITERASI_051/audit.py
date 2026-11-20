"""Regresi lintas peran, Ina komposit, tanda berbagi mask, dan penyajian (v0.5.1); memakai hasil tersimpan, bukan inferensi baru."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / "04_PENGUJIAN"))
from uji_kasus_minor import TestSavedMinorCases
from uji_geometri import geometry
from evaluasi_cer import normalize, character_errors, aggregate

spec = importlib.util.spec_from_file_location("before_050", OUT / "sebelum/susun_prediksi.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

TestSavedMinorCases.setUpClass()
case = TestSavedMinorCases()
package = ROOT.parent / "02_AKSARABATAKTOBA_TERBARU"
web = ROOT.parent / "04_WEB_APP_BATAK_TOBA"
evaluation = package / "eksperimen/hasil_evaluasi_R50_30epoch"
paths = [
    package / "eksperimen/DATASET/testing/instances.json",
    evaluation / "predictions.json",
    evaluation / "metrik_instansi.json",
    evaluation / "ringkasan.json",
    package / "model/identitas.json",
    package / "aplikasi/backend.py",
    ROOT / "01_ATURAN/peta_aksara.json",
    ROOT / "02_MODUL_TRANSLITERASI/susun_prediksi.py",
    ROOT / "02_MODUL_TRANSLITERASI/transliterasi.py",
    ROOT / "04_PENGUJIAN/uji_konflik_peran.py",
    ROOT / "04_PENGUJIAN/uji_kandidat_anak.py",
    Path(__file__).resolve(),
    web / "src/utils/transliterationAdapter.js",
    web / "src/pages/PublicReaderPage.jsx",
    web / "src/pages/ResearchPage.jsx",
    web / "src/pages/HistoryPage.jsx",
]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
hashes = {str(p): sha(p) for p in paths}

matching = json.loads((evaluation / "metrik_instansi.json").read_text())
matched = {(m["image_id"], m["pred_index"] + 1): m["gt_id"] for m in matching["matches"]}
references = json.loads((ROOT / "05_HASIL/TESTING_131_20261117T111615166527Z/AUDIT_BACAAN_DAN_GT/BUKTI_PER_CITRA.json").read_text())
refs = {r["image_id"]: r["latin_acuan_pdf"] for r in references}

rows, conflicts, regressions, failures = [], [], [], []
old_cer, new_cer, role_groups = [], [], []


def signature(r):
    return (
        r["text_automatic"],
        r["text_literal"],
        r["text_status"],
        [[(u["ina_id"], u["source_instance_ids"], u["reading"]["text"]) for u in l["units"]] for l in r["lines"]],
        sorted((a["anak_id"], a["ina_id"], a["status"]) for a in r["assignments"]),
        sorted((sorted(g["instance_ids"]), g["selected_instance_id"]) for g in r["role_candidate_groups"]),
        sorted((g["ina_id"], g["role"], sorted(g["sign_ids"]), g["selected_instance_id"]) for g in r["sign_candidate_groups"]),
        r["word_spacing"],
        r["presentation"],
    )


(OUT / "per_citra").mkdir(exist_ok=True)
for im in case.meta["images"]:
    image_id = im["id"]
    doc = case.document(image_id)
    snapshot = copy.deepcopy(doc)
    before = old.arrange(doc, lexicon=case.lex)
    after = geometry.arrange(doc, lexicon=case.lex)
    assert snapshot == doc

    claimed = [i for l in after["lines"] for u in l["units"] for i in u["source_instance_ids"]]
    claimed += [i for a in after["assignments"] if a["ina_id"] is None for i in a["source_instance_ids"]]
    assert sorted(claimed) == sorted(p["instance_id"] for p in doc["predictions"] if p["displayed"]), (image_id, claimed)

    for group_type, key in [("ina", "reading_candidate_groups"), ("roles", "role_candidate_groups"), ("signs", "sign_candidate_groups")]:
        for g in after[key]:
            ids = g.get("instance_ids", g.get("ina_ids", g.get("sign_ids", [])))
            gt_ids = {matched[(image_id, i)] for i in ids if (image_id, i) in matched}
            if len(gt_ids) > 1:
                conflicts.append({"image_id": image_id, "type": group_type, "ids": ids, "gt_ids": sorted(gt_ids)})
            alts = g["alternatives"]
            top = max(a["score"] for a in alts)
            winners = [a for a in alts if a["score"] == top]
            assert g["selected_instance_id"] == (winners[0]["instance_id"] if len(winners) == 1 else None)
            if key == "role_candidate_groups":
                role_groups.append({"image_id": image_id, **g})

    if normalize(before["text_automatic"]) == normalize(refs[image_id]) and normalize(after["text_automatic"]) != normalize(refs[image_id]):
        regressions.append(image_id)

    assert all("?" not in after["presentation"][k] for k in ["automatic_text", "literal_text", "spacing_suggestion"])

    for mode in ["reverse", "rotate", "scale_half", "scale_double", "translate"]:
        variant = copy.deepcopy(doc)
        if mode == "reverse":
            variant["predictions"].reverse()
        elif mode == "rotate":
            variant["predictions"] = variant["predictions"][1:] + variant["predictions"][:1]
        else:
            scale = 0.5 if mode == "scale_half" else 2 if mode == "scale_double" else 1
            dx, dy = (137, 83) if mode == "translate" else (0, 0)
            for p in variant["predictions"]:
                p["bbox_xyxy"] = [v * scale + (dx if j % 2 == 0 else dy) for j, v in enumerate(p["bbox_xyxy"])]
        if signature(geometry.arrange(variant, lexicon=case.lex)) != signature(after):
            failures.append([image_id, mode])

    old_cer.append(character_errors(normalize(refs[image_id]), normalize(before["text_automatic"])))
    new_cer.append(character_errors(normalize(refs[image_id]), normalize(after["text_automatic"])))
    rows.append({
        "image_id": image_id,
        "file": im["file_name"],
        "before": before["text_automatic"],
        "after": after["text_automatic"],
        "display": after["presentation"]["automatic_text"],
        "unresolved_units": after["presentation"]["unresolved_units"],
    })
    after["audit_source"] = {"image_id": image_id, "file_name": im["file_name"], "subset": "testing"}
    (OUT / "per_citra" / f"{image_id:03}.json").write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8")

assert all(sha(Path(p)) == h for p, h in hashes.items())
summary = {
    "version": geometry.VERSION,
    "images": len(rows),
    "changed": [r for r in rows if r["before"] != r["after"]],
    "role_groups": role_groups,
    "distinct_matched_gt_group_conflicts": conflicts,
    "reference_regressions": regressions,
    "coordinate_order_checks": 655,
    "invariance_failures": failures,
    "all_visible_ids_preserved": True,
    "all_predictions_unchanged": True,
    "presentation_has_no_question_mark": True,
    "remaining_unresolved_image_ids": [r["image_id"] for r in rows if r["unresolved_units"]],
    "source_hashes": hashes,
    "sources_unchanged_during_audit": True,
    "development_cer_before": aggregate(old_cer),
    "development_cer_after": aggregate(new_cer),
    "scope": "Exposed testing, provisional PDF reference; CER uses diagnostic text, never formatted presentation. Coordinate checks transform bbox only, not new experiments.",
    "training": False,
    "new_inference": False,
}
(OUT / "RINGKASAN.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k not in ["source_hashes", "role_groups"]}, indent=2, ensure_ascii=True))
assert not (conflicts or regressions or failures), (conflicts, regressions, failures)
