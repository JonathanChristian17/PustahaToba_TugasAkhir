"""Regresi kelompok mask: kasus tersimpan dan fixture negatif yang diberi label."""
import copy
import unittest
from uji_geometri import geometry,pred,fixture
import uji_kasus_minor as saved_tests


class TestMaskCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        saved_tests.TestSavedMinorCases.setUpClass();cls.saved=saved_tests.TestSavedMinorCases()

    def test_real_nya_la_groups_before_hauluan_pairing(self):
        doc=self.saved.document(118);before=copy.deepcopy(doc)
        result=geometry.arrange(doc)
        self.assertEqual(result['text_automatic'],'nyi')
        self.assertEqual(result['assignments'][0]['ina_id'],2)
        group=next(g for g in result['reading_candidate_groups'] if len(g['ina_ids'])>1)
        self.assertEqual(group['ina_ids'],[2,3]);self.assertEqual(group['selected_instance_id'],2)
        self.assertEqual(group['grouping_evidence'][0]['rule'],'SHARED_FOREGROUND_MASK')
        self.assertEqual(result['lines'][0]['units'][0]['source_instance_ids'],[1,2,3])
        self.assertEqual(doc,before)

    def test_real_same_class_pa_duplicates_group(self):
        result=geometry.arrange(self.saved.document(71))
        group=next(g for g in result['reading_candidate_groups'] if 12 in g['ina_ids'])
        self.assertEqual(group['ina_ids'],[12,15]);self.assertEqual(group['selected_instance_id'],12)

    def test_same_boxes_but_disjoint_ink_do_not_use_mask_fallback(self):
        a=pred(1,6,[0,0,10,10]);b=pred(2,3,[4,0,14,10])
        a['segmentation']={'size':[10,20],'counts':[0,10,190]}
        b['segmentation']={'size':[10,20],'counts':[100,10,90]}
        self.assertIsNone(geometry.reading_overlap(a,b))

    def test_absent_invalid_empty_and_mismatched_rle_do_not_merge(self):
        for mask in [None,{'size':[10,20],'counts':'bad'}, {'size':[10,20],'counts':[200]},
                     {'size':[5,5],'counts':[0,10,15]}]:
            a=pred(1,6,[0,0,10,10]);b=pred(2,3,[4,0,14,10])
            a['segmentation']={'size':[10,20],'counts':[0,10,190]};b['segmentation']=mask
            self.assertIsNone(geometry.reading_overlap(a,b))

    def test_mask_evidence_does_not_select_expected_class(self):
        doc=self.saved.document(118)
        doc['predictions'][1]['score']=.6;doc['predictions'][2]['score']=.99
        result=geometry.arrange(doc)
        group=next(g for g in result['reading_candidate_groups'] if len(g['ina_ids'])>1)
        self.assertEqual(group['selected_instance_id'],3)
        self.assertNotEqual(result['text_automatic'],'nyi')

    def test_mask_tie_is_still_ambiguous(self):
        doc=self.saved.document(118)
        doc['predictions'][1]['score']=doc['predictions'][2]['score']=.9
        result=geometry.arrange(doc)
        group=next(g for g in result['reading_candidate_groups'] if len(g['ina_ids'])>1)
        self.assertIsNone(group['selected_instance_id'])
        self.assertEqual(result['assignments'][0]['status'],'AMBIGUOUS')

    def test_signed_compressed_rle_matches_uncompressed_intervals(self):
        expected=geometry.mask_intervals({'size':[4,5],'counts':[0,4,2,3,1,2,8]})
        for counts in ['042OOO7',b'042OOO7']:
            self.assertEqual(geometry.mask_intervals({'size':[4,5],'counts':counts}),expected)

    def test_mask_evidence_is_pairwise_not_transitive_chain(self):
        a=pred(1,6,[0,0,10,10]);b=pred(2,3,[4,0,14,10]);c=pred(3,2,[8,0,18,10])
        for p in [a,b,c]:p['segmentation']={'size':[10,20],'counts':[0,10,190]}
        result=geometry.arrange(fixture(a,b,c))
        self.assertEqual(sorted(len(g['ina_ids']) for g in result['reading_candidate_groups']),[1,2])

    def test_web_payload_reads_nyi_but_keeps_three_detections(self):
        import sys
        sys.path.insert(0,str(saved_tests.ROOT.parent/'04_WEB_APP_BATAK_TOBA/server'))
        import api_server
        doc=self.saved.document(118)
        im=next(im for im in self.saved.meta['images'] if im['id']==118)
        doc['input_hw']=[im['height'],im['width']]
        for i,p in enumerate(doc['predictions'],1):p['display_number']=i if p['displayed'] else None
        before=copy.deepcopy(doc)
        payload=api_server.build_predict_payload(None,doc,{},include_research_exports=False)
        self.assertEqual(payload['transliteration']['text_automatic'],'nyi')
        self.assertEqual(payload['displayed_count'],3)
        self.assertEqual([p['rawClass'] for p in payload['detections']],['anak_hauluan','ina_nya','ina_la'])
        self.assertEqual(doc,before)


if __name__=='__main__':unittest.main()
