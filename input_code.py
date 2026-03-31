# -*- coding: utf-8 -*-
# Pynguin-friendly variant of MSLCrypto

from Cryptodome.Random import get_random_bytes
from Cryptodome.Hash import HMAC, SHA256
from Cryptodome.Cipher import PKCS1_OAEP, AES
from Cryptodome.PublicKey import RSA
from Cryptodome.Util import Padding
import base64
import json


# --------------------------------------------------
# Pure helper functions (high Pynguin value)
# --------------------------------------------------

def fix_base64_padding(payload: str) -> bytes:
    """Decode URL-safe base64 with automatic padding correction."""
    l = len(payload) % 4
    if l == 2:
        payload += "=="
    elif l == 3:
        payload += "="
    elif l != 0:
        raise ValueError("Invalid base64 string")
    return base64.urlsafe_b64decode(payload.encode("utf-8"))


def build_key_id(esn: str, sequence_number: int) -> str:
    return f"{esn}_{sequence_number}"


def extract_key_material(headerdata: dict):
    """Structural extractor for key response data."""
    keydata = headerdata["keyresponsedata"]["keydata"]
    return keydata["encryptionkey"], keydata["hmackey"]


def build_encryption_envelope(iv: bytes, ciphertext: bytes, key_id: str) -> dict:
    return {
        "ciphertext": base64.standard_b64encode(ciphertext).decode("ascii"),
        "keyid": key_id,
        "sha256": "AA==",
        "iv": base64.standard_b64encode(iv).decode("ascii"),
    }


# --------------------------------------------------
# MSLCrypto orchestration class
# --------------------------------------------------

class MSLCrypto:
    """
    Pynguin-friendly MSLCrypto variant.

    - Cryptographic primitives unchanged
    - Randomness injected
    - Protocol logic exposed
    """

    def __init__(
        self,
        kodi_helper=None,
        rng=get_random_bytes,
        rsa_factory=RSA.generate,
    ):
        self.kodi_helper = kodi_helper
        self.rng = rng
        self.rsa_factory = rsa_factory

        self.rsa_key = None
        self.encryption_key = None
        self.sign_key = None

    # --------------------------------------------------
    # RSA key handling
    # --------------------------------------------------

    def generate_rsa_keys(self, key_size: int = 2048):
        self.rsa_key = self.rsa_factory(key_size)

    def get_key_request(self) -> list:
        raw_key = self.rsa_key.publickey().exportKey(format="DER")
        public_key = base64.standard_b64encode(raw_key).decode("ascii")

        return [
            {
                "scheme": "ASYMMETRIC_WRAPPED",
                "keydata": {
                    "publickey": public_key,
                    "mechanism": "JWK_RSA",
                    "keypairid": "superKeyPair",
                },
            }
        ]

    # --------------------------------------------------
    # Serialization
    # --------------------------------------------------

    def to_dict(self) -> dict:
        encrypted_key = self.rsa_key.exportKey()
        return {
            "encryption_key": base64.standard_b64encode(self.encryption_key).decode("ascii"),
            "sign_key": base64.standard_b64encode(self.sign_key).decode("ascii"),
            "rsa_key": base64.standard_b64encode(encrypted_key).decode("ascii"),
        }

    def from_dict(self, data: dict) -> bool:
        """
        Load crypto material.
        Returns True if handshake is required.
        """
        need_handshake = False
        try:
            self.encryption_key = base64.standard_b64decode(data["encryption_key"])
            self.sign_key = base64.standard_b64decode(data["sign_key"])
            rsa_key = base64.standard_b64decode(data["rsa_key"])
            self.rsa_key = RSA.importKey(rsa_key)
        except (KeyError, ValueError, TypeError):
            need_handshake = True

        if not self.encryption_key or not self.sign_key:
            need_handshake = True

        return need_handshake

    # --------------------------------------------------
    # Key response parsing
    #   --------------------------------------------------

    def parse_key_response(self, headerdata: dict):
        enc_key_b64, sign_key_b64 = extract_key_material(headerdata)

        cipher_rsa = PKCS1_OAEP.new(self.rsa_key)

        enc_key_raw = cipher_rsa.decrypt(
            base64.standard_b64decode(enc_key_b64)
        )

        sign_key_raw = cipher_rsa.decrypt(
            base64.standard_b64decode(sign_key_b64)
        )

        enc_key_data = json.loads(enc_key_raw.decode())
        sign_key_data = json.loads(sign_key_raw.decode())

        self.encryption_key = fix_base64_padding(enc_key_data["k"])
        self.sign_key = fix_base64_padding(sign_key_data["k"])

    #------------------------------------
    #symmetric encryption
    #------------------------------------------

    def encrypt(self, data: str, esn: str, sequence_number: int) -> dict:
        iv = self.rng(16)
        plaintext = Padding.pad(data.encode("utf-8"), 16)

        cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext)

        key_id = build_key_id(esn, sequence_number)
        return build_encryption_envelope(iv, ciphertext, key_id)

    def decrypt(self, iv: bytes, data: bytes) -> bytes:
        cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
        return Padding.unpad(cipher.decrypt(data), 16)



def sign(self, message:bytes) ->bytes: 
    return HMAC.new(self.sign_key, message, SHA256).digest()