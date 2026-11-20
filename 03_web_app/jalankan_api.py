"""Peluncur API inferensi dan transliterasi (WSL .venv-web) untuk React Web App 04."""
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE / "server/api_server.py"
WSL_DISTRO = "Ubuntu-22.04"
WSL_PYTHON = "/home/jonatomic/skripsi-batak-toba/.venv-web/bin/python"


def main():
    if not SERVER.is_file():
        raise SystemExit(f"Berkas server tidak ditemukan: {SERVER}")
    if os.name == "nt":
        wsl = shutil.which("wsl.exe")
        if wsl is None:
            raise SystemExit("WSL belum tersedia pada Windows.")
        linux_script = subprocess.run(
            [wsl, "-d", WSL_DISTRO, "--exec", "wslpath", "-u", str(Path(__file__).resolve())],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return subprocess.call([wsl, "-d", WSL_DISTRO, "--exec", WSL_PYTHON, linux_script])
    if importlib.util.find_spec("torch") is None:
        raise SystemExit("Jalankan menggunakan /home/jonatomic/skripsi-batak-toba/.venv-web/bin/python.")
    os.execv(sys.executable, [sys.executable, str(SERVER)])


if __name__ == "__main__":
    raise SystemExit(main())
