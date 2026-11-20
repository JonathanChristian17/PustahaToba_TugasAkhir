"""Transliterasi batch prediksi testing tersimpan; tidak menjalankan model."""
import argparse
from collections import Counter
import copy
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT.parent / "02_AKSARABATAKTOBA_TERBARU"
sys.path.insert(0,str(ROOT / "02_MODUL_TRANSLITERASI"))
from susun_prediksi import arrange, CHECKPOINT_HASH, VERSION


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def adapt_predictions(records, names):
    """Tambahkan ID lokal tanpa mengubah label/score/bbox/mask hasil evaluasi."""
    adapted=[]
    for local_id,(source_index,record) in enumerate(records,1):
        p=copy.deepcopy(record)
        p.update(instance_id=local_id,class_label=names[p["category_id"]],displayed=p["score"]>=.5)
        adapted.append(p)
    return adapted


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start",action="store_true",help="Jalankan batch pada hasil testing tersimpan.")
    args=parser.parse_args()
    if not args.start:
        parser.print_help();return
    evaluation=PACKAGE/"eksperimen/hasil_evaluasi_R50_30epoch"
    prediction_path=evaluation/"predictions.json"
    image_path=PACKAGE/"eksperimen/DATASET/testing/instances.json"
    summary_path=evaluation/"ringkasan.json"
    selection_path=PACKAGE/"model/identitas.json"
    sources=[prediction_path,image_path,summary_path,selection_path,ROOT/"01_ATURAN/peta_aksara.json",
             ROOT/"02_MODUL_TRANSLITERASI/susun_prediksi.py",ROOT/"02_MODUL_TRANSLITERASI/transliterasi.py",
             Path(__file__).resolve()]
    source_hashes={str(p):sha(p) for p in sources}
    metadata=json.loads(image_path.read_text())
    images=metadata["images"]
    if len(images)!=131 or len({im["id"] for im in images})!=131:
        raise ValueError("Populasi bukan 131 citra testing unik yang diharapkan.")
    summary=json.loads(summary_path.read_text())
    selected=json.loads(selection_path.read_text())
    if summary["checkpoint_sha256"]!=CHECKPOINT_HASH or selected["checkpoint_sha256"]!=CHECKPOINT_HASH:
        raise ValueError("Identitas hasil evaluasi/checkpoint berbeda dari kandidat terpilih.")
    names={c["id"]:c["name"] for c in metadata["categories"]}
    label_path=PACKAGE/"model/class_map.json"
    if names!={c["id"]:c["name"] for c in json.loads(label_path.read_text())}:
        raise ValueError("Peta kelas testing berbeda dari model.")
    source_hashes[str(label_path)]=sha(label_path)
    records=json.loads(prediction_path.read_text())
    image_ids={im["id"] for im in images}
    grouped={key:[] for key in image_ids}
    for index,record in enumerate(records):
        if record["image_id"] not in image_ids:
            raise ValueError("Prediksi berada di luar populasi testing.")
        grouped[record["image_id"]].append((index,record))
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=ROOT/"05_HASIL"/("TESTING_131_"+stamp)
    out.mkdir(exist_ok=False);(out/"per_citra").mkdir()
    (out/"snapshot_kode").mkdir()
    for path in sources[4:]:
        (out/"snapshot_kode"/path.name).write_bytes(path.read_bytes())
    rows,failures=[],[]
    statuses=Counter();reasons=Counter();page=[]
    for number,im in enumerate(sorted(images,key=lambda x:x["id"]),1):
        image_id=im["id"];current=grouped[image_id]
        adapted=adapt_predictions(current,names)
        document={"input_kind":"ADAPTED_SAVED_TEST_EVALUATION_PREDICTIONS",
                  "checkpoint_sha256":CHECKPOINT_HASH,"display_threshold":.5,"predictions":adapted}
        before=copy.deepcopy(document)
        try:
            result=arrange(document)
            if before!=document:raise AssertionError("Masukan dimutasi.")
            for original,derived in zip(current,adapted):
                if any(original[1][k]!=derived[k] for k in ["image_id","category_id","score","bbox_xyxy","segmentation"]):
                    raise AssertionError("Adaptasi mengubah prediksi.")
            claimed=[key for line in result["lines"] for unit in line["units"] for key in unit["source_instance_ids"]]
            unmatched=[a["anak_id"] for a in result["assignments"] if a["ina_id"] is None]
            expected=[p["instance_id"] for p in adapted if p["displayed"]]
            if sorted(claimed+unmatched)!=sorted(expected):raise AssertionError("Pelestarian ID gagal.")
            result["source_trace"]={"image_id":image_id,"file_name":im["file_name"],
                "subset":"testing","input_json_sha256":source_hashes[str(prediction_path)],
                "local_id_to_source_record_index_zero_based":{str(i):entry[0] for i,entry in enumerate(current,1)}}
            result["text_reference_status"]="NOT_VERIFIED; no text accuracy or CER computed"
            (out/"per_citra"/f"{image_id:03}.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
            status=result["text_status"];text=result["text_automatic"]
            counts=Counter(a["status"] for a in result["assignments"])
            row={"image_id":image_id,"file_name":im["file_name"],"writer":im.get("writer_id",""),
                 "text":text,"status":status,"raw_predictions":len(adapted),"visible_predictions":len(expected),
                 "ina_groups":len(result["reading_candidate_groups"]),
                 "selected_overlap_groups":sum(len(g["ina_ids"])>1 for g in result["reading_candidate_groups"]),
                 "signs_proposed":counts["PROPOSED"],"signs_ambiguous":counts["AMBIGUOUS"],
                 "signs_unpaired":counts["UNPAIRED"],"issue_count":len(result["issues"])}
            reasons.update(x["reason"] for x in result["issues"])
        except Exception as error:
            status="PROCESSING_ERROR";text="";failures.append({"image_id":image_id,"error":repr(error)})
            row={"image_id":image_id,"file_name":im["file_name"],"writer":im.get("writer_id",""),"text":text,"status":status}
        rows.append(row);statuses[status]+=1
        real_image=PACKAGE/"eksperimen/DATASET/testing"/im["file_name"]
        url=Path(os.path.relpath(real_image,out)).as_posix()
        page.append('<article><h2>'+html.escape(str(image_id)+" — "+Path(im["file_name"]).name)+'</h2>'
                    +'<img loading="lazy" src="'+html.escape(url,quote=True)+'" alt="Citra testing asli">'
                    +'<pre>'+html.escape(text)+'</pre><p>'+html.escape(status)+'</p>'
                    +'<a href="per_citra/'+f'{image_id:03}.json'+'">Jejak pasangan dan kandidat</a></article>')
        if number%25==0 or number==len(images):print(f"Transliterasi tersimpan: {number}/{len(images)}",flush=True)
    fields=["image_id","file_name","writer","text","status","raw_predictions","visible_predictions","ina_groups",
            "selected_overlap_groups","signs_proposed","signs_ambiguous","signs_unpaired","issue_count"]
    with (out/"HASIL_PER_CITRA.csv").open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    unchanged=all(sha(Path(name))==value for name,value in source_hashes.items())
    report={"version":VERSION,"checkpoint_sha256":CHECKPOINT_HASH,"images":len(images),"raw_predictions":len(records),
            "visible_predictions":sum(p["score"]>=.5 for p in records),"statuses":dict(statuses),"issue_counts":dict(reasons),
            "processing_errors":failures,"source_hashes":source_hashes,"sources_unchanged":unchanged,
            "scope":"BATCH_TRANSLITERATION_OF_FROZEN_SAVED_TEST_PREDICTIONS; NOT_INDEPENDENT_MODEL_EVALUATION",
            "text_reference_status":"NOT_VERIFIED","text_accuracy":None,"CER":None,
            "word_boundaries":"NOT_INFERRED","new_inference":False,"training":False,"output":str(out)}
    (out/"RINGKASAN.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"TINJAU_HASIL.html").write_text('<!doctype html><html lang="id"><meta charset="utf-8"><title>Transliterasi 131 citra testing</title>'
        +'<style>body{font:17px system-ui;max-width:1100px;margin:32px auto;padding:16px;background:#f4f2ee;color:#222}article{background:white;padding:20px;margin:24px 0;border:1px solid #ccc}img{max-width:100%;height:auto}pre{white-space:pre-wrap;font:24px monospace}p{font-size:14px}</style>'
        +'<h1>Transliterasi 131 citra testing</h1><p>Hasil otomatis versi '+html.escape(VERSION)+'. Status teknis bukan akurasi. Spasi belum dipulihkan; acuan Latin belum diverifikasi. Gambar adalah citra testing asli.</p>'
        +''.join(page)+'</html>',encoding="utf-8")
    print(json.dumps({"statuses":dict(statuses),"errors":len(failures),"sources_unchanged":unchanged,"output":str(out)},indent=2),flush=True)
    if not unchanged or failures:raise SystemExit(1)


if __name__=="__main__":main()
