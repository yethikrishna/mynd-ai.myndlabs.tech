"""
Envelope encryption for credential payloads.

Secrets are never stored in plaintext. The production path wraps the payload
with a cloud KMS key (GCP KMS / AWS KMS); a local Fernet fallback exists for
development and tests. The provider is chosen by ``MYND_KMS_PROVIDER``:

    MYND_KMS_PROVIDER = "gcp" | "aws" | "local"  (default: "local")

For GCP:   MYND_GCP_KMS_KEY = projects/<p>/locations/<l>/keyRings/<r>/cryptoKeys/<k>
For AWS:   MYND_AWS_KMS_KEY_ID = <key-id-or-arn>
For local: MYND_LOCAL_ENCRYPTION_KEY = <base64 urlsafe 32-byte Fernet key>

A credential ``payload`` is an arbitrary JSON-serializable dict (api key,
oauth tokens, service-account JSON, aws keys, …).
"""

from __future__ import annotations

import json
import os
from abc import ABC
from abc import abstractmethod


class _Cipher(ABC):
    @abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes: ...

    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes: ...


class _LocalFernetCipher(_Cipher):
    def __init__(self) -> None:
        from cryptography.fernet import Fernet

        key = os.environ.get("MYND_LOCAL_ENCRYPTION_KEY")
        if not key:
            raise RuntimeError(
                "MYND_LOCAL_ENCRYPTION_KEY is not set; cannot encrypt "
                "credentials with the local cipher."
            )
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: bytes) -> bytes:
        return self._fernet.encrypt(plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        return self._fernet.decrypt(ciphertext)


class _GCPKMSCipher(_Cipher):  # pragma: no cover - requires GCP creds
    def __init__(self) -> None:
        from google.cloud import kms

        self._client = kms.KeyManagementServiceClient()
        self._key = os.environ["MYND_GCP_KMS_KEY"]

    def encrypt(self, plaintext: bytes) -> bytes:
        resp = self._client.encrypt(
            request={"name": self._key, "plaintext": plaintext}
        )
        return resp.ciphertext

    def decrypt(self, ciphertext: bytes) -> bytes:
        resp = self._client.decrypt(
            request={"name": self._key, "ciphertext": ciphertext}
        )
        return resp.plaintext


class _AWSKMSCipher(_Cipher):  # pragma: no cover - requires AWS creds
    def __init__(self) -> None:
        import boto3

        self._client = boto3.client("kms")
        self._key_id = os.environ["MYND_AWS_KMS_KEY_ID"]

    def encrypt(self, plaintext: bytes) -> bytes:
        resp = self._client.encrypt(KeyId=self._key_id, Plaintext=plaintext)
        return resp["CiphertextBlob"]

    def decrypt(self, ciphertext: bytes) -> bytes:
        resp = self._client.decrypt(CiphertextBlob=ciphertext)
        return resp["Plaintext"]


def _get_cipher() -> _Cipher:
    provider = os.environ.get("MYND_KMS_PROVIDER", "local").lower()
    if provider == "gcp":
        return _GCPKMSCipher()
    if provider == "aws":
        return _AWSKMSCipher()
    return _LocalFernetCipher()


def encrypt_payload(payload: dict) -> bytes:
    """Serialize + encrypt a credential payload dict to opaque bytes."""
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return _get_cipher().encrypt(raw)


def decrypt_payload(blob: bytes) -> dict:
    """Decrypt + deserialize a stored credential payload."""
    raw = _get_cipher().decrypt(blob)
    return json.loads(raw.decode())
