from __future__ import annotations

import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from backend.app.core.configs import settings


def _derive_user_key(user_id: str) -> bytes:
    master_key = settings.admin.master_encryption_key.get_secret_value().encode("utf-8")
    info = f"neura-admin-role-encryption:{user_id}".encode("utf-8")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=info,
    )
    return hkdf.derive(master_key)


def encrypt_role_permissions(user_id: str, permissions: list[str]) -> str:
    key = _derive_user_key(user_id)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps({"permissions": permissions, "user_id": user_id}).encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    combined = base64.b64encode(nonce + ciphertext).decode("utf-8")
    return combined


def decrypt_role_permissions(user_id: str, encrypted_data: str) -> list[str]:
    key = _derive_user_key(user_id)
    aesgcm = AESGCM(key)
    raw = base64.b64decode(encrypted_data.encode("utf-8"))
    nonce = raw[:12]
    ciphertext = raw[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    payload = json.loads(plaintext.decode("utf-8"))
    return payload["permissions"]
