"""Архив материалов для загрузки в облако, без Git и локальных данных"""
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('dockercheck', 'docs', 'examples', 'scripts', 'tests', '.github')
FILES = ('README.md', 'pyproject.toml', 'Dockerfile', '.dockerignore', '.gitignore', '.gitattributes')


def main():
    destination = ROOT/'dist'
    destination.mkdir(exist_ok=True)
    archive = destination/'dockerfile-security-checker.zip'
    files = [ROOT/name for name in FILES]
    for folder in FOLDERS:
        files.extend(path for path in (ROOT/folder).rglob('*') if path.is_file()
                     and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.bak'))
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as output:
        for path in sorted(files):
            output.write(path, 'dockerfile-security-checker/'+path.relative_to(ROOT).as_posix())
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination/'SHA256SUMS.txt').write_text(checksum+'  '+archive.name+'\n', encoding='utf-8')
    print(archive)
    print('SHA256 '+checksum)


if __name__ == '__main__':
    main()
