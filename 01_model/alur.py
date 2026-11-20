"""Jalankan tahapan penelitian dari satu pintu masuk."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
PYTHON = '/home/jonatomic/skripsi-batak-toba/.venv/bin/python'
WEB_PYTHON = '/home/jonatomic/skripsi-batak-toba/.venv-web/bin/python'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def path_arg(value):
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path

def fresh_folder(group):
    name = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    return ROOT / 'hasil_tahapan' / group / name

def execute(command, dry=False):
    print('Perintah:', shlex.join([str(x) for x in command]), flush=True)
    if dry:
        print('PRATINJAU: perintah tidak dijalankan.'); return 0
    return subprocess.call([str(x) for x in command], cwd=ROOT)

def status():
    params = read(ROOT / 'pendukung/02_KONFIGURASI/eksperimen.json')
    if params['epochs'] != 30:
        raise ValueError('Konfigurasi pelatihan harus 30 epoch.')
    print('Konfigurasi: 30 epoch; penurunan LR setelah epoch 20 dan 27.')
    for depth in (50, 101):
        folder = ROOT / f'eksperimen/hasil_train_R{depth}'
        rows = read(folder / 'riwayat.json')
        best = max(rows, key=lambda r:r['validasi']['AP'])
        print(f"R{depth}: selesai epoch {max(r['epoch'] for r in rows)}/30; "
              f"terbaik epoch {best['epoch']}; AP validasi {best['validasi']['AP']:.4f}%")
    print('UI memakai R50 epoch 28 yang sudah terverifikasi. Training baru tidak mengganti model UI otomatis.')

def folder_for_existing(depth):
    return ROOT / f'eksperimen/hasil_train_R{depth}'

def train(args):
    depth = 50 if args.stage.endswith('r50') else 101
    if args.audit_only:
        return execute([PYTHON,'-B',ROOT/'latih_paket.py',fresh_folder(f'audit_R{depth}'),
                        '--backbone',str(depth),'--responden-repeat','3','--audit-only'],args.dry_run)
    out = path_arg(args.output) if args.output else (folder_for_existing(depth) if args.resume else fresh_folder(f'train_R{depth}'))
    command = [PYTHON,'-B',ROOT/'latih_paket.py',out,'--backbone',str(depth),
               '--responden-repeat','3','--stop-after-epoch','30']
    if args.resume:
        if not (out/'model_last.pth').is_file():
            raise ValueError(f'Checkpoint terakhir tidak tersedia: {out}')
        contract = read(out/'kontrak_run.json')
        if contract['pengaturan']['backbone_depth'] != depth or contract['pengaturan']['epochs'] != 30:
            raise ValueError('Backbone atau durasi kontrak tidak sesuai.')
        command += ['--resume']
        if args.check_resume:
            command += ['--check-resume']
        else:
            history = read(out/'riwayat.json')
            last = max(r['epoch'] for r in history)
            if last >= 30:
                print(f'R{depth} sudah selesai {last}/30 epoch pada {out}. Tidak ada training yang dimulai.')
                return 0
            command += ['--mulai-training']
    else:
        if args.check_resume:
            raise ValueError('--check-resume memerlukan --resume.')
        if out.exists():
            raise ValueError(f'Folder sudah ada: {out}. Gunakan --resume untuk melanjutkan, atau folder baru.')
        command += ['--mulai-training']
    return execute(command,args.dry_run)

def evaluate(args):
    depth = 50 if args.stage.endswith('r50') else 101
    run = path_arg(args.run) if args.run else folder_for_existing(depth)
    contract = read(run/'kontrak_run.json')
    if contract['pengaturan']['backbone_depth'] != depth or contract['pengaturan']['epochs'] != 30:
        raise ValueError('Kontrak backbone/durasi evaluasi tidak sesuai.')
    rows = read(run/'riwayat.json')
    if max(r['epoch'] for r in rows) != 30:
        raise ValueError('Gunakan run yang telah selesai 30 epoch untuk evaluasi final.')
    out = path_arg(args.output) if args.output else fresh_folder(f'evaluasi_R{depth}')
    if out.exists():
        raise ValueError(f'Folder hasil sudah ada: {out}. Pilih folder baru.')
    if not args.dry_run:
        out.parent.mkdir(parents=True,exist_ok=True)
    return execute([PYTHON,'-B',ROOT/'evaluasi_paket.py',out,'--run',run],args.dry_run)

def open_path(path,dry):
    if not path.exists():raise ValueError(f'Tidak ditemukan: {path}')
    if dry:print('Buka:',path);return 0
    explorer = Path('/mnt/c/Windows/explorer.exe')
    winpath=subprocess.check_output(['wslpath','-w',str(path)],text=True).strip()
    subprocess.Popen([str(explorer),winpath],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return 0

def dispatch(args):
    if args.stage=='status':status();return 0
    if args.stage.startswith('train-'):return train(args)
    if args.stage.startswith('eval-'):return evaluate(args)
    if args.stage=='audit':
        for depth in (50,101):
            result=execute([PYTHON,'-B',ROOT/'latih_paket.py',fresh_folder(f'audit_R{depth}'),
                            '--backbone',str(depth),'--responden-repeat','3','--audit-only'],args.dry_run)
            if result:return result
        return 0
    if args.stage=='praproses':
        out=path_arg(args.output) if args.output else fresh_folder('praproses')
        if out.exists():raise ValueError('Pilih folder pratinjau baru.')
        return execute([PYTHON,'-B',ROOT/'tinjau_praproses.py','--output',out],args.dry_run)
    if args.stage=='ui':return execute([WEB_PYTHON,ROOT/'jalankan.py'],args.dry_run)
    if args.stage=='bukti':
        return open_path(ROOT.parents[1]/'SEMHAS/UJI_PROGRAM_EKSPERIMEN_2/BUKTI_VALIDASI.html',args.dry_run)
    if args.stage=='kode':
        path=ROOT/'BUKA_KODE.cmd'
        if args.dry_run:print('Buka kode dengan:',path);return 0
        winpath=subprocess.check_output(['wslpath','-w',str(path)],text=True).strip()
        return subprocess.call(['/mnt/c/Windows/System32/cmd.exe','/c',winpath])

def menu(parser):
    stages={'1':'status','2':'audit','3':'praproses','4':'train-r50','5':'train-r101',
            '6':'eval-r50','7':'eval-r101','8':'ui','9':'bukti','10':'kode'}
    while True:
        print('\nALUR AKSARABATAKTOBA - 30 EPOCH\n'
              '1 Status hasil yang sudah selesai\n2 Audit data/konfigurasi (tanpa training)\n'
              '3 Pratinjau resize, normalisasi, augmentasi\n'
              '4 MULAI TRAINING BARU R50 30 epoch\n5 MULAI TRAINING BARU R101 30 epoch\n'
              '6 Evaluasi ulang R50 tersimpan ke folder baru\n7 Evaluasi ulang R101 tersimpan ke folder baru\n'
              '8 Buka aplikasi (terminal tetap terbuka)\n9 Buka bukti validasi\n10 Buka folder kode\n0 Keluar')
        choice=input('Pilih tahap: ').strip()
        if choice=='0':return 0
        if choice not in stages:print('Pilihan tidak tersedia.');continue
        try:
            code=dispatch(parser.parse_args([stages[choice]]))
            if code:print(f'Tahap berakhir dengan kode {code}.')
        except (ValueError,OSError,KeyError) as e:print('Tahap tidak dijalankan:',e)
        except KeyboardInterrupt:print('\nTahap dihentikan. Periksa checkpoint sebelum melanjutkan.')

def main():
    if os.name=='nt':
        args=sys.argv[1:]
        for i,a in enumerate(args[:-1]):
            if a in ('--output','--run') and Path(args[i+1]).is_absolute():
                args[i+1]=subprocess.check_output(['wsl.exe','-d','Ubuntu-22.04','--exec','wslpath','-u',args[i+1]],text=True).strip()
        script=subprocess.check_output(['wsl.exe','-d','Ubuntu-22.04','--exec','wslpath','-u',str(Path(__file__).resolve())],text=True).strip()
        return subprocess.call(['wsl.exe','-d','Ubuntu-22.04','--exec',PYTHON,'-B',script,*args])
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='stage')
    for name in ['status','audit','praproses','ui','bukti','kode','train-r50','train-r101','eval-r50','eval-r101']:
        cmd=sub.add_parser(name);cmd.add_argument('--dry-run',action='store_true',help='Tampilkan perintah tanpa menjalankannya')
        if name=='praproses' or name.startswith(('train-','eval-')):cmd.add_argument('--output',help='Folder keluaran, absolut atau relatif terhadap paket')
        if name.startswith('train-'):
            cmd.add_argument('--resume',action='store_true');cmd.add_argument('--check-resume',action='store_true');cmd.add_argument('--audit-only',action='store_true')
        if name.startswith('eval-'):cmd.add_argument('--run',help='Folder training yang akan dievaluasi')
    args=parser.parse_args()
    if args.stage is None:return menu(parser)
    return dispatch(args)

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError) as error:print('Tidak dijalankan:',error,file=sys.stderr);raise SystemExit(2)
