"""Aturan pembacaan unit aksara dengan pasangan tanda yang sudah ditentukan.

Tahap ini belum menentukan pasangan atau urutan baca dari koordinat gambar.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "01_ATURAN/peta_aksara.json"


def suggest_spaces(text: str, words: set[str], allowed_boundaries=None) -> dict:
    """Usulkan spasi hanya untuk pembagian tunggal; huruf tidak diubah."""
    if any(not isinstance(w,str) or re.fullmatch(r"[a-z]+",w) is None for w in words):
        raise ValueError("Kosakata harus berisi kata huruf kecil a-z tanpa spasi.")
    lengths=sorted({len(w) for w in words})
    parts=[];output=[];offset=0
    for chunk in re.split(r"(\s+)",text):
        if not chunk:continue
        if chunk.isspace():
            output.append(chunk);offset+=len(chunk);continue
        status="UNSUPPORTED_OR_AMBIGUOUS_INPUT";candidates=[]
        if re.fullmatch(r"[A-Za-z]+",chunk):
            paths={len(chunk):[[]]}
            for start in range(len(chunk)-1,-1,-1):
                choices=[]
                for length in lengths:
                    end=start+length
                    if end>len(chunk):break
                    if allowed_boundaries is not None and offset+end not in allowed_boundaries:continue
                    if chunk[start:end].lower() in words:
                        for tail in paths.get(end,[]):
                            choices.append([chunk[start:end]]+tail)
                            if len(choices)==2:break
                    if len(choices)==2:break
                if choices:paths[start]=choices
            candidates=[" ".join(path) for path in paths.get(0,[])]
            status="UNIQUE" if len(candidates)==1 else ("AMBIGUOUS" if candidates else "UNKNOWN")
        proposed=candidates[0] if status=="UNIQUE" else chunk
        output.append(proposed)
        parts.append({"start":offset,"end":offset+len(chunk),"original":chunk,
                      "suggestion":proposed,"status":status,"candidates_at_most_two":candidates})
        offset+=len(chunk)
    suggestion="".join(output)
    assert suggestion.replace(" ","")==text.replace(" ","")
    pending=any(part["status"]!="UNIQUE" for part in parts)
    return {"original_text":text,"suggested_text":suggestion,
            "status":"NEEDS_REVIEW" if pending else ("SUGGESTED" if suggestion!=text else "UNCHANGED"),
            "method":"EXACT_LEXICON_SEGMENTATION; UNIQUE_ONLY; candidate paths capped at two",
            "confidence":None,"parts":parts}


@dataclass(frozen=True)
class Reading:
    text: str
    status: str
    source_labels: tuple[str, ...]
    rules: tuple[str, ...]
    warnings: tuple[str, ...] = ()


class Transliterator:
    """Pembacaan ortografis; ejaan dan batas kata tidak ditebak dari kosakata."""

    def __init__(self, rules_path: Path = RULES_PATH):
        self.document = json.loads(Path(rules_path).read_text(encoding="utf-8"))
        if self.document.get("language") != "batak_toba":
            raise ValueError("Modul ini hanya menggunakan aturan Batak Toba.")
        self.version = self.document["version"]
        entries = self.document["classes"]
        if len(entries) != 25 or {e["id"] for e in entries} != set(range(25)):
            raise ValueError("Peta aturan harus memuat tepat 25 ID kelas 0-24.")
        self.classes = {entry["name"]: entry for entry in entries}
        if len(self.classes) != 25:
            raise ValueError("Nama kelas tidak boleh berulang.")

    def _entry(self, name: str, kinds: set[str]) -> dict:
        if name not in self.classes:
            raise ValueError(f"Kelas tidak dikenal: {name}")
        entry = self.classes[name]
        if entry["kind"] not in kinds:
            raise ValueError(f"Peran kelas tidak sesuai: {name}")
        return entry

    def read_unit(
        self,
        ina: str,
        anak: Iterable[str] = (),
        *,
        coda: str | None = None,
        coda_marks: Iterable[str] = (),
    ) -> Reading:
        """Baca unit dalam urutan logis, termasuk konsonan penutup berpangolat.

        `anak` sudah dipasangkan secara logis kepada `ina`. Penempatan visual
        tanda vokal pada konsonan akhir harus diselesaikan tahap geometri.
        """
        if isinstance(anak, str) or isinstance(coda_marks, str):
            raise ValueError("Daftar tanda harus berupa urutan label, bukan satu string.")
        marks, closing_marks = tuple(anak), tuple(coda_marks)
        base = self._entry(ina, {"consonant", "independent_vowel"})
        mark_entries = [self._entry(m, {"vowel_sign", "final_ng", "killer"}) for m in marks]
        closing = self._entry(coda, {"consonant"}) if coda is not None else None
        for name in closing_marks:
            self._entry(name, {"vowel_sign", "final_ng", "killer"})
        if closing is None and closing_marks:
            raise ValueError("Tanda penutup diberikan tanpa konsonan penutup.")
        labels = (ina,) + marks + ((coda,) if coda is not None else ()) + closing_marks

        def uncertain(reason: str) -> Reading:
            return Reading("[?]", "AMBIGUOUS", labels, (), (reason,))

        if len(marks) != len(set(marks)) or len(closing_marks) != len(set(closing_marks)):
            return uncertain("Tanda berulang memerlukan pemeriksaan instansi.")
        vowels = [e for e in mark_entries if e["kind"] == "vowel_sign"]
        final_ng = any(e["kind"] == "final_ng" for e in mark_entries)
        killer = any(e["kind"] == "killer" for e in mark_entries)
        if len(vowels) > 1:
            return uncertain("Lebih dari satu tanda vokal pada satu unit.")
        if killer and (vowels or final_ng or closing is not None):
            return uncertain("Pangolat dan tanda lain perlu pemisahan kelompok suku kata.")
        if closing is not None and (final_ng or closing_marks != ("anak_pangolat",)):
            return uncertain("Konsonan penutup memerlukan satu pangolat dan tidak bersamaan dengan ng akhir.")
        if base["kind"] == "independent_vowel" and (killer or (vowels and ina != "ina_a")):
            return uncertain("Kombinasi tanda pada vokal mandiri belum didukung aturan ini.")

        trace, warnings = [], []
        if killer:
            text = "k" if ina == "ina_ha" else base["onset"]
            trace.append("KILL_INHERENT_A")
            if ina == "ina_ha":
                trace.append("TOBA_HA_AS_FINAL_K")
        elif vowels:
            prefix = base.get("onset", "")
            text = prefix + vowels[0]["vowel"]
            trace.append("A_CARRIER_VOWEL" if ina == "ina_a" else "REPLACE_INHERENT_A")
        else:
            text = base["latin"]
            trace.append("BASE_VALUE")
        if ina == "ina_ha" and not killer:
            trace.append("TOBA_HA_ONSET_H")
        if final_ng:
            text += "ng"
            trace.append("APPEND_FINAL_NG")
        if closing is not None:
            text += "k" if coda == "ina_ha" else closing["onset"]
            trace.append("CLOSED_SYLLABLE_LOGICAL_ORDER")
            if coda == "ina_ha":
                trace.append("TOBA_HA_AS_FINAL_K")
        if ina in {"ina_wa", "ina_ya"}:
            warnings.append("Wa/Ya dipertahankan pada unit harfiah; normalisasi memerlukan konteks antarsuku kata.")
        return Reading(text, "REVIEW" if warnings else "RULE_APPLIED", labels, tuple(trace), tuple(warnings))


def demonstration(engine: Transliterator) -> dict:
    """Fixture perangkat lunak yang bukan hasil pengenalan citra."""
    examples = [
        ("ba", {"ina": "ina_ba"}),
        ("bi", {"ina": "ina_ba", "anak": ["anak_hauluan"]}),
        ("bu", {"ina": "ina_ba", "anak": ["anak_haborotan"]}),
        ("bang", {"ina": "ina_ba", "anak": ["anak_haminsaran"]}),
        ("bing", {"ina": "ina_ba", "anak": ["anak_hauluan", "anak_haminsaran"]}),
        ("b", {"ina": "ina_ba", "anak": ["anak_pangolat"]}),
        ("tip", {"ina": "ina_ta", "anak": ["anak_hauluan"], "coda": "ina_pa", "coda_marks": ["anak_pangolat"]}),
        ("konflik", {"ina": "ina_ba", "anak": ["anak_hauluan", "anak_sihora"]}),
    ]
    return {
        "kind": "SOFTWARE_FIXTURE_NOT_IMAGE_INFERENCE",
        "rules_version": engine.version,
        "pairing": "MANUALLY_SPECIFIED_LOGICAL_GROUPS",
        "examples": [{"name": name, "input": data, "reading": asdict(engine.read_unit(**data))}
                     for name, data in examples],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contoh", action="store_true", help="Tampilkan fixture aturan, tanpa memuat model.")
    args = parser.parse_args()
    if not args.contoh:
        parser.print_help()
        return
    print(json.dumps(demonstration(Transliterator()), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
