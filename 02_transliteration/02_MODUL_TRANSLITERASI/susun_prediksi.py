"""Susun bacaan dari prediksi tersimpan tanpa mengganti kelas hasil model."""
from __future__ import annotations

import argparse
import hashlib
from dataclasses import asdict
import json
import math
from pathlib import Path
from statistics import median

from transliterasi import Transliterator, suggest_spaces

VERSION = "0.5.1-composite-ina-and-mask-sign-conflicts"
CHECKPOINT_HASH = "5d964b6e0f56f14901351933272f0ffb2ee6d6b085213fadd3f8406ffa4221c2"
THRESHOLD = 0.50
# Parameter pengembangan; testing telah ditinjau, bukan pengujian independen.
LINE_ALIGNMENT = 0.25
LINE_HEIGHT_TOLERANCE = 1.0
LINE_NEIGHBOR_GAP = 3.5
LINE_OVERLAP_LIMIT = 0.35
OVERLAP_CONFLICT = 0.65
CONTAINMENT_MIN = 0.90
CONTAINED_AREA_RATIO_MIN = 0.35
CONTAINED_X_OVERLAP_MIN = 0.90
CONTAINED_X_CENTER_MAX = 0.15
CONTAINED_Y_CENTER_MAX = 0.35
MASK_CANDIDATE_IOU_MIN = 0.50
MASK_CANDIDATE_BBOX_IOU_MIN = 0.25
CONTAINED_ANAK_MASK_MIN = 0.90
CONTAINED_ANAK_BBOX_MIN = 0.90
COMPOSITE_INA_COVERAGE_MIN = 0.80
COMPOSITE_INA_PART_CONTAINMENT_MIN = 0.30
COMPOSITE_INA_PART_SHARE_MIN = 0.15
PAIR_MARGIN = 0.25
MAX_PAIR_COST = 1.70
PROFILES = {
    19: ((0.20, -0.12), (-0.50, 1.20, -1.00, 0.45)),
    20: ((1.10, 0.65), (0.45, 2.20, -0.40, 1.50)),
    21: ((1.10, 0.65), (0.45, 2.20, -0.40, 1.50)),
    22: ((0.80, 0.90), (0.15, 1.80, 0.25, 1.80)),
    23: ((0.90, -0.15), (-0.25, 1.60, -1.00, 0.50)),
    24: ((1.10, 0.65), (0.45, 2.20, -0.40, 1.50)),
}


def center(p):
    x1, y1, x2, y2 = p["bbox_xyxy"]
    return (x1+x2)/2, (y1+y2)/2


def iou(a, b):
    x1, y1, x2, y2 = a["bbox_xyxy"]
    u1, v1, u2, v2 = b["bbox_xyxy"]
    intersection = max(0, min(x2, u2)-max(x1, u1))*max(0, min(y2, v2)-max(y1, v1))
    return intersection/((x2-x1)*(y2-y1)+(u2-u1)*(v2-v1)-intersection)


def mask_intervals(segmentation):
    """Interval foreground COCO RLE; tanpa rasterisasi atau dependensi tambahan."""
    if not isinstance(segmentation,dict):return None
    size=segmentation.get("size");counts=segmentation.get("counts")
    if not isinstance(size,(list,tuple)) or len(size)!=2 or any(type(v) is not int or v<=0 for v in size):return None
    if isinstance(counts,bytes):
        try:counts=counts.decode("ascii")
        except UnicodeDecodeError:return None
    if isinstance(counts,str):
        decoded=[];position=0
        while position<len(counts):
            value=shift=0
            while True:
                if position==len(counts):return None
                code=ord(counts[position])-48;position+=1
                if not 0<=code<=63:return None
                value|=(code&31)<<shift;shift+=5
                if not code&32:break
                if shift>64:return None
            if code&16:value|=-1<<shift
            if len(decoded)>2:value+=decoded[-2]
            decoded.append(value)
        counts=decoded
    if not isinstance(counts,(list,tuple)) or any(type(v) is not int or v<0 for v in counts):return None
    if sum(counts)!=size[0]*size[1]:return None
    intervals=[];offset=0
    for i,count in enumerate(counts):
        if i%2 and count:intervals.append((offset,offset+count))
        offset+=count
    return tuple(size),intervals,sum(counts[1::2])


def mask_overlap(a,b):
    left=mask_intervals(a.get("segmentation"));right=mask_intervals(b.get("segmentation"))
    if left is None or right is None or left[0]!=right[0] or not left[2] or not right[2]:return None
    i=j=intersection=0
    while i<len(left[1]) and j<len(right[1]):
        x1,x2=left[1][i];y1,y2=right[1][j]
        intersection+=max(0,min(x2,y2)-max(x1,y1))
        if x2<=y2:i+=1
        else:j+=1
    return {"mask_iou":intersection/(left[2]+right[2]-intersection),
            "mask_intersection":intersection,"mask_areas":[left[2],right[2]]}


