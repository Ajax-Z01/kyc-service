import hashlib

def verify_file_integrity(file_path, expected_hash):
    """
    Cek apakah file sesuai dengan hash yang diharapkan.
    """
    with open(file_path, "rb") as f:
        content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        return file_hash == expected_hash

def simple_format_check(file_path, allowed_extensions=None):
    """
    Cek ekstensi file (misal hanya pdf, png, jpg).
    """
    if allowed_extensions is None:
        allowed_extensions = ["pdf", "png", "jpg", "jpeg"]

    ext = file_path.split(".")[-1].lower()
    return ext in allowed_extensions
