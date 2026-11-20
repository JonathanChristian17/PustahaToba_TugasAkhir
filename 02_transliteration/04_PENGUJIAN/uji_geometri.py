"""Fixture koordinat untuk uji perangkat lunak; bukan sampel penelitian."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "02_MODUL_TRANSLITERASI"))
import susun_prediksi as geometry
from transliterasi import Transliterator

NAMES = {v["id"]:v["name"] for v in Transliterator().classes.values()}


def pred(key,cid,box,score=.9):
    return {"instance_id":key,"category_id":cid,"class_label":NAMES[cid],"score":score,
            "bbox_xyxy":box,"displayed":score>=.5,"segmentation":{"fixture_only":True}}


def fixture(*rows):
    return {"input_kind":"SOFTWARE_FIXTURE_NOT_IMAGE_INFERENCE","checkpoint_sha256":geometry.CHECKPOINT_HASH,
            "display_threshold":.5,"predictions":list(rows)}


class TestGeometry(unittest.TestCase):
    def test_reading_order_not_confidence_order(self):
        result=geometry.arrange(fixture(pred(1,6,[120,20,200,100],.99),pred(2,14,[0,20,80,100],.6)))
        self.assertEqual(result["text_automatic"],"saba")
        self.assertEqual([u["ina_id"] for u in result["lines"][0]["units"]],[2,1])

    def test_right_vowel_sign(self):
        r=geometry.arrange(fixture(pred(1,6,[0,20,100,120]),pred(2,20,[105,70,115,90])))
        self.assertEqual(r["text_automatic"],"bi")
        self.assertEqual(r["assignments"][0]["ina_id"],1)

    def test_touching_haborotan(self):
        r=geometry.arrange(fixture(pred(1,6,[0,20,100,120]),pred(2,22,[65,95,95,125])))
        self.assertEqual(r["text_automatic"],"bu")

    def test_upper_left_e_and_upper_right_ng(self):
        r=geometry.arrange(fixture(pred(1,6,[0,100,100,200]),pred(2,19,[10,80,30,90]),pred(3,23,[80,80,100,90])))
        self.assertEqual(r["text_automatic"],"beng")

    def test_two_lines(self):
        r=geometry.arrange(fixture(pred(1,6,[0,0,100,80]),pred(2,10,[0,200,100,280])))
        self.assertEqual(r["text_automatic"],"ba\nja")

    def test_killer_reordering_with_visual_vowel_near_coda(self):
        r=geometry.arrange(fixture(pred(1,5,[0,20,80,100]),pred(2,7,[100,20,180,100]),
                                  pred(3,20,[181,50,189,60]),pred(4,24,[190,70,200,90])))
        self.assertEqual(r["text_automatic"],"tip")
        self.assertEqual(set(r["lines"][0]["units"][0]["source_instance_ids"]),{1,2,3,4})
        self.assertEqual(r["lines"][0]["units"][0]["geometry_rule"],"DRAFT_CLOSED_SYLLABLE_REORDER")

    def test_overlapping_classes_retained_and_flagged(self):
        r=geometry.arrange(fixture(pred(1,17,[0,20,100,120]),pred(2,4,[2,20,102,120])))
        self.assertEqual(r["visible_instance_ids"],[1,2])
        self.assertTrue(any(x["reason"]=="READING_CANDIDATE_GROUP" for x in r["issues"]))
        self.assertEqual(r["text_status"],"NEEDS_REVIEW")

    def test_two_similar_candidate_costs_not_forced(self):
        r=geometry.arrange(fixture(pred(1,6,[0,100,100,200]),pred(2,3,[120,100,220,200]),
                                  pred(3,19,[70,80,80,90])))
        self.assertEqual(r["assignments"][0]["status"],"AMBIGUOUS")

    def test_distant_sign_is_unpaired(self):
        r=geometry.arrange(fixture(pred(1,6,[0,20,100,120]),pred(2,20,[900,40,910,50])))
        self.assertEqual(r["assignments"][0]["status"],"UNPAIRED")
        self.assertEqual(r["text_status"],"NEEDS_REVIEW")

    def test_below_threshold_not_deleted_from_input(self):
        d=fixture(pred(1,6,[0,20,100,120]),pred(2,4,[0,20,100,120],.49))
        before=copy.deepcopy(d);r=geometry.arrange(d)
        self.assertEqual(r["visible_instance_ids"],[1]);self.assertEqual(d,before)

    def test_inconsistent_display_flag_rejected(self):
        d=fixture(pred(1,6,[0,20,100,120]));d["predictions"][0]["displayed"]=False
        with self.assertRaises(ValueError):geometry.arrange(d)

    def test_no_guess_at_word_boundaries(self):
        r=geometry.arrange(fixture(pred(1,6,[0,20,100,120]),pred(2,6,[500,20,600,120])))
        self.assertEqual(r["text_automatic"],"baba")
        self.assertEqual(r["word_boundaries"],"NOT_INFERRED")

    def test_empty_and_sign_only(self):
        self.assertEqual(geometry.arrange(fixture())["text_status"],"NO_PREDICTIONS")
        self.assertEqual(geometry.arrange(fixture(pred(1,20,[0,0,10,10])))["text_status"],"NEEDS_REVIEW")

    def test_input_and_mask_unchanged(self):
        d=fixture(pred(1,6,[0,20,100,120]),pred(2,20,[105,70,115,90]))
        original=json.dumps(d,sort_keys=True);geometry.arrange(d)
        self.assertEqual(original,json.dumps(d,sort_keys=True))

    def test_duplicate_ids_and_bad_bbox_rejected(self):
        for d in [fixture(pred(1,6,[0,0,10,10]),pred(1,3,[20,0,30,10])),fixture(pred(1,6,[0,0,0,10]))]:
            with self.assertRaises(ValueError):geometry.arrange(d)

    def test_other_experiment_rejected(self):
        d=fixture();d["checkpoint_sha256"]="run400"
        with self.assertRaises(ValueError):geometry.arrange(d)

    def test_alternatives_one_group_with_scores_and_original_ids(self):
        d=fixture(pred(1,6,[150,20,250,120],.99),pred(2,22,[225,95,255,125],.98),
                  pred(3,10,[0,20,100,120],.85),pred(4,17,[2,20,102,120],.62))
        original=copy.deepcopy(d)
        r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'jabu')
        self.assertEqual(len(r['lines'][0]['units']),2)
        group=r['lines'][0]['units'][0]
        self.assertEqual(group['ina_id'],3)
        self.assertEqual(group['ina_ids'],[3,4])
        self.assertEqual(group['source_instance_ids'],[3,4])
        self.assertEqual([(c['instance_id'],c['score']) for c in group['reading']['alternatives']],[(3,.85),(4,.62)])
        self.assertEqual(len(group['candidate_groups'][0]['alternatives']),2)
        self.assertEqual(group['reading']['selected_instance_id'],3)
        self.assertEqual(group['reading']['selection_status'],'SELECTED_FOR_READING_ONLY')
        self.assertEqual(r['assignments'][0]['ina_id'],1)
        self.assertEqual(d,original)
        self.assertEqual(r['text_status'],'NEEDS_REVIEW')

    def test_alternative_group_does_not_follow_input_order(self):
        rows=[pred(3,10,[0,20,100,120],.85),pred(4,17,[2,20,102,120],.62)]
        a=geometry.arrange(fixture(*rows))
        b=geometry.arrange(fixture(*reversed(rows)))
        self.assertEqual(a['lines'],b['lines'])

    def test_overlapping_chain_not_all_one_location(self):
        r=geometry.arrange(fixture(pred(1,10,[0,20,100,120]),pred(2,17,[18,20,118,120]),pred(3,4,[36,20,136,120])))
        units=r['lines'][0]['units']
        self.assertEqual(len(units),2)
        self.assertEqual(sorted(key for u in units for key in u['source_instance_ids']),[1,2,3])
        self.assertEqual(len(units[0]['candidate_groups'][0]['alternatives']),2)

    def test_nonoverlapping_ambiguous_anchors_not_merged(self):
        r=geometry.arrange(fixture(pred(1,6,[0,100,100,200]),pred(2,3,[120,100,220,200]),pred(3,19,[70,80,80,90])))
        self.assertEqual(len(r['lines'][0]['units']),2)
        self.assertFalse(any(u.get('kind')=='ALTERNATIVE_INA_GROUP' for u in r['lines'][0]['units']))

    def test_identical_class_duplicates_retain_both_ids(self):
        r=geometry.arrange(fixture(pred(1,10,[0,20,100,120],.8),pred(2,10,[2,20,102,120],.7)))
        unit=r['lines'][0]['units'][0]
        self.assertEqual(unit['ina_ids'],[1,2])
        self.assertEqual(unit['reading']['text'],'ja')
        self.assertEqual(unit['reading']['selected_instance_id'],1)

    def test_winner_can_be_any_class_not_hardcoded_ja(self):
        r=geometry.arrange(fixture(pred(1,10,[0,20,100,120],.61),pred(2,17,[2,20,102,120],.9)))
        self.assertEqual(r['text_automatic'],'i')
        self.assertEqual(r['lines'][0]['units'][0]['reading']['selected_instance_id'],2)

    def test_equal_scores_keep_ambiguity_without_arbitrary_winner(self):
        r=geometry.arrange(fixture(pred(1,10,[0,20,100,120],.9),pred(2,17,[2,20,102,120],.9)))
        reading=r['lines'][0]['units'][0]['reading']
        self.assertEqual(reading['text'],'[ja / i]')
        self.assertIsNone(reading['selected_instance_id'])
        self.assertEqual(reading['selection_status'],'TIED_CONFIDENCE')

    def test_selection_precedes_anak_pairing_without_losing_predictions(self):
        d=fixture(pred(1,6,[0,20,100,120],.9),pred(2,3,[2,20,102,120],.6),pred(3,22,[70,100,90,120],.95))
        original=copy.deepcopy(d);r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'bu')
        self.assertEqual(r['assignments'][0]['status'],'PROPOSED')
        self.assertEqual(r['assignments'][0]['ina_id'],1)
        self.assertEqual(r['assignments'][0]['anak_id'],3)
        self.assertEqual(r['visible_instance_ids'],[1,2,3])
        self.assertEqual(r['text_status'],'NEEDS_REVIEW')
        self.assertEqual(d,original)

    def test_carrier_closed_syllable_with_alternatives_on_both_bases(self):
        d=fixture(pred(1,0,[0,20,100,100]),pred(2,0,[120,20,220,100],.97),
                  pred(3,1,[120,20,220,100],.7),pred(4,1,[240,20,320,100],.93),
                  pred(5,4,[240,20,320,100],.6),pred(6,19,[250,0,270,10],.96),
                  pred(7,24,[325,60,335,80],.99))
        original=copy.deepcopy(d);r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'aek')
        self.assertEqual(r['assignments'][0]['ina_id'],4)
        self.assertEqual(r['assignments'][1]['ina_id'],4)
        self.assertEqual(r['lines'][0]['units'][1]['reading']['text'],'ek')
        self.assertEqual(sorted(k for u in r['lines'][0]['units'] for k in u['source_instance_ids']),list(range(1,8)))
        self.assertEqual(d,original)
        # Aturan harus mengikuti geometri pada skala dan posisi lain.
        shifted=copy.deepcopy(d)
        for p in shifted['predictions']:
            p['bbox_xyxy']=[v*2+(500 if i%2==0 else 300) for i,v in enumerate(p['bbox_xyxy'])]
        self.assertEqual(geometry.arrange(shifted)['text_automatic'],'aek')

    def test_tied_ina_still_prevents_forced_sign_attachment(self):
        d=fixture(pred(1,6,[0,20,100,120],.9),pred(2,3,[2,20,102,120],.9),pred(3,22,[70,100,90,120],.95))
        r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'[ba / na]')
        self.assertEqual(r['assignments'][0]['status'],'AMBIGUOUS')

    def test_higher_confidence_class_not_replaced_to_match_word(self):
        d=fixture(pred(1,0,[0,20,100,100]),pred(2,0,[120,20,220,100],.7),
                  pred(3,1,[120,20,220,100],.97),pred(4,1,[240,20,320,100],.93),
                  pred(5,19,[250,0,270,10],.96),pred(6,24,[325,60,335,80],.99))
        d['source_name']='P01_N06_006.png'
        self.assertEqual(geometry.arrange(d)['text_automatic'],'ahek')

    def test_horizontal_pa_uses_line_height_for_right_vowel(self):
        d=fixture(pred(1,7,[0,100,100,115]),pred(2,20,[105,100,120,150]),
                  pred(3,14,[250,100,350,200]))
        self.assertEqual(geometry.arrange(d)['text_automatic'],'pisa')

    def test_neighboring_glyphs_follow_a_sloped_single_line(self):
        d=fixture(pred(1,6,[0,150,100,250]),pred(2,6,[140,100,240,200]),
                  pred(3,6,[280,50,380,150]))
        self.assertEqual(geometry.arrange(d)['text_automatic'],'bababa')
        self.assertEqual(len(geometry.arrange(d)['lines']),1)

    def test_spacing_vowel_extends_reach_for_ng(self):
        d=fixture(pred(1,5,[0,100,40,200]),pred(2,21,[70,130,100,180]),
                  pred(3,23,[75,90,95,100]))
        r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'tong')
        self.assertEqual({a['ina_id'] for a in r['assignments']},{1})

    def test_spacing_vowel_then_killer_closes_previous_syllable(self):
        d=fixture(pred(1,13,[0,100,80,200]),pred(2,14,[110,100,150,200]),
                  pred(3,21,[180,130,210,180]),pred(4,24,[240,140,260,180]))
        self.assertEqual(geometry.arrange(d)['text_automatic'],'los')

    def test_width_fallback_for_narrow_glyph_keeps_existing_pair_priority(self):
        d=fixture(pred(1,5,[140,20,169,58]),pred(2,21,[196,21,219,45]),
                  pred(3,6,[245,20,302,60]))
        r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'toba')
        self.assertEqual(r['assignments'][0]['geometry_basis'],'LINE_MEDIAN_WIDTH_FALLBACK')

    def test_normalized_glides_preserve_literal_reading(self):
        for first,sign,second,expected,literal in [(14,20,15,'sia','siya'),(11,22,8,'dua','duwa'),(7,19,15,'pea','peya')]:
            box=[20,80,35,90] if sign==19 else ([70,170,95,200] if sign==22 else [105,140,120,160])
            d=fixture(pred(1,first,[0,100,100,200]),pred(2,sign,box),pred(3,second,[250,100,350,200]))
            r=geometry.arrange(d)
            self.assertEqual(r['text_automatic'],expected)
            self.assertEqual(r['text_literal'],literal)
        d=fixture(pred(1,6,[0,100,100,200]),pred(2,8,[250,100,350,200]),pred(3,23,[330,80,345,90]))
        self.assertEqual(geometry.arrange(d)['text_automatic'],'bawang')

    def test_no_replacement_of_onset_ha_to_force_buku(self):
        d=fixture(pred(1,6,[0,100,100,200]),pred(2,22,[70,170,95,200]),
                  pred(3,1,[250,100,350,200]),pred(4,22,[320,170,345,200]))
        d['source_name']='buku_ni_anggi.png'
        self.assertEqual(geometry.arrange(d)['text_automatic'],'buhu')
        d['source_name']='huta.png'
        self.assertEqual(geometry.arrange(d)['text_automatic'],'buhu')

    def test_missing_ng_is_not_inserted_from_expected_word(self):
        d=fixture(pred(1,0,[0,100,100,200]),pred(2,2,[250,100,350,200]))
        d['expected_text']='amang'
        self.assertEqual(geometry.arrange(d)['text_automatic'],'ama')

    def test_killed_ya_is_not_a_vowel_glide(self):
        d=fixture(pred(1,17,[0,100,100,200]),pred(2,15,[250,100,350,200]),
                  pred(3,24,[355,140,370,170]))
        self.assertEqual(geometry.arrange(d)['text_automatic'],'iy')

    def test_aligned_contained_da_is_alternative_to_i(self):
        d=fixture(pred(1,3,[220,70,380,200],.995),pred(2,17,[40,50,170,157],.973),
                  pred(3,11,[37,52,169,114],.565))
        before=copy.deepcopy(d);r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'ina')
        group=next(g for g in r['reading_candidate_groups'] if len(g['ina_ids'])>1)
        self.assertEqual(group['selected_instance_id'],2)
        self.assertEqual(set(group['ina_ids']),{2,3})
        self.assertEqual(group['grouping_evidence'][0]['rule'],'ALIGNED_CONTAINED_BBOX')
        self.assertEqual(d,before)
        self.assertEqual(r['visible_instance_ids'],[1,2,3])

    def test_contained_group_selects_score_even_if_class_is_wrong(self):
        d=fixture(pred(1,17,[40,50,170,157],.6),pred(2,11,[37,52,169,114],.95))
        self.assertEqual(geometry.arrange(d)['text_automatic'],'da')
        d['expected_text']='i'
        self.assertEqual(geometry.arrange(d)['text_automatic'],'da')

    def test_equal_scores_in_contained_group_remain_ambiguous(self):
        d=fixture(pred(1,17,[40,50,170,157],.9),pred(2,11,[37,52,169,114],.9))
        r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'[i / da]')
        self.assertIsNone(r['reading_candidate_groups'][0]['selected_instance_id'])

    def test_small_fragment_not_merged_with_whole_ina(self):
        d=fixture(pred(1,17,[0,0,100,100]),pred(2,7,[0,0,100,15],.7))
        self.assertIsNone(geometry.reading_overlap(*d['predictions']))
        self.assertEqual(len(geometry.arrange(d)['reading_candidate_groups']),2)

    def test_side_by_side_touching_ina_are_separate(self):
        for box in ([85,0,185,100],[0,110,100,210]):
            d=fixture(pred(1,3,[0,0,100,100]),pred(2,3,box,.8))
            self.assertIsNone(geometry.reading_overlap(*d['predictions']))
            self.assertEqual(len(geometry.arrange(d)['reading_candidate_groups']),2)

    def test_offset_contained_box_not_merged_by_containment_alone(self):
        d=fixture(pred(1,17,[0,0,100,100]),pred(2,11,[50,0,100,80],.7))
        self.assertIsNone(geometry.reading_overlap(*d['predictions']))
        self.assertEqual(len(geometry.arrange(d)['reading_candidate_groups']),2)

    def test_contained_group_independent_of_prediction_input_order(self):
        d=fixture(pred(1,17,[40,50,170,157],.973),pred(2,11,[37,52,169,114],.565))
        a=geometry.arrange(d)
        d['predictions'].reverse();b=geometry.arrange(d)
        self.assertEqual(a['lines'],b['lines'])
        self.assertEqual(a['reading_candidate_groups'],b['reading_candidate_groups'])

    def test_ahu_from_coordinates_does_not_follow_expected_word(self):
        d=fixture(pred(1,0,[0,100,100,200]),pred(2,1,[250,100,350,200]),
                  pred(3,22,[320,175,345,200]))
        d['source_name']='aku.png';d['expected_text']='aku'
        r=geometry.arrange(d)
        self.assertEqual(r['text_automatic'],'ahu')
        self.assertEqual(r['text_literal'],'ahu')
        self.assertIn('TOBA_HA_ONSET_H',r['lines'][0]['units'][1]['reading']['rules'])


if __name__=="__main__":unittest.main(verbosity=2)
