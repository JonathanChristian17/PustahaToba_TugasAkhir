"""Contoh buatan untuk menguji hitungan CER, bukan hasil penelitian."""
from functools import lru_cache
from itertools import product
import unittest
from evaluasi_cer import character_errors,aggregate,normalize


class TestCER(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(character_errors('inang','inang')['cer'],0)

    def test_deletion(self):
        r=character_errors('inang','ina')
        self.assertEqual((r['D'],r['S'],r['I'],r['N']),(2,0,0,5))
        self.assertEqual(r['cer'],.4)

    def test_insertion_and_unbounded_rate(self):
        r=character_errors('a','aaaa')
        self.assertEqual(r['I'],3);self.assertEqual(r['cer'],3)

    def test_substitution(self):
        r=character_errors('huta','hata')
        self.assertEqual((r['S'],r['D'],r['I']),(1,0,0))

    def test_empty_prediction_and_reference(self):
        self.assertEqual(character_errors('abc','')['D'],3)
        with self.assertRaises(ValueError):character_errors('','abc')

    def test_micro_aggregation(self):
        r=aggregate([character_errors('a','b'),character_errors('abcdefghi','abcdefghi')])
        self.assertEqual(r['cer'],.1)

    def test_markers_are_not_removed(self):
        self.assertEqual(normalize(' A[?]\nB '),'a[?]b')
        self.assertEqual(normalize(' A\t B\nC ',True),'a b c')

    def test_alignment_against_independent_recursive_distance(self):
        @lru_cache(None)
        def distance(a,b):
            if not a:return len(b)
            if not b:return len(a)
            return min(distance(a[1:],b)+1,distance(a,b[1:])+1,distance(a[1:],b[1:])+(a[0]!=b[0]))
        strings=[''.join(p) for n in range(4) for p in product('ab',repeat=n)]
        for a in strings[1:]:
            for b in strings:
                r=character_errors(a,b)
                self.assertEqual(r['errors'],distance(a,b))
                self.assertEqual(''.join(o['ref'] for o in r['alignment']),a)
                self.assertEqual(''.join(o['hyp'] for o in r['alignment']),b)


if __name__=='__main__':unittest.main()
