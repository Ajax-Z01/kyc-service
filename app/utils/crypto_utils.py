from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def encrypt_file(file_path: str) -> tuple[str, bytes]:
    key = os.urandom(32)  # 256-bit key
    iv = os.urandom(16)

    encrypted_path = f"{file_path}.enc"
    backend = default_backend()

    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=backend)
    encryptor = cipher.encryptor()

    with open(file_path, "rb") as infile, open(encrypted_path, "wb") as outfile:
        outfile.write(iv)  # simpan IV di awal file
        while chunk := infile.read(1024):
            outfile.write(encryptor.update(chunk))
        outfile.write(encryptor.finalize())

    return encrypted_path, key
