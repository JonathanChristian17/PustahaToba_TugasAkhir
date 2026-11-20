"""Jalankan aplikasi Streamlit melalui environment penelitian lokal."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
APP = PACKAGE / "aplikasi/app.py"
WSL_DISTRO = "Ubuntu-22.04"
WSL_PYTHON = "/home/jonatomic/skripsi-batak-toba/.venv-web/bin/python"


def main():
    if not APP.is_file():
        raise SystemExit(f"Berkas aplikasi tidak ditemukan: {APP}")
    if os.name == "nt":
        wsl = shutil.which("wsl.exe")
        if wsl is None:
            raise SystemExit("WSL belum tersedia pada Windows.")
        linux_script = subprocess.run(
            [wsl, "-d", WSL_DISTRO, "--exec", "wslpath", "-u", str(Path(__file__).resolve())],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return subprocess.call([wsl, "-d", WSL_DISTRO, "--exec", WSL_PYTHON, linux_script])
    if importlib.util.find_spec("streamlit") is None:
        raise SystemExit("Aktifkan environment ~/skripsi-batak-toba/.venv-web terlebih dahulu.")
    os.chdir(APP.parent)
    os.execv(sys.executable, [
        sys.executable, "-m", "streamlit", "run", str(APP),
        "--server.address", "127.0.0.1", "--server.port", "8502",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
