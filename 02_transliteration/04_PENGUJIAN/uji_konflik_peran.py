"""Regresi peran dan penyajian; contoh koordinat buatan bukan eksperimen citra."""
import copy
import unittest
from uji_geometri import geometry,pred,fixture
import uji_kasus_minor as saved_tests


class TestRoleConflicts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        saved_tests.TestSavedMinorCases.setUpClass();cls.saved=saved_tests.TestSavedMinorCases()

    def test_real_cross_role_and_closed_syllable_cases(self):
        for image_id,expected in [(8,'poda'),(35,'ulos'),(50,'emediporlak'),(53,'ulosnianggi')]:
            doc=self.saved.document(image_id);before=copy.deepcopy(doc)
            result=geometry.arrange(doc)
            self.assertEqual(result['text_automatic'],expected)
            self.assertTrue(result['role_candidate_groups'])
            self.assertEqual(doc,before)

    def test_same_ink_cross_role_chooses_score_not_ina_preference(self):
        a=pred(1,6,[0,0,10,10],.7);b=pred(2,20,[0,0,10,10],.9)
        for p in [a,b]:p['segmentation']={'size':[10,10],'counts':[0,10,90]}
        items,groups,ties=geometry.select_role_candidates([a,b])
        self.assertEqual([p['instance_id'] for p in items],[2])
        self.assertEqual(groups[0]['selected_instance_id'],2);self.assertFalse(ties)

    def test_disjoint_masks_are_not_cross_role_alternatives(self):
        a=pred(1,6,[0,0,10,10]);b=pred(2,20,[0,0,10,10])
        a['segmentation']={'size':[10,10],'counts':[0,10,90]}
        b['segmentation']={'size':[10,10],'counts':[90,10]}
        items,groups,_=geometry.select_role_candidates([a,b])
        self.assertEqual(len(items),2);self.assertEqual(groups,[])

    def test_cross_role_tie_retains_unknown_and_both_ids(self):
        a=pred(1,6,[0,0,10,10],.9);b=pred(2,20,[0,0,10,10],.9)
        for p in [a,b]:p['segmentation']={'size':[10,10],'counts':[0,10,90]}
        result=geometry.arrange(fixture(a,b))
        self.assertIsNone(result['role_candidate_groups'][0]['selected_instance_id'])
        self.assertTrue(result['presentation']['has_unresolved_units'])
        self.assertEqual(result['lines'][0]['units'][0]['source_instance_ids'],[1,2])

    def test_ambiguous_sign_does_not_block_later_unique_pair(self):
        doc=fixture(pred(1,6,[0,100,100,200]),pred(2,6,[40,100,140,200]),
                    pred(3,20,[129,160,131,170]),pred(4,24,[150,160,160,170]))
        result=geometry.arrange(doc)
        pair={a['anak_id']:a for a in result['assignments']}
        self.assertEqual(pair[3]['status'],'AMBIGUOUS')
        self.assertEqual(pair[4]['status'],'PROPOSED');self.assertEqual(pair[4]['ina_id'],2)

    def test_real_fragment_keeps_whole_ina_and_trace(self):
        result=geometry.arrange(self.saved.document(4))
        group=next(g for g in result['reading_candidate_groups'] if 5 in g['ina_ids'])
        self.assertIn(6,group['ina_ids']);self.assertEqual(group['selected_instance_id'],5)

    def test_real_invalid_source_is_not_forced_to_pdf(self):
        result=geometry.arrange(self.saved.document(124),lexicon=self.saved.lex)
        self.assertEqual(result['text_automatic'],'pi[?]nianggi')
        self.assertEqual(result['presentation']['automatic_text'],'pi⟦belum terbaca⟧nianggi')
        self.assertNotIn('?',result['presentation']['spacing_suggestion'])
        self.assertTrue(result['presentation']['unresolved_units'][0]['reasons'])

    def test_missing_predictions_are_not_invented(self):
        result=geometry.arrange(self.saved.document(2))
        self.assertEqual(result['text_automatic'],'ina')
        self.assertEqual(result['presentation']['automatic_text'],'ina')

    def test_scale_order_and_translation_preserve_role_decision(self):
        doc=self.saved.document(35);before=geometry.arrange(doc)
        doc['predictions'].reverse()
        for p in doc['predictions']:p['bbox_xyxy']=[v*2+(50 if i%2==0 else 30) for i,v in enumerate(p['bbox_xyxy'])]
        result=geometry.arrange(doc)
        self.assertEqual(result['text_automatic'],before['text_automatic'])
        self.assertEqual([(g['instance_ids'],g['selected_instance_id']) for g in result['role_candidate_groups']],
                         [(g['instance_ids'],g['selected_instance_id']) for g in before['role_candidate_groups']])

    def test_real_id4_id43_id70_and_id58_non_regression(self):
        r4=geometry.arrange(self.saved.document(4))
        self.assertEqual(r4['text_automatic'],'unglos')
        self.assertEqual(r4['presentation']['unresolved_units'],[])
        grp3=next(g for g in r4['reading_candidate_groups'] if g['selected_instance_id']==3)
        self.assertIn(9,grp3['ina_ids'])
        sgrp=next(g for g in r4['sign_candidate_groups'] if g['role']=='SHARED_MASK')
        self.assertEqual(sorted(sgrp['sign_ids']),[7,8])
        self.assertEqual(sgrp['selected_instance_id'],7)
        claimed4=[i for l in r4['lines'] for u in l['units'] for i in u['source_instance_ids']]
        claimed4 += [i for a in r4['assignments'] if a['ina_id'] is None for i in a['source_instance_ids']]
        self.assertEqual(sorted(claimed4),list(range(1,10)))

        r43=geometry.arrange(self.saved.document(43))
        self.assertEqual(r43['text_automatic'],'dongan')

        r70=geometry.arrange(self.saved.document(70))
        lines70=r70['text_automatic'].split('\n')
        self.assertEqual(lines70[0],'rohanadenggan')
        self.assertEqual(lines70[1],'u[?]nianggi')

        r58=geometry.arrange(self.saved.document(58))
        self.assertEqual(r58['text_automatic'],'buhunianggi')

    def test_negative_guards_v051(self):
        # 1) Shared-mask Anak beda peran dengan skor seri tetap AMBIGUOUS [?]
        a=pred(1,6,[0,100,100,200],.95)
        b=pred(2,23,[30,80,70,95],.80);c=pred(3,19,[30,80,70,95],.80)
        b['segmentation']={'size':[240,200],'counts':[80*240,40*240,200*240-120*240]}
        c['segmentation']={'size':[240,200],'counts':[80*240,40*240,200*240-120*240]}
        rt=geometry.arrange(fixture(a,b,c))
        self.assertEqual(rt['text_automatic'],'[?]')
        self.assertIsNone(next(g for g in rt['sign_candidate_groups'] if g['role']=='SHARED_MASK')['selected_instance_id'])

        # 2) Contained Anak dengan skor LEBIH TINGGI dari Ina tidak boleh ditekan
        ina=pred(1,3,[0,0,100,100],.70);anak=pred(2,19,[20,10,60,30],.95)
        # Rect [0,0,100,100] & [20,10,60,30] on 100x100 canvas via pycocotools-compatible uncompressed counts:
        # Easier: vertical band [0..10] inside [0..100] contiguous in column-major RLE:
        ina['segmentation']={'size':[100,100],'counts':[0,10000]}
        anak['segmentation']={'size':[100,100],'counts':[2000,800,7200]}
        rh=geometry.arrange(fixture(ina,anak))
        self.assertEqual(rh['role_candidate_groups'],[])
        self.assertEqual(rh['text_automatic'],'ne')

        # 3a) Composite Ina tertutup Ina berskor lebih rendah tidak diserap
        low_span=pred(1,14,[0,0,100,50],.95)
        h1=pred(2,13,[0,0,45,50],.70);h2=pred(3,14,[55,0,100,50],.70)
        low_span['segmentation']={'size':[50,100],'counts':[0,5000]}
        h1['segmentation']={'size':[50,100],'counts':[0,2250,2750]}
        h2['segmentation']={'size':[50,100],'counts':[2750,2250]}
        rc=geometry.arrange(fixture(low_span,h1,h2))
        self.assertEqual(len(rc['reading_candidate_groups']),3)

        # 3b) Composite Ina tertutup < 0.80 oleh Ina berskor lebih tinggi tidak diserap
        part_span=pred(1,14,[0,0,100,50],.65)
        p1=pred(2,13,[0,0,35,50],.95);p2=pred(3,14,[65,0,100,50],.95)
        part_span['segmentation']={'size':[50,100],'counts':[0,5000]}
        p1['segmentation']={'size':[50,100],'counts':[0,1750,3250]}
        p2['segmentation']={'size':[50,100],'counts':[3250,1750]}
        rp=geometry.arrange(fixture(part_span,p1,p2))
        self.assertEqual(len(rp['reading_candidate_groups']),3)

        # 4) Vokal mandiri ina_u diikuti konsonan + vokal + pangolat tidak melakukan closed syllable reorder
        u=pred(1,18,[0,100,50,150],.99);l=pred(2,13,[65,100,115,150],.99)
        v=pred(3,21,[120,110,140,140],.99);k=pred(4,24,[145,105,160,135],.99)
        ru=geometry.arrange(fixture(u,l,v,k))
        self.assertEqual(ru['text_automatic'],'u[?]')


if __name__=='__main__':unittest.main()