def reading_overlap(a, b):
    """Bukti geometri kandidat selokasi; tidak mengubah deteksi atau NMS."""
    overlap=iou(a,b)
    if overlap>=OVERLAP_CONFLICT:
        return {"rule":"HIGH_BBOX_IOU","bbox_iou":overlap}
    x1,y1,x2,y2=a["bbox_xyxy"]
    u1,v1,u2,v2=b["bbox_xyxy"]
    aw,ah,bw,bh=x2-x1,y2-y1,u2-u1,v2-v1
    intersection_x=max(0,min(x2,u2)-max(x1,u1))
    intersection_y=max(0,min(y2,v2)-max(y1,v1))
    containment=intersection_x*intersection_y/min(aw*ah,bw*bh)
    area_ratio=min(aw*ah,bw*bh)/max(aw*ah,bw*bh)
    x_overlap=intersection_x/min(aw,bw)
    x_center=abs((x1+x2-u1-u2)/2)/max(aw,bw)
    y_center=abs((y1+y2-v1-v2)/2)/max(ah,bh)
    if (containment>=CONTAINMENT_MIN and area_ratio>=CONTAINED_AREA_RATIO_MIN
            and x_overlap>=CONTAINED_X_OVERLAP_MIN and x_center<=CONTAINED_X_CENTER_MAX
            and y_center<=CONTAINED_Y_CENTER_MAX):
        return {"rule":"ALIGNED_CONTAINED_BBOX","bbox_iou":overlap,
                "intersection_over_smaller_area":containment,"smaller_to_larger_area":area_ratio,
                "x_overlap_over_smaller_width":x_overlap,
                "x_center_distance_over_larger_width":x_center,
                "y_center_distance_over_larger_height":y_center}
    if overlap>=MASK_CANDIDATE_BBOX_IOU_MIN or (x_overlap>=CONTAINED_X_OVERLAP_MIN and x_center<=CONTAINED_X_CENTER_MAX):
        masks=mask_overlap(a,b)
        if masks is not None and masks["mask_iou"]>=MASK_CANDIDATE_IOU_MIN:
            return {"rule":"SHARED_FOREGROUND_MASK","bbox_iou":overlap,**masks}
    return None


def validate(document, engine):
    if document.get("checkpoint_sha256") != CHECKPOINT_HASH:
        raise ValueError("JSON bukan keluaran checkpoint Eksperimen 2 yang dipilih.")
    if document.get("display_threshold") != THRESHOLD:
        raise ValueError("Masukan harus memakai threshold tampilan 0,50.")
    rows = document.get("predictions")
    if not isinstance(rows, list):
        raise ValueError("Gunakan JSON ekspor backend UI dengan daftar predictions.")
    names = {e["id"]: e["name"] for e in engine.classes.values()}
    ids = set()
    for p in rows:
        key, cid, score = p["instance_id"], p["category_id"], p["score"]
        if type(key) is not int or key < 1 or key in ids:
            raise ValueError("ID instansi harus berupa integer positif yang unik.")
        ids.add(key)
        if type(cid) is not int or cid not in names or p["class_label"] != names[cid]:
            raise ValueError("ID dan label kelas tidak sesuai peta penelitian.")
        if not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Confidence tidak valid.")
        if p.get("displayed") is not (score >= THRESHOLD):
            raise ValueError("Penanda displayed tidak sesuai threshold 0,50.")
        box = p["bbox_xyxy"]
        if len(box) != 4 or not all(isinstance(v, (int,float)) and math.isfinite(v) for v in box):
            raise ValueError("Bounding box tidak valid.")
        if box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError("Bounding box harus memiliki luas positif.")
    return [p for p in rows if p["displayed"]]


def bbox_containment(a, b):
    x1, y1, x2, y2 = a["bbox_xyxy"]
    u1, v1, u2, v2 = b["bbox_xyxy"]
    ix = max(0, min(x2, u2) - max(x1, u1))
    iy = max(0, min(y2, v2) - max(y1, v1))
    return (ix * iy) / min((x2 - x1) * (y2 - y1), (u2 - u1) * (v2 - v1))


