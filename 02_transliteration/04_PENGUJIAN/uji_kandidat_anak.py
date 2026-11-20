"""Regresi tanda bersaing untuk bacaan; fixture bukan citra penelitian."""
import copy
import unittest
from uji_geometri import geometry,pred,fixture
import uji_kasus_minor as saved_tests


class TestSignReadingCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        saved_tests.TestSavedMinorCases.setUpClass();cls.saved=saved_tests.TestSavedMinorCases()

    def vowel_conflict(self,score_i=.95,score_e=.6):
        return fixture(pred(1,6,[0,100,100,200]),pred(2,20,[105,160,115,175],score_i),
                       pred(3,19,[0,80,20,90],score_e))

    def test_real_aek_cases_and_preserved_ids(self):
        for image_id in [60,125]:
            doc=self.saved.document(image_id);before=copy.deepcopy(doc)
            result=geometry.arrange(doc,lexicon=self.saved.lex)
            self.assertEqual(result['text_automatic'],'aeknatio')
            if image_id==125:
                group=result['sign_candidate_groups'][0]
                self.assertEqual(next(a['class_label'] for a in group['alternatives'] if a['instance_id']==group['selected_instance_id']),'anak_sihora')
            else:
                role_group=result['role_candidate_groups'][0]
                self.assertEqual(role_group['instance_ids'],[9,11])
                self.assertEqual(role_group['selected_instance_id'],9)
                self.assertEqual(role_group['grouping_evidence'][0]['rule'],'CONTAINED_ANAK_IN_INA_MASK')
            claimed=[i for line in result['lines'] for u in line['units'] for i in u['source_instance_ids']]
            claimed += [i for a in result['assignments'] if a['ina_id'] is None for i in a['source_instance_ids']]
            self.assertEqual(sorted(claimed),sorted(p['instance_id'] for p in doc['predictions'] if p['displayed']))
            self.assertEqual(doc,before)
            self.assertEqual(result['word_spacing']['status'],'NEEDS_REVIEW')

    def test_competing_vowels_choose_confidence_not_fixed_vowel(self):
        for scores,expected in [((.95,.6),'bi'),((.6,.95),'be')]:
            result=geometry.arrange(self.vowel_conflict(*scores))
            self.assertEqual(result['text_automatic'],expected)
            self.assertEqual(result['lines'][0]['units'][0]['source_instance_ids'],[1,2,3])
            self.assertIn(False,[a.get('reading_selected') for a in result['assignments']])

    def test_tie_keeps_uncertainty_instead_of_inventing_a_vowel(self):
        result=geometry.arrange(self.vowel_conflict(.9,.9))
        self.assertIsNone(result['sign_candidate_groups'][0]['selected_instance_id'])
        self.assertEqual(result['text_automatic'],'[?]')

    def test_vowel_plus_ng_are_not_competing(self):
        doc=self.vowel_conflict();doc['predictions']=doc['predictions'][:2]+[pred(4,23,[80,80,100,90])]
        result=geometry.arrange(doc)
        self.assertEqual(result['text_automatic'],'bing')
        self.assertEqual(result['sign_candidate_groups'],[])

    def test_same_mark_duplicates_remain_in_provenance(self):
        doc=self.vowel_conflict();doc['predictions'][2].update(category_id=20,class_label='anak_hauluan',bbox_xyxy=[105,160,115,175])
        result=geometry.arrange(doc)
        self.assertEqual(result['text_automatic'],'bi')
        self.assertEqual(result['lines'][0]['units'][0]['source_instance_ids'],[1,2,3])

    def test_vowel_and_killer_not_silently_reduced_to_one(self):
        doc=self.vowel_conflict();doc['predictions']=doc['predictions'][:2]+[pred(4,24,[110,170,125,190])]
        result=geometry.arrange(doc)
        self.assertEqual(result['text_automatic'],'[?]')
        self.assertEqual(result['sign_candidate_groups'],[])

    def test_selection_is_input_order_independent(self):
        doc=self.vowel_conflict();before=geometry.arrange(doc);doc['predictions'].reverse()
        after=geometry.arrange(doc)
        for key in ['text_automatic','lines','assignments','sign_candidate_groups']:
            self.assertEqual(after[key],before[key])

    def test_web_payload_preserves_extra_mark_and_reads_aeknatio(self):
        import sys
        sys.path.insert(0,str(saved_tests.ROOT.parent/'04_WEB_APP_BATAK_TOBA/server'))
        import api_server
        doc=self.saved.document(125);im=next(im for im in self.saved.meta['images'] if im['id']==125)
        doc['input_hw']=[im['height'],im['width']]
        number=0
        for p in doc['predictions']:
            if p['displayed']:number+=1;p['display_number']=number
        before=copy.deepcopy(doc)
        payload=api_server.build_predict_payload(None,doc,{},include_research_exports=False)
        self.assertEqual(payload['transliteration']['text_automatic'],'aeknatio')
        self.assertEqual(payload['displayed_count'],number)
        self.assertTrue(any(p['instance_id']==12 and p['rawClass']=='anak_hatadingan' for p in payload['detections']))
        self.assertEqual(doc,before)


if __name__=='__main__':unittest.main()
