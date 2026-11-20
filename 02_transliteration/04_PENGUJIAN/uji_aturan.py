"""Uji perangkat lunak aturan; fixture tidak mewakili evaluasi citra penelitian."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("batak_transliterasi_rules", ROOT / "02_MODUL_TRANSLITERASI/transliterasi.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class TestReadingRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = module.Transliterator()

    def read(self, ina, anak=(), **kwargs):
        return self.reader.read_unit(ina, anak, **kwargs)

    def test_mapping_matches_research_class_ids(self):
        actual = json.loads((ROOT.parent / "02_AKSARABATAKTOBA_TERBARU/model/class_map.json").read_text())
        self.assertEqual({r["id"]: r["name"] for r in actual},
                         {r["id"]: r["name"] for r in self.reader.classes.values()})

    def test_19_base_values_include_independent_vowels(self):
        expected = "a ha ma na ra ta ba pa wa ga ja da nga la sa ya nya i u".split()
        for value in expected:
            with self.subTest(value=value):
                self.assertEqual(self.read("ina_" + value).text, value)

    def test_four_vowel_changes(self):
        for mark, text in [("hatadingan", "be"), ("hauluan", "bi"), ("sihora", "bo"), ("haborotan", "bu")]:
            with self.subTest(mark=mark):
                self.assertEqual(self.read("ina_ba", ["anak_" + mark]).text, text)

    def test_ng_retains_vowel(self):
        self.assertEqual(self.read("ina_ba", ["anak_haminsaran"]).text, "bang")

    def test_ng_combines_with_four_vowels(self):
        for mark, text in [("hatadingan", "beng"), ("hauluan", "bing"), ("sihora", "bong"), ("haborotan", "bung")]:
            with self.subTest(mark=mark):
                self.assertEqual(self.read("ina_ba", ["anak_" + mark, "anak_haminsaran"]).text, text)

    def test_mark_list_order_does_not_change_vowel_ng(self):
        self.assertEqual(self.read("ina_ba", ["anak_haminsaran", "anak_hauluan"]).text, "bing")

    def test_killer_retains_multiletter_consonants(self):
        self.assertEqual(self.read("ina_nga", ["anak_pangolat"]).text, "ng")
        self.assertEqual(self.read("ina_nya", ["anak_pangolat"]).text, "ny")

    def test_a_is_vowel_carrier(self):
        self.assertEqual(self.read("ina_a", ["anak_hatadingan"]).text, "e")
        self.assertEqual(self.read("ina_a", ["anak_sihora"]).text, "o")

    def test_no_silent_killing_of_independent_vowel(self):
        for ina in ["ina_a", "ina_i", "ina_u"]:
            self.assertEqual(self.read(ina, ["anak_pangolat"]).status, "AMBIGUOUS")

    def test_tip_logical_group_not_nearest_visual_attachment(self):
        result = self.read("ina_ta", ["anak_hauluan"], coda="ina_pa", coda_marks=["anak_pangolat"])
        self.assertEqual(result.text, "tip")
        self.assertIn("CLOSED_SYLLABLE_LOGICAL_ORDER", result.rules)

    def test_closed_vowel_visual_group_requires_resolution(self):
        result = self.read("ina_pa", ["anak_hauluan", "anak_pangolat"])
        self.assertEqual(result.status, "AMBIGUOUS")

    def test_multiple_vowels_are_not_forced_into_one_reading(self):
        self.assertEqual(self.read("ina_ba", ["anak_sihora", "anak_hauluan"]).text, "[?]")

    def test_duplicate_mark_is_reported(self):
        self.assertEqual(self.read("ina_ba", ["anak_haminsaran"] * 2).status, "AMBIGUOUS")

    def test_coda_needs_killer(self):
        self.assertEqual(self.read("ina_ta", coda="ina_pa").status, "AMBIGUOUS")

    def test_ng_and_explicit_coda_not_both_added(self):
        self.assertEqual(self.read("ina_ta", ["anak_haminsaran"], coda="ina_pa", coda_marks=["anak_pangolat"]).status, "AMBIGUOUS")

    def test_ha_is_k_only_when_closed_by_pangolat(self):
        result = self.read("ina_ha", ["anak_pangolat"])
        self.assertEqual(result.text, "k")
        self.assertEqual(result.status, "RULE_APPLIED")
        self.assertIn("TOBA_HA_AS_FINAL_K",result.rules)
        self.assertEqual(self.read("ina_ha").text,"ha")
        self.assertEqual(self.read("ina_ha",["anak_haborotan"]).text,"hu")

    def test_closed_vowel_carrier_before_ha(self):
        self.assertEqual(self.read("ina_a",["anak_hatadingan"],coda="ina_ha",coda_marks=["anak_pangolat"]).text,"ek")

    def test_toba_ha_onset_with_each_vowel_stays_h(self):
        for signs,expected in [([],"ha"),(["anak_hauluan"],"hi"),(["anak_haborotan"],"hu"),
                               (["anak_hatadingan"],"he"),(["anak_sihora"],"ho")]:
            result=self.read("ina_ha",signs)
            self.assertEqual(result.text,expected)
            self.assertIn("TOBA_HA_ONSET_H",result.rules)

    def test_ahu_huta_roha_and_halak_follow_toba_syllables(self):
        self.assertEqual(self.read('ina_a').text+self.read('ina_ha',['anak_haborotan']).text,'ahu')
        self.assertEqual(self.read('ina_ha',['anak_haborotan']).text+self.read('ina_ta').text,'huta')
        self.assertEqual(self.read('ina_ra',['anak_sihora']).text+self.read('ina_ha').text,'roha')
        self.assertEqual(self.read('ina_ha').text+self.read('ina_la',coda='ina_ha',coda_marks=['anak_pangolat']).text,'halak')

    def test_other_language_policy_is_rejected(self):
        document=copy.deepcopy(self.reader.document);document['language']='karo'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'rules.json';path.write_text(json.dumps(document),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Batak Toba'):module.Transliterator(path)

    def test_closed_syllables_other_than_carrier(self):
        for vowel,expected in [("hatadingan","bek"),("hauluan","bik"),("sihora","bok"),("haborotan","buk")]:
            self.assertEqual(self.read("ina_ba",["anak_"+vowel],coda="ina_ha",coda_marks=["anak_pangolat"]).text,expected)

    def test_ulos_and_porlak_logical_units(self):
        ulos=self.read("ina_u").text+self.read("ina_la",["anak_sihora"],coda="ina_sa",coda_marks=["anak_pangolat"]).text
        porlak=self.read("ina_pa",["anak_sihora"],coda="ina_ra",coda_marks=["anak_pangolat"]).text+self.read("ina_la",coda="ina_ha",coda_marks=["anak_pangolat"]).text
        self.assertEqual(ulos,"ulos")
        self.assertEqual(porlak,"porlak")

    def test_wa_ya_not_removed(self):
        for ina in ["ina_wa", "ina_ya"]:
            result = self.read(ina)
            self.assertEqual(result.status, "REVIEW")
            self.assertEqual(result.text, ina[4:])

    def test_invalid_roles_and_unknown_labels(self):
        for ina, marks in [("ina_ka", []), ("anak_hauluan", []), ("ina_ba", ["ina_i"])]:
            with self.subTest(ina=ina, marks=marks), self.assertRaises(ValueError):
                self.read(ina, marks)

    def test_mark_string_rejected(self):
        with self.assertRaises(ValueError):
            self.read("ina_ba", "anak_hauluan")

    def test_input_not_mutated_and_provenance_retained(self):
        marks = ["anak_hauluan", "anak_haminsaran"]
        original = copy.deepcopy(marks)
        result = self.read("ina_ba", marks)
        self.assertEqual(marks, original)
        self.assertEqual(result.source_labels, ("ina_ba", *marks))

    def test_fixture_is_explicitly_labeled(self):
        result = module.demonstration(self.reader)
        self.assertEqual(result["kind"], "SOFTWARE_FIXTURE_NOT_IMAGE_INFERENCE")
        self.assertEqual(result["pairing"], "MANUALLY_SPECIFIED_LOGICAL_GROUPS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
