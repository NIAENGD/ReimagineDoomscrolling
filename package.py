from pathlib import Path
import zipfile
import shutil

PACKAGE_NAME = 'ReimagineDoomscrolling.zip'
DIST_DIR = Path('dist')
FILES = [
    'server.py',
    'requirements.txt',
    'run_app.bat',
    'run_server.cmd',
]

EXT_DIR = Path('extension')


def build_package() -> Path:
    DIST_DIR.mkdir(exist_ok=True)
    archive_path = DIST_DIR / PACKAGE_NAME
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            path = Path(f)
            if path.exists():
                z.write(path, path.name)
        for p in EXT_DIR.rglob('*'):
            z.write(p, str(Path('extension') / p.relative_to(EXT_DIR)))
    return archive_path


if __name__ == '__main__':
    p = build_package()
    print(f'Created {p}')