def composite_mask_coverage(candidate, others):
    """Deteksi mask Ina komposit yang >=80% tertutup gabungan >=2 Ina berskor lebih tinggi."""
    mi_a = mask_intervals(candidate.get("segmentation"))
    if not mi_a or not mi_a[2]:
        return None
    covered_intervals = []
    contributors = []
    for b in sorted(others, key=lambda p: (-p["score"], p["instance_id"])):
        if b["instance_id"] == candidate["instance_id"] or b["score"] <= candidate["score"]:
            continue
        mo = mask_overlap(candidate, b)
        if not mo or not mo["mask_intersection"]:
            continue
        mcont_smaller = mo["mask_intersection"] / min(mo["mask_areas"])
        share_of_cand = mo["mask_intersection"] / mi_a[2]
        if mcont_smaller >= COMPOSITE_INA_PART_CONTAINMENT_MIN and share_of_cand >= COMPOSITE_INA_PART_SHARE_MIN:
            contributors.append((b, mo["mask_intersection"]))
            mi_b = mask_intervals(b.get("segmentation"))
            i = j = 0
            while i < len(mi_a[1]) and j < len(mi_b[1]):
                x1, x2 = mi_a[1][i]
                y1, y2 = mi_b[1][j]
                s, e = max(x1, y1), min(x2, y2)
                if s < e:
                    covered_intervals.append((s, e))
                if x2 <= y2:
                    i += 1
                else:
                    j += 1
    if len(contributors) < 2 or not covered_intervals:
        return None
    covered_intervals.sort()
    merged = [covered_intervals[0]]
    for s, e in covered_intervals[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    cov_ratio = sum(e - s for s, e in merged) / mi_a[2]
    if cov_ratio < COMPOSITE_INA_COVERAGE_MIN:
        return None
    contributors.sort(key=lambda t: (-t[1], -t[0]["score"], t[0]["instance_id"]))
    host = contributors[0][0]
    return {
        "host_id": host["instance_id"],
        "rule": "COMPOSITE_SPANNING_INA_MASK",
        "covered_mask_ratio": cov_ratio,
        "covering_instance_ids": sorted(c[0]["instance_id"] for c in contributors),
    }


def select_reading_anchors(anchors, engine):
    """Pilih jalur bacaan sebelum geometri; semua alternatif dipertahankan."""
    groups, selected, tied_ids = [], [], set()
    for anchor in sorted(anchors, key=lambda p:(center(p)[0], center(p)[1], p["instance_id"])):
        target = next((g for g in groups if all(reading_overlap(anchor,m) is not None for m in g)),None)
        if target is None:
            groups.append([anchor])
        else:
            target.append(anchor)
    audit = {}
    for members in groups:
        members = sorted(members,key=lambda p:(-p["score"],p["instance_id"]))
        representative = members[0]
        tied = len(members)>1 and members[0]["score"]==members[1]["score"]
        selected.append(representative)
        if tied:
            tied_ids.add(representative["instance_id"])
        audit[representative["instance_id"]] = {
            "ina_ids":[p["instance_id"] for p in members],
            "selected_instance_id":None if tied else representative["instance_id"],
            "selection_status":"TIED_CONFIDENCE" if tied else "SELECTED_FOR_READING_ONLY",
            "grouping_scope":"READING_ONLY; geometric hypothesis, not verified object identity",
            "grouping_evidence":[{"instance_ids":[a["instance_id"],b["instance_id"]],
                                  **reading_overlap(a,b)}
                                 for i,a in enumerate(members) for b in members[i+1:]],
            "alternatives":[{"instance_id":p["instance_id"],"class_label":p["class_label"],
                "score":p["score"],"bbox_xyxy":list(p["bbox_xyxy"]),
                "base_latin":engine.classes[p["class_label"]]["latin"]} for p in members],
        }
    absorbed = {}
    for cand in sorted(selected, key=lambda p: (p["score"], p["instance_id"])):
        if cand["instance_id"] in tied_ids:
            continue
        remaining_hosts = [
            p for p in selected
            if p["instance_id"] != cand["instance_id"] and p["instance_id"] not in absorbed
        ]
        cov = composite_mask_coverage(cand, remaining_hosts)
        if cov is not None:
            absorbed[cand["instance_id"]] = cov
    if absorbed:
        selected = [p for p in selected if p["instance_id"] not in absorbed]
        for cid, cov in absorbed.items():
            hid = cov["host_id"]
            host_grp = audit[hid]
            cand_grp = audit.pop(cid)
            host_grp["alternatives"] = sorted(
                host_grp["alternatives"] + cand_grp["alternatives"],
                key=lambda a: (-a["score"], a["instance_id"]),
            )
            host_grp["ina_ids"] = [a["instance_id"] for a in host_grp["alternatives"]]
            host_grp["grouping_evidence"] = list(host_grp["grouping_evidence"]) + list(cand_grp["grouping_evidence"]) + [{
                "instance_ids": [hid, cid],
                "rule": cov["rule"],
                "covered_mask_ratio": cov["covered_mask_ratio"],
                "covering_instance_ids": cov["covering_instance_ids"],
            }]
    return selected,audit,tied_ids


def select_role_candidates(visible):
    """Konflik mask lintas Ina/Anak sebelum menentukan peran bacaan."""
    def evidence(a,b):
        overlap=iou(a,b)
        if overlap<MASK_CANDIDATE_BBOX_IOU_MIN:return None
        masks=mask_overlap(a,b)
        if masks is None or masks["mask_iou"]<MASK_CANDIDATE_IOU_MIN:return None
        return {"bbox_iou":overlap,**masks}
    candidates=[]
    for item in sorted(visible,key=lambda p:(center(p)[0],center(p)[1],p["instance_id"])):
        group=next((g for g in candidates if all(evidence(item,p) is not None for p in g)),None)
        if group is None:candidates.append([item])
        else:group.append(item)
    selected=[];groups=[];tied_ids=set()
    for members in candidates:
        if len({p["category_id"]<19 for p in members})<2:
            selected.extend(members);continue
        members=sorted(members,key=lambda p:(-p["score"],p["instance_id"]))
        tied=members[0]["score"]==members[1]["score"]
        representative=members[0];selected.append(representative)
        if tied:tied_ids.add(representative["instance_id"])
        groups.append({"representative_id":representative["instance_id"],
            "instance_ids":[p["instance_id"] for p in members],
            "selected_instance_id":None if tied else representative["instance_id"],
            "selection_status":"TIED_CONFIDENCE" if tied else "SELECTED_FOR_READING_ONLY",
            "grouping_scope":"SHARED_MASK_ROLE_HYPOTHESIS; not verified physical identity",
            "grouping_evidence":[{"instance_ids":[a["instance_id"],b["instance_id"]],**evidence(a,b)} for i,a in enumerate(members) for b in members[i+1:]],
            "alternatives":[{k:p[k] for k in ("instance_id","class_label","category_id","score","bbox_xyxy")} for p in members]})
    # Sub-langkah kedua: Anak berskor lebih rendah yang terkandung penuh (>=0.90 mask & bbox) di dalam mask Ina
    ina_pool = [p for p in selected if p["category_id"] < 19]
    suppressed_anak_ids = set()
    for anak in sorted([p for p in selected if p["category_id"] >= 19], key=lambda p: (p["score"], p["instance_id"])):
        if anak["instance_id"] in tied_ids:
            continue
        best = None
        for ina in ina_pool:
            if anak["score"] >= ina["score"]:
                continue
            masks = mask_overlap(ina, anak)
            if masks is None or not masks["mask_intersection"]:
                continue
            ina_area, anak_area = masks["mask_areas"]
            if anak_area > ina_area:
                continue
            mcont = masks["mask_intersection"] / anak_area
            bcont = bbox_containment(ina, anak)
            if mcont >= CONTAINED_ANAK_MASK_MIN and bcont >= CONTAINED_ANAK_BBOX_MIN:
                key = (mcont, ina["score"], -ina["instance_id"])
                if best is None or key > best[0]:
                    best = (key, ina, mcont, bcont, masks)
        if best is None:
            continue
        _, ina, mcont, bcont, masks = best
        suppressed_anak_ids.add(anak["instance_id"])
        ev = {
            "instance_ids": [ina["instance_id"], anak["instance_id"]],
            "rule": "CONTAINED_ANAK_IN_INA_MASK",
            "bbox_iou": iou(ina, anak),
            "bbox_containment": bcont,
            "mask_containment": mcont,
            **masks,
        }
        existing_grp = next((g for g in groups if g["representative_id"] == ina["instance_id"]), None)
        if existing_grp is not None:
            existing_grp["alternatives"] = sorted(
                list(existing_grp["alternatives"]) + [{k: anak[k] for k in ("instance_id", "class_label", "category_id", "score", "bbox_xyxy")}],
                key=lambda a: (-a["score"], a["instance_id"]),
            )
            existing_grp["instance_ids"] = [a["instance_id"] for a in existing_grp["alternatives"]]
            existing_grp["grouping_evidence"] = list(existing_grp["grouping_evidence"]) + [ev]
        else:
            members = [ina, anak]
            groups.append({
                "representative_id": ina["instance_id"],
                "instance_ids": [p["instance_id"] for p in members],
                "selected_instance_id": ina["instance_id"],
                "selection_status": "SELECTED_FOR_READING_ONLY",
                "grouping_scope": "SHARED_MASK_ROLE_HYPOTHESIS; not verified physical identity",
                "grouping_evidence": [ev],
                "alternatives": [{k: p[k] for k in ("instance_id", "class_label", "category_id", "score", "bbox_xyxy")} for p in members],
            })
    if suppressed_anak_ids:
        selected = [p for p in selected if p["instance_id"] not in suppressed_anak_ids]
    return selected,groups,tied_ids


def expand_role_ids(ids,role_groups):
    result=set(ids)
    for group in role_groups:
        if group["representative_id"] in result:result.update(group["instance_ids"])
    return sorted(result)


def decorate_unit(unit, groups):
    """Simpan kandidat untuk induk maupun penutup tanpa mengubah nilai prediksi."""
    used_groups = [groups[key] for key in unit["source_instance_ids"] if key in groups]
    ids = set(unit["source_instance_ids"])
    for group in used_groups:
        ids.update(group["ina_ids"])
    unit["source_instance_ids"] = sorted(ids)
    unit["candidate_groups"] = used_groups
    main = groups[unit["ina_id"]]
    if len(main["ina_ids"])>1:
        unit["kind"] = "ALTERNATIVE_INA_GROUP"
        unit["ina_ids"] = main["ina_ids"]
        unit["reading"].update(alternatives=main["alternatives"],
            selected_instance_id=main["selected_instance_id"],
            selection_status=main["selection_status"],
            selection_policy="HIGHEST_CONFIDENCE_BEFORE_DIACRITIC_PAIRING")
        if main["selection_status"] == "TIED_CONFIDENCE":
            unit["reading"]["text"] = "["+" / ".join(c["base_latin"] for c in main["alternatives"])+"]"
        else:
            unit["reading"]["rules"] = list(unit["reading"]["rules"])+["SELECT_HIGHEST_CONFIDENCE_INA"]
    return unit


def arrange(document, lexicon=None):
    """Baca salinan data; daftar prediksi asli tidak dimutasi atau disaring ulang."""
    engine = Transliterator()
    visible = validate(document, engine)
    reading_items,role_groups,role_tied_ids=select_role_candidates(visible)
    raw_anchors = [p for p in reading_items if p["category_id"] < 19]
    anchors, groups, tied_ids = select_reading_anchors(raw_anchors, engine)
    tied_ids.update(role_tied_ids)
    signs = sorted([p for p in reading_items if p["category_id"] >= 19], key=lambda p:p["instance_id"])
    issues, lines, matches = [], [], []
    for group in role_groups:
        issues.append({"reason":"READING_ROLE_CANDIDATES","instance_ids":group["instance_ids"],"selected_instance_id":group["selected_instance_id"]})
    width = median([p["bbox_xyxy"][2]-p["bbox_xyxy"][0] for p in anchors]) if anchors else 1
    # Hubungan antartetangga mengikuti baris miring tanpa menjadikan Ina
    # bergoresan mendatar sebagai baris baru. Baris terpisah tidak dipaksa rata.
    components = {a["instance_id"]:a["instance_id"] for a in anchors}
    def parent(key):
        while components[key] != key:
            components[key] = components[components[key]]
            key = components[key]
        return key
    for i,a in enumerate(anchors):
        for b in anchors[i+1:]:
            left,right=sorted((a,b),key=lambda p:center(p)[0])
            lx1,ly1,lx2,ly2=left["bbox_xyxy"]
            rx1,ry1,rx2,ry2=right["bbox_xyxy"]
            horizontal_overlap=max(0,lx2-rx1)
            local_height=max(ly2-ly1,ry2-ry1)
            vertical_distance=abs(center(left)[1]-center(right)[1])
            if horizontal_overlap>LINE_OVERLAP_LIMIT*min(lx2-lx1,rx2-rx1) and vertical_distance>LINE_ALIGNMENT*local_height:
                continue
            if rx1-lx2>LINE_NEIGHBOR_GAP*width and vertical_distance>LINE_ALIGNMENT*local_height:
                continue
            if vertical_distance<=LINE_HEIGHT_TOLERANCE*local_height:
                components[parent(right["instance_id"])]=parent(left["instance_id"])
    by_line={}
    for a in anchors:
        by_line.setdefault(parent(a["instance_id"]),[]).append(a)
    lines=list(by_line.values())
    lines.sort(key=lambda line:median(center(p)[1] for p in line))
    virtual_height={a["instance_id"]:max(p["bbox_xyxy"][3]-p["bbox_xyxy"][1] for p in line) for line in lines for a in line}
    line_width={a["instance_id"]:median(p["bbox_xyxy"][2]-p["bbox_xyxy"][0] for p in line) for line in lines for a in line}
    attached = {p["instance_id"]: [] for p in anchors}
    blocked = set(tied_ids)
    pending_signs={p["instance_id"]:[] for p in anchors}
    for i,a in enumerate(anchors):
        for b in anchors[i+1:]:
            if iou(a,b) >= OVERLAP_CONFLICT:
                blocked.update([a["instance_id"],b["instance_id"]])
                issues.append({"reason":"OVERLAPPING_INA", "instance_ids":[a["instance_id"],b["instance_id"]]})
    for sign in sorted(signs,key=lambda p:(0 if p["category_id"] in range(19,23) else (1 if p["category_id"]==23 else 2),p["instance_id"])):
        (tx,ty), (xmin,xmax,ymin,ymax) = PROFILES[sign["category_id"]]
        sx,sy = center(sign)
        candidates, fallback_candidates = [], []
        for base in anchors:
            x1,y1,x2,y2 = base["bbox_xyxy"]
            # Ng dan pangolat dapat mengikuti glyph vokal yang menempati ruang.
            if sign["category_id"] in (23,24):
                spacing=[p for p in attached[base["instance_id"]] if p["category_id"] in (20,21,22)]
                x2=max([x2]+[p["bbox_xyxy"][2] for p in spacing])
            for bucket,normalized_width in ((candidates,x2-x1),(fallback_candidates,max(x2-x1,line_width[base["instance_id"]]))):
                nx,ny = (sx-x1)/normalized_width,(sy-y1)/virtual_height[base["instance_id"]]
                if xmin <= nx <= xmax and ymin <= ny <= ymax:
                    cost = math.hypot(nx-tx,ny-ty)
                    if cost <= MAX_PAIR_COST:
                        bucket.append({"ina_id":base["instance_id"],"cost":cost})
        geometry_basis="LOCAL_GLYPH_AND_ATTACHED_VOWEL"
        if not candidates:
            candidates=fallback_candidates
            geometry_basis="LINE_MEDIAN_WIDTH_FALLBACK"
        candidates.sort(key=lambda c:(c["cost"],c["ina_id"]))
        record = {"anak_id":sign["instance_id"], "candidates":candidates, "ina_id":None,"geometry_basis":geometry_basis}
        if not candidates:
            record["status"] = "UNPAIRED"
        elif sign["instance_id"] in role_tied_ids or candidates[0]["ina_id"] in blocked or (len(candidates)>1 and candidates[1]["cost"]-candidates[0]["cost"] < PAIR_MARGIN):
            record["status"] = "AMBIGUOUS"
            for candidate in candidates:
                if candidate["cost"]-candidates[0]["cost"]<PAIR_MARGIN:
                    pending_signs[candidate["ina_id"]].append(sign["instance_id"])
        else:
            record.update(status="PROPOSED",ina_id=candidates[0]["ina_id"])
            attached[record["ina_id"]].append(sign)
        if record["status"] != "PROPOSED":
            issues.append({"reason":"SIGN_"+record["status"],"instance_ids":[sign["instance_id"]]})
        record["source_instance_ids"]=expand_role_ids([sign["instance_id"]],role_groups)
        matches.append(record)

    for group in groups.values():
        if len(group["ina_ids"])>1:
            issues.append({"reason":"READING_CANDIDATE_GROUP", "instance_ids":group["ina_ids"], "selected_instance_id":group["selected_instance_id"]})
    def sign_mask_evidence(a, b):
        overlap = iou(a, b)
        if overlap < MASK_CANDIDATE_BBOX_IOU_MIN:
            return None
        masks = mask_overlap(a, b)
        if masks is None or masks["mask_iou"] < MASK_CANDIDATE_IOU_MIN:
            return None
        return {"rule": "SHARED_FOREGROUND_MASK", "bbox_iou": overlap, **masks}

    all_attached=attached
    attached={};sign_groups=[]
    for bid,marks in all_attached.items():
        dedup_marks = []
        mask_clusters = []
        for mark in sorted(marks, key=lambda p: (center(p)[0], center(p)[1], p["instance_id"])):
            cluster = next((g for g in mask_clusters if all(sign_mask_evidence(mark, p) is not None for p in g)), None)
            if cluster is None:
                mask_clusters.append([mark])
            else:
                cluster.append(mark)
        for cluster in mask_clusters:
            if len(cluster) < 2:
                dedup_marks.extend(cluster)
                continue
            cluster = sorted(cluster, key=lambda p: (-p["score"], p["instance_id"]))
            tied = cluster[0]["score"] == cluster[1]["score"]
            winner = None if tied else cluster[0]["instance_id"]
            if tied:
                pending_signs[bid].extend(p["instance_id"] for p in cluster)
                dedup_marks.extend(cluster)
            else:
                dedup_marks.append(cluster[0])
            group = {
                "ina_id": bid,
                "role": "SHARED_MASK",
                "sign_ids": [p["instance_id"] for p in cluster],
                "selected_instance_id": winner,
                "selection_status": "TIED_CONFIDENCE" if tied else "SELECTED_FOR_READING_ONLY",
                "grouping_scope": "SHARED_FOREGROUND_MASK_SIGN_CONFLICT; not verified same physical object",
                "grouping_evidence": [
                    {"instance_ids": [a["instance_id"], b["instance_id"]], **sign_mask_evidence(a, b)}
                    for i, a in enumerate(cluster)
                    for b in cluster[i + 1:]
                ],
                "alternatives": [{"instance_id": p["instance_id"], "class_label": p["class_label"], "score": p["score"]} for p in cluster],
            }
            sign_groups.append(group)
            issues.append({"reason": "READING_SIGN_CANDIDATES", "instance_ids": group["sign_ids"], "ina_id": bid, "selected_instance_id": winner})
            for match in matches:
                if match["anak_id"] in group["sign_ids"]:
                    match["reading_selected"] = None if tied else match["anak_id"] == winner
                    match["reading_role"] = "SHARED_MASK"
        selected=[]
        for role,categories in (("VOWEL",range(19,23)),("FINAL_NG",[23]),("KILLER",[24])):
            candidates=sorted((p for p in dedup_marks if p["category_id"] in categories),key=lambda p:(-p["score"],p["instance_id"]))
            if len(candidates)<2:
                selected.extend(candidates);continue
            tied=candidates[0]["score"]==candidates[1]["score"]
            winner=None if tied else candidates[0]["instance_id"]
            selected.extend(candidates if tied else candidates[:1])
            group={"ina_id":bid,"role":role,"sign_ids":[p["instance_id"] for p in candidates],
                   "selected_instance_id":winner,"selection_status":"TIED_CONFIDENCE" if tied else "SELECTED_FOR_READING_ONLY",
                   "grouping_scope":"MUTUALLY_EXCLUSIVE_LOGICAL_SIGN_ROLE; not verified same physical object",
                   "alternatives":[{"instance_id":p["instance_id"],"class_label":p["class_label"],"score":p["score"]} for p in candidates]}
            sign_groups.append(group)
            issues.append({"reason":"READING_SIGN_CANDIDATES","instance_ids":group["sign_ids"],"ina_id":bid,"selected_instance_id":winner})
            for match in matches:
                if match["anak_id"] in group["sign_ids"]:
                    match["reading_selected"]=None if tied else match["anak_id"]==winner
                    match["reading_role"]=role
        attached[bid]=selected
    result_lines = []
    for line_no,line in enumerate(lines,1):
        line.sort(key=lambda p:(center(p)[0],p["instance_id"]))
        units, i = [], 0
        while i < len(line):
            base = line[i]; bid = base["instance_id"]
            marks = attached[bid]
            labels = [p["class_label"] for p in marks]
            source_ids = [bid]+[p["instance_id"] for p in all_attached[bid]]
            next_base = line[i+1] if i+1<len(line) else None
            trace = "DIRECT_LOGICAL_UNIT"
            kwargs = {}
            consumed = 1
            # Tanda vokal dapat dirender dekat konsonan penutup berpangolat.
            if next_base is not None and bid not in blocked and next_base["instance_id"] not in blocked and not labels:
                next_marks = attached[next_base["instance_id"]]
                vowel = [p for p in next_marks if 19 <= p["category_id"] <= 22]
                killers = [p for p in next_marks if p["category_id"] == 24]
                gap = next_base["bbox_xyxy"][0]-base["bbox_xyxy"][2]
                local_width=max(line_width[bid],base["bbox_xyxy"][2]-base["bbox_xyxy"][0],next_base["bbox_xyxy"][2]-next_base["bbox_xyxy"][0])
                if len(next_marks)==2 and len(vowel)==1 and len(killers)==1 and gap <= 0.75*local_width and base["category_id"] not in (17,18) and next_base["category_id"] not in [0,17,18]:
                    labels = [vowel[0]["class_label"]]
                    kwargs = {"coda":next_base["class_label"],"coda_marks":["anak_pangolat"]}
                    source_ids += [next_base["instance_id"]]+[p["instance_id"] for p in all_attached[next_base["instance_id"]]]
                    trace = "DRAFT_CLOSED_SYLLABLE_REORDER"
                    consumed = 2
            unresolved_pairings=sorted(set(pending_signs[bid]+(pending_signs[next_base["instance_id"]] if consumed==2 else [])))
            if bid in blocked or unresolved_pairings:
                reading = {"text":"[?]","status":"AMBIGUOUS","warnings":["Pasangan/objek bertumpang tindih perlu diperiksa."],"rules":[]}
            else:
                reading = asdict(engine.read_unit(base["class_label"],labels,**kwargs))
            unit = {"ina_id":bid,"source_instance_ids":source_ids,"reading":reading,"geometry_rule":trace}
            if unresolved_pairings:unit["pending_sign_ids"]=unresolved_pairings
            unit_sign_groups=[g for g in sign_groups if g["ina_id"] in source_ids]
            if unit_sign_groups:
                unit["sign_candidate_groups"]=unit_sign_groups
                if any(g["selected_instance_id"] is not None for g in unit_sign_groups):
                    reading["rules"]=list(reading["rules"])+["SELECT_HIGHEST_CONFIDENCE_ANAK_PER_LOGICAL_ROLE"]
            if reading["status"] != "RULE_APPLIED":
                issues.append({"reason":reading["status"],"instance_ids":source_ids})
            unit=decorate_unit(unit,groups)
            unit["source_instance_ids"]=expand_role_ids(unit["source_instance_ids"],role_groups)
            units.append(unit);i += consumed
        literal_text="".join(u["reading"]["text"] for u in units)
        # Ya/Wa sebagai penyambung dua vokal; bentuk harfiah tetap disimpan.
        normalized=[]
        for unit in units:
            value=unit["reading"]["text"]
            previous=normalized[-1] if normalized else ""
            label=next((a["class_label"] for a in anchors if a["instance_id"]==unit["ina_id"]),None)
            has_vowel_after_glide=len(value)>1 and value[1] in "aeiou"
            if previous and has_vowel_after_glide and ((label=="ina_ya" and previous[-1:] in "ie" and value[:1]=="y") or (label=="ina_wa" and previous.endswith("u") and value[:1]=="w")):
                value=value[1:]
                unit["reading"]["orthographic_text"]=value
                unit["reading"]["orthographic_rule"]="REMOVE_INTERVOCALIC_GLIDE_FOR_LATIN_SPELLING"
            normalized.append(value)
        result_lines.append({"line_number":line_no,"units":units,"text_literal":literal_text,"text":"".join(normalized)})
    result = {
        "stage":"DEVELOPMENT_READING_NOT_INDEPENDENTLY_VALIDATED", "version":VERSION,
        "input_kind":document.get("input_kind","SAVED_UI_PREDICTIONS"),
        "rules_version":engine.version, "checkpoint_sha256":document.get("checkpoint_sha256"),
        "source_sha256":document.get("source_sha256"), "display_threshold":THRESHOLD,
        "raw_prediction_count":len(document["predictions"]), "visible_instance_ids":[p["instance_id"] for p in visible],
        "text_automatic":"\n".join(line["text"] for line in result_lines),
        "text_literal":"\n".join(line["text_literal"] for line in result_lines),
        "text_status":"NEEDS_REVIEW" if issues else ("DRAFT_READING" if anchors else "NO_PREDICTIONS"),
        "word_boundaries":"NOT_INFERRED", "lines":result_lines,"assignments":matches,"issues":issues,
        "development_context":"Rules and geometry revised after inspection of exposed testing; no independent text accuracy claimed",
        "latin_spelling":"INTERVOCALIC_YA_WA_NORMALIZED; literal reading retained; no dictionary or PDF answer lookup",
        "overlap_reading_policy":"HIGHEST_CONFIDENCE_PER_COMPLETE_LINK_LOCATION_GROUP; high bbox IoU, aligned containment, or shared foreground mask; equal top scores remain ambiguous; raw detections retained",
        "reading_candidate_groups":list(groups.values()),
        "sign_candidate_groups":sign_groups,
        "role_candidate_groups":role_groups,
        "geometry_uses":"BBOX_PAIRING; RLE_FOREGROUND_OVERLAP_FOR_ROLE_AND_INA_CANDIDATES; original masks unchanged",
        "parameters":{"line_alignment":LINE_ALIGNMENT,"line_height_tolerance":LINE_HEIGHT_TOLERANCE,"line_neighbor_gap":LINE_NEIGHBOR_GAP,"line_overlap_limit":LINE_OVERLAP_LIMIT,"overlap_conflict":OVERLAP_CONFLICT,
                      "contained_reading_candidate":{"containment_min":CONTAINMENT_MIN,"area_ratio_min":CONTAINED_AREA_RATIO_MIN,"x_overlap_min":CONTAINED_X_OVERLAP_MIN,"x_center_max":CONTAINED_X_CENTER_MAX,"y_center_max":CONTAINED_Y_CENTER_MAX},
                      "mask_candidate":{"mask_iou_min":MASK_CANDIDATE_IOU_MIN,"bbox_iou_min":MASK_CANDIDATE_BBOX_IOU_MIN,
                          "aligned_column_fragment":{"x_overlap_min":CONTAINED_X_OVERLAP_MIN,"x_center_max":CONTAINED_X_CENTER_MAX}},
                      "composite_ina_candidate":{"coverage_min":COMPOSITE_INA_COVERAGE_MIN,"part_containment_min":COMPOSITE_INA_PART_CONTAINMENT_MIN,"part_share_min":COMPOSITE_INA_PART_SHARE_MIN},
                      "role_candidate":{"mask_iou_min":MASK_CANDIDATE_IOU_MIN,"bbox_iou_min":MASK_CANDIDATE_BBOX_IOU_MIN,
                          "contained_anak_mask_min":CONTAINED_ANAK_MASK_MIN,"contained_anak_bbox_min":CONTAINED_ANAK_BBOX_MIN},
                      "shared_mask_sign_candidate":{"mask_iou_min":MASK_CANDIDATE_IOU_MIN,"bbox_iou_min":MASK_CANDIDATE_BBOX_IOU_MIN},
                      "pair_margin":PAIR_MARGIN,"max_pair_cost":MAX_PAIR_COST,"profiles":PROFILES},
    }
    if lexicon is not None:
        if lexicon.get("language")!="batak_toba" or not all(lexicon.get(k) for k in ("source","license","revision")):
            raise ValueError("Kosakata memerlukan bahasa Toba, sumber, lisensi dan revisi.")
        words=lexicon.get("words")
        if not isinstance(words,list) or not words:
            raise ValueError("Daftar kosakata tidak boleh kosong.")
        boundaries=set();position=0
        for line in result_lines:
            for unit in line["units"]:
                position+=len(unit["reading"].get("orthographic_text",unit["reading"]["text"]))
                boundaries.add(position)
            position+=1
        result["word_spacing"]=suggest_spaces(result["text_automatic"],set(words),boundaries)
        result["word_spacing"]["boundary_policy"]="BETWEEN_EXISTING_READING_UNITS_ONLY"
        result["word_spacing"]["lexicon"]={k:lexicon[k] for k in ("language","source","license","revision")}
        result["word_spacing"]["lexicon_sha256"]=hashlib.sha256(json.dumps(lexicon,sort_keys=True,ensure_ascii=True).encode()).hexdigest()
        result["word_spacing"]["review_required"]=True
        result["word_spacing"]["review_reasons"]=["LEXICON_UNIQUENESS_IS_NOT_LANGUAGE_VALIDATION"]
        if result["issues"]:
            result["word_spacing"]["suggested_text"]=result["text_automatic"]
            result["word_spacing"]["status"]="NEEDS_REVIEW"
            result["word_spacing"]["review_reasons"].append("READING_HAS_RECORDED_ISSUES")
    unresolved=[]
    for line in result_lines:
        for number,unit in enumerate(line["units"],1):
            if unit["reading"]["status"]=="AMBIGUOUS":
                unresolved.append({"line_number":line["line_number"],"unit_number":number,
                    "source_instance_ids":unit["source_instance_ids"],
                    "reasons":list(unit["reading"].get("warnings",[])),
                    "pending_sign_ids":unit.get("pending_sign_ids",[])})
    display=lambda text:text.replace("[?]","⟦belum terbaca⟧")
    result["presentation"]={"automatic_text":display(result["text_automatic"]),
        "literal_text":display(result["text_literal"]),
        "spacing_suggestion":display(result.get("word_spacing",{}).get("suggested_text",result["text_automatic"])),
        "has_unresolved_units":bool(unresolved),"unresolved_units":unresolved,
        "unpaired_signs":[m for m in matches if m["status"]!="PROPOSED"],
        "note":"Readable presentation only; original diagnostic text retained; no missing characters inferred."}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions",type=Path,required=True,help="JSON ekspor UI satu citra.")
    parser.add_argument("--output",type=Path,help="Berkas JSON baru; keluaran yang sudah ada tidak ditimpa.")
    parser.add_argument("--lexicon",type=Path,help="Kosakata Toba JSON untuk usulan spasi opsional.")
    args = parser.parse_args()
    document = json.loads(args.predictions.read_text(encoding="utf-8-sig"))
    lexicon=json.loads(args.lexicon.read_text(encoding="utf-8-sig")) if args.lexicon else None
    result = arrange(document,lexicon=lexicon)
    text = json.dumps(result,ensure_ascii=True,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open("x",encoding="utf-8") as stream:
            stream.write(text+"\n")
    print(text)


if __name__ == "__main__":
    main()
