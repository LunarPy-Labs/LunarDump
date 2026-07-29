"""AES-256-GCM encryption and decryption module for LunarDump."""

import os
import base64
import struct
from typing import Generator, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC_HEADER = b"LUNARDUMP_V1\n"
CHUNK_SIZE = 64 * 1024  # 64KB chunks for streaming encryption


def derive_key(secret_key: str, salt: bytes) -> bytes:
    """Derive a 256-bit encryption key using PBKDF2-HMAC-SHA256.

    If secret_key is already a 64-char hex or 44-char base64 string matching 32 raw bytes,
    derive key or validate length directly.
    """
    try:
        # Check if secret_key is 32-byte hex string
        if len(secret_key) == 64:
            return bytes.fromhex(secret_key)
        # Check if secret_key is base64 encoded 32 bytes
        decoded = base64.b64decode(secret_key)
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(secret_key.encode("utf-8"))


class StreamCipher:
    """AES-256-GCM Streaming Cipher."""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def encrypt_stream(
        self, stream: Generator[bytes, None, None]
    ) -> Generator[bytes, None, None]:
        """Encrypt input bytes stream chunk-by-chunk with AES-256-GCM.

        Output layout:
          - MAGIC_HEADER (13 bytes)
          - Salt (16 bytes)
          - For each chunk:
            - Chunk payload length (4 bytes uint32 big-endian)
            - Nonce (12 bytes)
            - Ciphertext + GCM Tag (chunk_payload + 16 bytes)
        """
        salt = os.urandom(16)
        raw_key = derive_key(self.secret_key, salt)
        aesgcm = AESGCM(raw_key)

        # Yield magic header and salt
        yield MAGIC_HEADER
        yield salt

        chunk_counter = 0
        for chunk in stream:
            if not chunk:
                continue
            nonce = struct.pack(">I", chunk_counter) + os.urandom(8)
            ciphertext = aesgcm.encrypt(nonce, chunk, None)
            total_len = len(ciphertext)
            yield struct.pack(">I", total_len)
            yield nonce
            yield ciphertext
            chunk_counter += 1

    def decrypt_stream(
        self, stream: Generator[bytes, None, None]
    ) -> Generator[bytes, None, None]:
        """Decrypt streaming bytes encrypted with encrypt_stream."""
        buffer = bytearray()

        def read_bytes(count: int) -> bytes:
            nonlocal buffer
            while len(buffer) < count:
                try:
                    chunk = next(stream)
                    buffer.extend(chunk)
                except StopIteration:
                    break
            if len(buffer) < count:
                raise ValueError("Corrupted stream: unexpected EOF while reading header or chunk")
            result = bytes(buffer[:count])
            del buffer[:count]
            return result

        # Read magic header
        magic = read_bytes(len(MAGIC_HEADER))
        if magic != MAGIC_HEADER:
            raise ValueError("Invalid file format or header mismatch")

        salt = read_bytes(16)
        raw_key = derive_key(self.secret_key, salt)
        aesgcm = AESGCM(raw_key)

        while True:
            # Check if EOF reached
            if len(buffer) < 4:
                try:
                    chunk = next(stream)
                    buffer.extend(chunk)
                except StopIteration:
                    if len(buffer) == 0:
                        break
                    else:
                        raise ValueError("Truncated data stream at chunk length header")

            len_bytes = read_bytes(4)
            (chunk_len,) = struct.unpack(">I", len_bytes)

            nonce = read_bytes(12)
            ciphertext = read_bytes(chunk_len)

            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            yield plaintext

    def encrypt_bytes(self, data: bytes) -> bytes:
        """Helper to encrypt complete byte string."""
        def _gen():
            for i in range(0, len(data), CHUNK_SIZE):
                yield data[i : i + CHUNK_SIZE]

        result = bytearray()
        for chunk in self.encrypt_stream(_gen()):
            result.extend(chunk)
        return bytes(result)

    def decrypt_bytes(self, data: bytes) -> bytes:
        """Helper to decrypt complete byte string."""
        def _gen():
            yield data

        result = bytearray()
        for chunk in self.decrypt_stream(_gen()):
            result.extend(chunk)
        return bytes(result)
