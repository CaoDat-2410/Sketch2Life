"""AES-256-GCM and a keyed MAC for encrypted profile support needs (T-12c).

The cipher is real (``cryptography``, AES-256-GCM, a fresh 96-bit nonce per encryption, the record
identity as associated data). One key per family is derived with HKDF-SHA-256 from a master key
of the keyring, so the Parent and BE1 tables never share an encryption key, and the receipt MAC
key is a different master key from the encryption one.

Nothing here reads the environment or a file. A keyring is built from bytes the caller already
holds: tests build one from synthetic bytes; the production composition has none until the owner
approves a key source (gate O-SEED-KEY), so the routes answer 503 ``SUPPORT_NEEDS_UNAVAILABLE``.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable, Mapping
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from sketch2life.application.ports.support_needs import (
    SealedSupportNeeds,
    SupportNeedsUnavailable,
)
from sketch2life.domain.support_needs import (
    ALGORITHM_VERSION,
    KEY_BYTES,
    NONCE_BYTES,
    SupportNeedsFamily,
    SupportNeedsPayload,
    SupportNeedsRuleViolation,
    build_aad,
    fingerprint_message,
    parse_plaintext,
)

NonceSource = Callable[[], bytes]

_ENCRYPTION_INFO: Final = b"s2l.support-needs.v1.encryption."
_FINGERPRINT_INFO: Final = b"s2l.support-needs.v1.receipt-mac."


def secure_nonce() -> bytes:
    """The production nonce source: 12 bytes from the operating system's CSPRNG."""
    return secrets.token_bytes(NONCE_BYTES)


def _valid_key_id(value: str) -> bool:
    return 1 <= len(value) <= 128 and all(33 <= ord(char) <= 126 for char in value)


class StaticSupportNeedsKeyring:
    """Master keys held in memory, by key id; one current id for encryption, one for the MAC."""

    def __init__(
        self,
        *,
        encryption_keys: Mapping[str, bytes],
        current_key_id: str,
        fingerprint_keys: Mapping[str, bytes],
        current_fingerprint_key_id: str,
    ) -> None:
        for name, keys, current in (
            ("encryption", encryption_keys, current_key_id),
            ("fingerprint", fingerprint_keys, current_fingerprint_key_id),
        ):
            if current not in keys:
                raise ValueError(f"the current {name} key id is not in the keyring")
            for key_id, material in keys.items():
                if not _valid_key_id(key_id) or len(material) < KEY_BYTES:
                    raise ValueError(f"a {name} key is malformed or shorter than {KEY_BYTES} bytes")
        encryption_material = set(encryption_keys.values())
        if encryption_material & set(fingerprint_keys.values()):
            raise ValueError("an encryption key and a fingerprint key must differ")
        self._encryption = dict(encryption_keys)
        self._fingerprint = dict(fingerprint_keys)
        self.current_key_id = current_key_id
        self.current_fingerprint_key_id = current_fingerprint_key_id

    def encryption_key(self, family: SupportNeedsFamily, key_id: str) -> bytes | None:
        master = self._encryption.get(key_id)
        if master is None:
            return None
        return _derive(master, _ENCRYPTION_INFO + family.encode("ascii"))

    def fingerprint_key(self, family: SupportNeedsFamily, key_id: str) -> bytes | None:
        master = self._fingerprint.get(key_id)
        if master is None:
            return None
        return _derive(master, _FINGERPRINT_INFO + family.encode("ascii"))


def _derive(master: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=KEY_BYTES, salt=None, info=info).derive(master)


class AesGcmSupportNeedsCrypto:
    """The `SupportNeedsCrypto` port over a keyring and a nonce source."""

    def __init__(
        self, keyring: StaticSupportNeedsKeyring, nonce_source: NonceSource = secure_nonce
    ) -> None:
        self._keyring = keyring
        self._nonce_source = nonce_source

    @property
    def fingerprint_key_id(self) -> str:
        return self._keyring.current_fingerprint_key_id

    def seal(
        self,
        *,
        family: SupportNeedsFamily,
        tenant: str,
        profile_id: str,
        revision: int,
        payload: SupportNeedsPayload,
    ) -> SealedSupportNeeds:
        key_id = self._keyring.current_key_id
        key = self._keyring.encryption_key(family, key_id)
        if key is None:
            raise SupportNeedsUnavailable("no encryption key")
        nonce = self._nonce_source()
        if len(nonce) != NONCE_BYTES:
            raise SupportNeedsUnavailable("bad nonce")
        aad = build_aad(
            family=family,
            tenant=tenant,
            profile_id=profile_id,
            revision=revision,
            key_id=key_id,
        )
        ciphertext = AESGCM(key).encrypt(nonce, payload.plaintext(), aad)
        return SealedSupportNeeds(
            ciphertext=ciphertext,
            nonce=nonce,
            key_id=key_id,
            algorithm_version=ALGORITHM_VERSION,
        )

    def open(
        self,
        *,
        family: SupportNeedsFamily,
        tenant: str,
        profile_id: str,
        revision: int,
        sealed: SealedSupportNeeds,
    ) -> SupportNeedsPayload:
        if sealed.algorithm_version != ALGORITHM_VERSION or len(sealed.nonce) != NONCE_BYTES:
            raise SupportNeedsUnavailable("unsupported record")
        key = self._keyring.encryption_key(family, sealed.key_id)
        if key is None:
            raise SupportNeedsUnavailable("no encryption key")
        aad = build_aad(
            family=family,
            tenant=tenant,
            profile_id=profile_id,
            revision=revision,
            key_id=sealed.key_id,
            algorithm_version=sealed.algorithm_version,
        )
        try:
            plaintext = AESGCM(key).decrypt(sealed.nonce, sealed.ciphertext, aad)
            return parse_plaintext(plaintext)
        except (InvalidTag, SupportNeedsRuleViolation):
            raise SupportNeedsUnavailable("record does not authenticate") from None

    def fingerprint(
        self,
        *,
        family: SupportNeedsFamily,
        tenant: str,
        profile_id: str,
        principal: str,
        expected_revision: int,
        payload: SupportNeedsPayload,
        key_id: str | None = None,
    ) -> bytes:
        key = self._keyring.fingerprint_key(
            family, key_id if key_id is not None else self._keyring.current_fingerprint_key_id
        )
        if key is None:
            raise SupportNeedsUnavailable("no fingerprint key")
        message = fingerprint_message(
            family=family,
            tenant=tenant,
            profile_id=profile_id,
            principal=principal,
            expected_revision=expected_revision,
            payload=payload,
        )
        return hmac.new(key, message, hashlib.sha256).digest()


__all__ = [
    "AesGcmSupportNeedsCrypto",
    "NonceSource",
    "StaticSupportNeedsKeyring",
    "secure_nonce",
]
