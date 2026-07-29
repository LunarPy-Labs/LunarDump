"""Unit tests for AES-256-GCM encryption and keygen."""

import pytest
from lunardump.core.security import StreamCipher, generate_key_hex, generate_key_file


def test_keygen():
    key = generate_key_hex()
    assert len(key) == 64  # 32 bytes hex encoded


def test_encryption_decryption_bytes_roundtrip():
    secret_key = generate_key_hex()
    cipher = StreamCipher(secret_key)

    original_data = b"Hello, LunarDump Zero-Trust Encrypted Backup System! " * 100
    encrypted = cipher.encrypt_bytes(original_data)
    assert encrypted != original_data
    assert len(encrypted) > len(original_data)

    decrypted = cipher.decrypt_bytes(encrypted)
    assert decrypted == original_data


def test_encryption_decryption_stream_roundtrip():
    secret_key = generate_key_hex()
    cipher = StreamCipher(secret_key)

    data_chunks = [b"Chunk 1 payload data. ", b"Chunk 2 payload data. ", b"Chunk 3 binary stream!"]

    def chunk_gen():
        for chunk in data_chunks:
            yield chunk

    encrypted_stream = cipher.encrypt_stream(chunk_gen())
    decrypted_stream = cipher.decrypt_stream(encrypted_stream)

    decrypted_result = b"".join(list(decrypted_stream))
    assert decrypted_result == b"".join(data_chunks)


def test_decryption_invalid_key_fails():
    key1 = generate_key_hex()
    key2 = generate_key_hex()

    cipher1 = StreamCipher(key1)
    cipher2 = StreamCipher(key2)

    data = b"Sensitive database backup stream"
    encrypted = cipher1.encrypt_bytes(data)

    with pytest.raises(Exception):
        cipher2.decrypt_bytes(encrypted)
