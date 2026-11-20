"""Kosakata buatan untuk pengujian kode; bukan acuan atau kamus penelitian."""
import copy
import unittest
from uji_geometri import fixture,pred,geometry
from transliterasi import suggest_spaces


class TestSpacing(unittest.TestCase):
    def test_unique_and_case_preserved(self):
        self.assertEqual(suggest_spaces('Abcd',{'ab','cd'})['suggested_text'],'Ab cd')

    def test_no_space_inside_a_reading_unit(self):
        r=suggest_spaces('anggi',{'an','ggi'},allowed_boundaries={3,5})
        self.assertEqual(r['suggested_text'],'anggi')
        self.assertEqual(r['parts'][0]['status'],'UNKNOWN')

    def test_ambiguous_is_not_chosen(self):
        r=suggest_spaces('abcd',{'ab','cd','abcd'})
        self.assertEqual(r['suggested_text'],'abcd')
        self.assertEqual(r['parts'][0]['status'],'AMBIGUOUS')

    def test_unknown_does_not_fill_or_replace_letters(self):
        r=suggest_spaces('ina',{'inang'})
        self.assertEqual(r['suggested_text'],'ina')
        self.assertEqual(r['parts'][0]['status'],'UNKNOWN')

    def test_markers_and_punctuation_are_preserved(self):
        text='ab[?]cd\nabc/d, [ja / i]'
        self.assertEqual(suggest_spaces(text,{'ab','cd'})['suggested_text'],text)

    def test_existing_whitespace_is_preserved(self):
        r=suggest_spaces('abcd\n\t  efgh',{'ab','cd','ef','gh'})
        self.assertEqual(r['suggested_text'],'ab cd\n\t  ef gh')

    def test_candidate_count_is_bounded(self):
        r=suggest_spaces('a'*200,{'a','aa','aaa'})
        self.assertEqual(len(r['parts'][0]['candidates_at_most_two']),2)
        self.assertEqual(r['suggested_text'],'a'*200)

    def test_invalid_words_are_rejected(self):
        for words in [{'ab cd'},{''},{'AB'},{'ß'}]:
            with self.assertRaises(ValueError):suggest_spaces('abcd',words)

    def test_geometry_opt_in_preserves_original_output_and_predictions(self):
        d=fixture(pred(1,6,[0,100,100,200]),pred(2,6,[300,100,400,200]))
        before=copy.deepcopy(d);original=geometry.arrange(d)
        lex={'language':'batak_toba','source':'SOFTWARE_FIXTURE_NOT_REAL_DICTIONARY',
             'license':'test-only','revision':'fixture1','words':['ba']}
        result=geometry.arrange(d,lexicon=lex)
        self.assertEqual(result['word_spacing']['suggested_text'],'ba ba')
        self.assertEqual(result['text_automatic'],'baba')
        result.pop('word_spacing')
        self.assertEqual(result['presentation']['spacing_suggestion'],'ba ba')
        result.pop('presentation');original.pop('presentation')
        self.assertEqual(result,original);self.assertEqual(d,before)

    def test_other_language_or_missing_provenance_rejected(self):
        for lex in [{'language':'karo','words':['a']},{'language':'batak_toba','words':['a']}]:
            with self.assertRaises(ValueError):geometry.arrange(fixture(),lexicon=lex)

    def test_no_lexicon_no_spacing_field(self):
        self.assertNotIn('word_spacing',geometry.arrange(fixture()))

    def test_overlap_candidates_hold_spacing_without_changing_reading(self):
        d=fixture(pred(1,6,[0,100,100,200],.9),pred(2,3,[0,100,100,200],.6),
                  pred(3,6,[300,100,400,200]))
        lex={'language':'batak_toba','source':'SOFTWARE_FIXTURE','license':'test-only',
             'revision':'fixture1','words':['ba']}
        r=geometry.arrange(d,lexicon=lex)
        self.assertEqual(r['text_automatic'],'baba')
        self.assertEqual(r['word_spacing']['suggested_text'],'baba')
        self.assertEqual(r['word_spacing']['status'],'NEEDS_REVIEW')
        self.assertIn('READING_HAS_RECORDED_ISSUES',r['word_spacing']['review_reasons'])
        self.assertEqual(r['word_spacing']['parts'][0]['candidates_at_most_two'],['ba ba'])

    def test_even_unique_spacing_requires_language_review(self):
        d=fixture(pred(1,6,[0,100,100,200]),pred(2,6,[300,100,400,200]))
        lex={'language':'batak_toba','source':'SOFTWARE_FIXTURE','license':'test-only',
             'revision':'fixture1','words':['ba']}
        r=geometry.arrange(d,lexicon=lex)
        self.assertEqual(r['word_spacing']['suggested_text'],'ba ba')
        self.assertTrue(r['word_spacing']['review_required'])


if __name__=='__main__':unittest.main()
