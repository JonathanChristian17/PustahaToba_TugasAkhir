"""Regresi atas prediksi penelitian tersimpan; bukan evaluasi akurasi baru."""
import copy
import json
from pathlib import Path
import unittest
from uji_geometri import geometry
from uji_testing_tersimpan import adapt_predictions

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT.parent / '02_AKSARABATAKTOBA_TERBARU'


class TestSavedMinorCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta=json.loads((PACKAGE/'eksperimen/DATASET/testing/instances.json').read_text(encoding='utf-8'))
        cls.predictions=json.loads((PACKAGE/'eksperimen/hasil_evaluasi_R50_30epoch/predictions.json').read_text(encoding='utf-8'))
        cls.names={c['id']:c['name'] for c in cls.meta['categories']}
        cls.lex=json.loads((ROOT/'01_ATURAN/KOSAKATA_EKSTERNAL/kosakata_toba_v2.json').read_text(encoding='utf-8'))

    def document(self,image_id):
        return {'checkpoint_sha256':geometry.CHECKPOINT_HASH,'display_threshold':.5,
                'predictions':adapt_predictions([(i,p) for i,p in enumerate(self.predictions)
                                                if p['image_id']==image_id],self.names)}

    def test_jabuob_keeps_winning_class_and_holds_spacing(self):
        doc=self.document(31);before=copy.deepcopy(doc)
        result=geometry.arrange(doc,lexicon=self.lex)
        self.assertEqual(result['text_automatic'],'jabuob')
        self.assertEqual(result['word_spacing']['status'],'NEEDS_REVIEW')
        groups=[g for g in result['reading_candidate_groups'] if len(g['ina_ids'])>1]
        self.assertTrue(groups)
        for group in groups:
            selected=next(p for p in doc['predictions'] if p['instance_id']==group['selected_instance_id'])
            self.assertEqual(selected['score'],max(a['score'] for a in group['alternatives']))
        self.assertEqual(doc,before)

    def test_missing_u_not_filled_from_reference(self):
        result=geometry.arrange(self.document(49),lexicon=self.lex)
        self.assertEqual(result['text_automatic'],'aeknihata')
        self.assertEqual(result['word_spacing']['suggested_text'],'aek ni hata')
        self.assertTrue(result['word_spacing']['review_required'])

    def test_wrong_class_not_corrected_by_lexicon(self):
        result=geometry.arrange(self.document(51),lexicon=self.lex)
        self.assertEqual(result['text_automatic'],'porlakninanang')
        self.assertEqual(result['word_spacing']['suggested_text'],'porlak ni na nang')
        self.assertTrue(result['word_spacing']['review_required'])

    def test_ha_onset_not_replaced_with_k_in_real_case(self):
        result=geometry.arrange(self.document(94))
        self.assertEqual(result['text_automatic'],'buhunianggi')
        self.assertTrue(any('TOBA_HA_ONSET_H' in u['reading']['rules']
                            for line in result['lines'] for u in line['units']))

    def test_corrected_copy_reads_ja_without_changing_active_data(self):
        doc=json.loads((ROOT/'05_HASIL/KOREKSI_P10_N23_V1/inferensi_koreksi/predictions.json').read_text(encoding='utf-8'))
        before=copy.deepcopy(doc)
        result=geometry.arrange(doc,lexicon=self.lex)
        self.assertEqual(result['text_automatic'],'ulosdijabu')
        self.assertEqual(doc,before)


if __name__=='__main__':unittest.main()
