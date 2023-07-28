import zipfile
import tarfile
import tempfile
def _uncompress_zip(file_path, dest):
    zFile = zipfile.ZipFile(file_path, "r")
    for fileM in zFile.namelist():
        zFile.extract(fileM, dest)
    zFile.close()


def _compress_tar(file_path, dest):
    with tarfile.open(dest, "w:gz") as tar:
        tar.add(file_path, arcname=os.path.basename(file_path))


def _uncompress_tar(file_path, dest):
    print(f'file_path: {file_path} dest: {dest}')
    tar = tarfile.open(file_path, "r:*")

    code_files = tar.getnames()
    for code_file in code_files:
        tar.extract(code_file, dest)


def uncompress_code(file_path, dest):
    if file_path.endswith(".zip"):
        _uncompress_zip(file_path, dest)

    elif file_path.endswith(".tar") or file_path.endswith(".tar.gz"):
        _uncompress_tar(file_path, dest)
    else:
        try:
            _uncompress_zip(file_path, dest)
            return
        except Exception:
            pass

        try:
            _uncompress_tar(file_path, dest)
            return
        except Exception:
            pass

        raise Exception(f"Unsupported compression type [{file_path}]")


