"""CER hasil transliterasi tersimpan terhadap acuan PDF; tidak menjalankan model."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT.parent/'02_AKSARABATAKTOBA_TERBARU'
REFERENCES=ROOT/'05_HASIL/TESTING_131_20261117T111615166527Z/AUDIT_BACAAN_DAN_GT/BUKTI_PER_CITRA.json'
READINGS=ROOT/'05_HASIL/TAHAP_08_SPASI_KONSERVATIF/per_citra'


def normalize(text,include_spaces=False):
    return (' '.join(text.casefold().split()) if include_spaces else ''.join(text.casefold().split()))


def character_errors(reference,hypothesis):
    """Levenshtein per code point; tie: diagonal, deletion, insertion."""
    n,m=len(reference),len(hypothesis)
    if not n:raise ValueError('Acuan kosong tidak mempunyai denominator CER.')
    dp=[[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1):dp[i][0]=i
    for j in range(m+1):dp[0][j]=j
    for i in range(1,n+1):
        for j in range(1,m+1):
            dp[i][j]=min(dp[i-1][j-1]+(reference[i-1]!=hypothesis[j-1]),dp[i-1][j]+1,dp[i][j-1]+1)
    counts={'S':0,'D':0,'I':0,'C':0,'N':n}
    operations=[];i,j=n,m
    while i or j:
        if i and j and dp[i][j]==dp[i-1][j-1]+(reference[i-1]!=hypothesis[j-1]):
            op='C' if reference[i-1]==hypothesis[j-1] else 'S'
            operations.append({'op':op,'ref':reference[i-1],'hyp':hypothesis[j-1]});i-=1;j-=1
        elif i and dp[i][j]==dp[i-1][j]+1:
            op='D';operations.append({'op':op,'ref':reference[i-1],'hyp':''});i-=1
        else:
            op='I';operations.append({'op':op,'ref':'','hyp':hypothesis[j-1]});j-=1
        counts[op]+=1
    counts['errors']=counts['S']+counts['D']+counts['I']
    assert counts['errors']==dp[n][m] and counts['S']+counts['D']+counts['C']==n
    return {**counts,'cer':counts['errors']/n,'alignment':list(reversed(operations))}


def aggregate(records):
    total={k:sum(r[k] for r in records) for k in ['S','D','I','C','N','errors']}
    return {**total,'cer':total['errors']/total['N'],'cer_percent':100*total['errors']/total['N'],
            'images':len(records),'exact_text_matches':sum(r['errors']==0 for r in records)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='Folder baru, tidak menimpa hasil lama.')
    args=parser.parse_args()
    out=args.output
    if out.exists():raise FileExistsError(out)
    meta_path=PACKAGE/'eksperimen/DATASET/testing/instances.json'
    source_paths=[REFERENCES,meta_path,Path(__file__).resolve(),ROOT/'01_ATURAN/peta_aksara.json',
                  ROOT/'02_MODUL_TRANSLITERASI/susun_prediksi.py',ROOT/'02_MODUL_TRANSLITERASI/transliterasi.py',
                  ROOT/'05_HASIL/TAHAP_08_SPASI_KONSERVATIF/RINGKASAN.json',
                  PACKAGE/'eksperimen/hasil_evaluasi_R50_30epoch/predictions.json',
                  PACKAGE/'eksperimen/hasil_evaluasi_R50_30epoch/metrik_instansi.json']
    refs=json.loads(REFERENCES.read_text(encoding='utf-8'))
    meta=json.loads(meta_path.read_text(encoding='utf-8'))
    ids=[im['id'] for im in meta['images']]
    assert len(ids)==len(set(ids))==len(refs)==131
    assert {int(r['image_id']) for r in refs}==set(ids)
    source_paths += [READINGS/f'{image_id:03}.json' for image_id in ids]
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    known_gt_pdf={41,49,54,98,119,124}
    rows=[];evidence=[]
    for reference in sorted(refs,key=lambda r:int(r['image_id'])):
        image_id=int(reference['image_id'])
        im=next(im for im in meta['images'] if im['id']==image_id)
        reading=json.loads((READINGS/f'{image_id:03}.json').read_text(encoding='utf-8'))
        assert Path(im['file_name']).name==reference['nama_citra']==Path(reading['audit_source']['file_name']).name
        assert reading['audit_source']['image_id']==image_id
        raw=reading['text_automatic'];target=reference['latin_acuan_pdf']
        spaced=reading['word_spacing']['suggested_text']
        assert normalize(raw)==normalize(spaced)
        protocols={
            'no_spaces':character_errors(normalize(target),normalize(raw)),
            'with_spaces':character_errors(normalize(target,True),normalize(spaced,True)),
        }
        row={'image_id':image_id,'file_name':im['file_name'],'writer':reference['responden'],
             'reference_pdf':target,'prediction_raw':raw,'spacing_suggestion':spaced,
             'reference_mapping_status':reference['source_reference_status'],
             'known_gt_pdf_difference':image_id in known_gt_pdf,
             'hk_spelling_difference':'buhu' in reference['bacaan_GT_diagnostik'] and 'buku' in target.casefold(),
             'spacing_status':reading['word_spacing']['status'],'reading_status':reading['text_status']}
        for name,metrics in protocols.items():
            row.update({name+'_'+k:v for k,v in metrics.items() if k!='alignment'})
        rows.append(row)
        evidence.append({**row,'alignments':protocols})
    summary={
        'status':'DEVELOPMENT_COMPARISON_TO_PDF_NOT_INDEPENDENT_FINAL_TEXT_ACCURACY',
        'subset':'testing','images':131,'formula':'CER=(S+D+I)/N; corpus micro aggregation, not mean image CER',
        'main_no_spaces':aggregate([r['alignments']['no_spaces'] for r in evidence]),
        'supplementary_with_spaces':aggregate([r['alignments']['with_spaces'] for r in evidence]),
        'normalization':'casefold; remove all whitespace for main, collapse whitespace for supplementary; retain punctuation and ambiguity markers verbatim',
        'reference_mapping_statuses':{s:sum(r['reference_mapping_status']==s for r in rows) for s in sorted({r['reference_mapping_status'] for r in rows})},
        'known_gt_pdf_difference_ids':sorted(known_gt_pdf),
        'notes':['All 131 images included, including errors and ambiguity; no selective exclusions.',
                 'References are exposed PDF stimulus mappings; not all visually confirmed or expert-validated.',
                 'Known source/reference and h/k spelling differences contribute to CER.',
                 'No corrected P10_N23 copy substituted into primary testing.',
                 'Supplementary score includes uncertainty of proposed spacing, not validated word segmentation.',
                 'Character alignment can have multiple optimal paths; S/D/I tie rule is documented.',
                 'No training, inference, prediction editing, or changes to original research metrics.'],
        'source_hashes':hashes,
    }
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    out.mkdir(parents=True)
    (out/'ringkasan_cer.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'BUKTI_PER_CITRA.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    with (out/'CER_PER_CITRA.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:v for k,v in summary.items() if k!='source_hashes'},indent=2))


if __name__=='__main__':main()
