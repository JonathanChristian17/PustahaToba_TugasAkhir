"""Audit pengelompokan kandidat bacaan pada prediksi tersimpan, tanpa inferensi."""
import argparse
from collections import Counter
import copy
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT.parent/"02_AKSARABATAKTOBA_TERBARU"
DEFAULT_BEFORE=ROOT/"05_HASIL/TESTING_131_20261117T110305251381Z"
sys.path.insert(0,str(ROOT/"02_MODUL_TRANSLITERASI"))
from susun_prediksi import arrange, VERSION, CHECKPOINT_HASH
from uji_testing_tersimpan import adapt_predictions


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(name):
    if os.name=="nt" and name.startswith("/mnt/d/"):
        return Path("D:/"+name[len("/mnt/d/"):])
    return Path(name)


def norm(value):
    return re.sub(r"\s+","",value).casefold()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hasil",type=Path,required=True)
    parser.add_argument("--sebelum",type=Path,default=DEFAULT_BEFORE)
    args=parser.parse_args()
    after,before=args.hasil.resolve(),args.sebelum.resolve()
    out=after/"AUDIT_KANDIDAT_SELOKASI"
    if out.exists():raise FileExistsError("Audit lama tidak ditimpa.")
    summary=read(after/"RINGKASAN.json")
    if summary["version"]!=VERSION:raise ValueError("Versi hasil dan mesin berbeda.")
    for name,digest in summary["source_hashes"].items():
        if sha(local_path(name))!=digest:raise ValueError("Sumber batch telah berubah: "+name)
    evaluation=PACKAGE/"eksperimen/hasil_evaluasi_R50_30epoch"
    meta_path=PACKAGE/"eksperimen/DATASET/testing/instances.json"
    protected={str(path):sha(path) for path in [meta_path,evaluation/"predictions.json",evaluation/"metrik_instansi.json",
               evaluation/"ringkasan.json",PACKAGE/"model/identitas.json",PACKAGE/"model/class_map.json"]}
    original_hashes=read(before/"RINGKASAN.json")["source_hashes"]
    source_comparisons={name:sha(local_path(name))==digest for name,digest in original_hashes.items()
                        if "02_AKSARABATAKTOBA_TERBARU/" in name.replace("\\","/")}
    if not source_comparisons or not all(source_comparisons.values()):raise AssertionError("Sumber eksperimen berubah.")
    metadata=read(meta_path);predictions=read(evaluation/"predictions.json")
    matching=read(evaluation/"metrik_instansi.json")
    gt_by_prediction={(m["image_id"],m["pred_index"]+1):m["gt_id"] for m in matching["matches"]}
    names={c["id"]:c["name"] for c in metadata["categories"]}
    references=read(ROOT/"05_HASIL/TESTING_131_20261117T102933620328Z/AUDIT_TEKS_DAN_AKSARA/audit_terstruktur.json")
    references={int(r["image_id"]):r["latin_acuan_pdf"] for r in references}
    rows,groups,changed,conflicts,regressions,articles=[],[],[],[],[],[]
    counts=Counter()
    for image in metadata["images"]:
        image_id=image["id"]
        previous=read(before/"per_citra"/f"{image_id:03}.json")
        current=read(after/"per_citra"/f"{image_id:03}.json")
        adapted=adapt_predictions([(j,p) for j,p in enumerate(predictions) if p["image_id"]==image_id],names)
        document={"checkpoint_sha256":CHECKPOINT_HASH,"display_threshold":.5,"predictions":adapted}
        untouched=copy.deepcopy(document);result=arrange(document)
        if document!=untouched:raise AssertionError("Prediksi dimutasi.")
        if result["text_automatic"]!=current["text_automatic"]:raise AssertionError("Hasil tersimpan tidak konsisten.")
        visible={p["instance_id"] for p in adapted if p["displayed"]}
        claimed=[k for line in result["lines"] for unit in line["units"] for k in unit["source_instance_ids"]]
        claimed += [a["anak_id"] for a in result["assignments"] if a["ina_id"] is None]
        if sorted(claimed)!=sorted(visible):raise AssertionError("Pelestarian identitas instansi gagal.")
        shifted=copy.deepcopy(document)
        for prediction in shifted["predictions"]:
            prediction["bbox_xyxy"]=[v*2+(200 if j%2==0 else 300) for j,v in enumerate(prediction["bbox_xyxy"])]
        transformed=arrange(shifted)
        signature=lambda d:[(a["anak_id"],a["ina_id"],a["status"]) for a in d["assignments"]]
        if result["text_automatic"]!=transformed["text_automatic"] or signature(result)!=signature(transformed):
            raise AssertionError("Bacaan/pasangan berubah karena skala atau translasi.")
        reordered=copy.deepcopy(document);reordered["predictions"].reverse()
        reverse=arrange(reordered)
        if result["lines"]!=reverse["lines"] or result["reading_candidate_groups"]!=reverse["reading_candidate_groups"]:
            raise AssertionError("Bacaan berubah karena urutan daftar prediksi.")
        additions=[]
        for group in current["reading_candidate_groups"]:
            if len(group["ina_ids"])<2:continue
            counts["overlapping_ina_groups"]+=1
            alternatives=group["alternatives"]
            top=alternatives[0]["score"]
            winners=[p for p in alternatives if p["score"]==top]
            expected=winners[0]["instance_id"] if len(winners)==1 else None
            if group["selected_instance_id"]!=expected:raise AssertionError("Pemenang bukan confidence tertinggi.")
            matched=sorted({gt_by_prediction[(image_id,k)] for k in group["ina_ids"] if (image_id,k) in gt_by_prediction})
            if len(matched)>1:conflicts.append({"image_id":image_id,"ids":group["ina_ids"],"gt_ids":matched})
            added=any(e["rule"]=="ALIGNED_CONTAINED_BBOX" for e in group["grouping_evidence"])
            proof={"image_id":image_id,"file_name":image["file_name"],**group,
                   "matched_gt_ids":matched,"new_containment_rule_used":added}
            groups.append(proof)
            if added:additions.append(proof);counts["contained_ina_groups"]+=1
        text_changed=previous["text_automatic"]!=current["text_automatic"]
        if text_changed:changed.append(image_id)
        if norm(previous["text_automatic"])==norm(references[image_id]) and norm(current["text_automatic"])!=norm(references[image_id]):
            regressions.append(image_id)
        row={"image_id":image_id,"file_name":image["file_name"],"before":previous["text_automatic"],
             "after":current["text_automatic"],"changed":text_changed,"new_containment_groups":len(additions),
             "raw_count":len(adapted),"visible_count":len(visible),"all_ids_conserved":True,
             "highest_confidence_checked":True,"scale_translation_checked":True,"input_order_checked":True}
        rows.append(row)
        if additions:
            url=Path(os.path.relpath(PACKAGE/"eksperimen/DATASET/testing"/image["file_name"],out)).as_posix()
            articles.append(f'<article><h2>{html.escape(Path(image["file_name"]).name)}</h2><img src="{html.escape(url,quote=True)}" alt="Citra asli">'
                            f'<p>Sebelum: <code>{html.escape(row["before"])}</code></p><p>Sesudah: <code>{html.escape(row["after"])}</code></p>'
                            + ''.join('<p>Calon: '+html.escape(' / '.join(f'{p["instance_id"]}: {p["class_label"]} {p["score"]:.6f}' for p in g['alternatives']))
                                      +f' — ID terpilih {g["selected_instance_id"]}; GT pasangan tersimpan {g["matched_gt_ids"]}</p>' for g in additions)
                            + '<p>Pemilihan hanya untuk teks. Confidence tertinggi tetap dapat salah kelas; tidak ada penambahan tanda yang hilang.</p></article>')
    if conflicts or regressions:raise AssertionError({"distinct_gt_groups":conflicts,"reference_regressions":regressions})
    if not all(sha(Path(name))==digest for name,digest in protected.items()):raise AssertionError("Sumber audit berubah.")
    out.mkdir()
    with (out/"AUDIT_131.csv").open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/"KELOMPOK_KANDIDAT.json").write_text(json.dumps(groups,ensure_ascii=False,indent=2),encoding="utf-8")
    report={"version":VERSION,"images":len(rows),"raw_predictions":len(predictions),
            "visible_predictions":sum(p['score']>=.5 for p in predictions),"counts":dict(counts),
            "changed_image_ids":changed,"reference_regressions":regressions,"groups_with_distinct_matched_gt":conflicts,
            "all_ids_conserved":True,"all_highest_confidence_selections_checked":True,
            "scale_translation_invariant_images":len(rows),"input_order_invariant_images":len(rows),
            "source_hashes":protected,"original_hashes_match_previous_batch":source_comparisons,
            "script_sha256":sha(Path(__file__).resolve()),
            "scope":"DEVELOPMENT_AUDIT_ON_EXPOSED_TESTING; NOT_INDEPENDENT_MODEL_EVALUATION",
            "limitations":"BBox grouping is a geometric hypothesis. Stored matching does not independently establish object identity. Model errors, missing signs, word spaces, h/k decisions and UI integration remain outside this change.",
            "training":False,"new_inference":False}
    (out/"RINGKASAN.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"TINJAU_PERUBAHAN.html").write_text('<!doctype html><html lang="id"><meta charset="utf-8"><title>Audit kandidat selokasi</title>'
        '<style>body{font:17px system-ui;max-width:1100px;margin:auto;padding:24px;background:#f5f2ec}article{background:white;border:1px solid #bbb;padding:20px;margin:24px 0}img{max-width:100%}code{font:22px monospace;white-space:pre-wrap}</style>'
        '<h1>Perubahan kandidat bacaan</h1><p>Empat citra menggunakan aturan containment tambahan. Semua prediksi model tetap tersimpan; yang dipilih hanya jalur bacaan Latin. Pemeriksaan pengembangan pada testing yang sudah ditinjau, bukan akurasi model baru.</p>'
        +''.join(articles)+'</html>',encoding="utf-8")
    print(json.dumps({"images":len(rows),"counts":dict(counts),"changed_image_ids":changed,
                      "distinct_gt_groups":len(conflicts),"reference_regressions":len(regressions),"output":str(out)},indent=2))


if __name__=="__main__":
    main()
