"""Jalankan evaluator asli dengan dependensi lokal paket."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"eksperimen"))
import evaluasi_Aksarabataktoba as evaluator
evaluator.PREVIOUS=ROOT/"pendukung"
if __name__=="__main__":evaluator.main()
