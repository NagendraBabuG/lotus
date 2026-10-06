from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, mldsa


def run_test(test_name, expected_success, func):
    ADAPTERS = [Ed25519Adapter(), MLDSA65Adapter()]

    status = None

    for adapter in ADAPTERS:
        prev_status = status

        try:
            func(adapter)

            if expected_success:
                status = f"[PASS] {test_name}"
            else:
                status = f"[FAIL] {test_name} (expected exception)"

        except Exception as e:
            if expected_success:
                status = f"[FAIL] {test_name}: {type(e).__name__}: {e}"
            else:
                status = f"[PASS] {test_name} (caught {type(e).__name__})"

        if status == prev_status:
            print(f"EQUIVALENT BEHAVIOUR: {status}\n")
        else:
            print(f"DIVERGENT BEHAVIOUR:\n{prev_status}\n{status}\n")


# ================================================================
# ORIGINAL & TRANSLATED SNIPPET
# ================================================================

def source():
    private_key = ed25519.Ed25519PrivateKey.generate()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )

    loaded_private_key = (
        ed25519.Ed25519PrivateKey.from_private_bytes(
            private_bytes
        )
    )


# AFTER TRANSLATION

def translated():
    private_key = mldsa.MLDSA65PrivateKey.generate()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )

    loaded_private_key = (
        mldsa.MLDSA65PrivateKey.from_seed_bytes(
            private_bytes
        )
    )


# ================================================================
# SOURCE ADAPTER - EXTRACT RELEVANT METHODS
# ================================================================

class Ed25519Adapter:

    def generate_private_key(self):
        return ed25519.Ed25519PrivateKey.generate()

    def serialize_private_key(self, private_key):
        return private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

    def load_private_key(self, private_bytes):
        return ed25519.Ed25519PrivateKey.from_private_bytes(
            private_bytes
        )

    # ============================================================
    # ADDITIONAL METHODS FOR ENABLING TESTING ON DIFFERENT
    # USE-CASES
    # ============================================================

    def encode_private_key(self, private_key, password):
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(
                password
            )
        )

    def load_pem_key(self, private_key, password):
        return serialization.load_pem_private_key(
            private_key,
            password
        )

    def load_private_key_bytearray(self, private_bytes):
        return ed25519.Ed25519PrivateKey.from_private_bytes(
            bytearray(private_bytes)
        )


# ================================================================
# TRANSLATED ADAPTER
# ================================================================

class MLDSA65Adapter:

    def generate_private_key(self):
        return mldsa.MLDSA65PrivateKey.generate()

    def serialize_private_key(self, private_key):
        return private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

    def load_private_key(self, private_bytes):
        return mldsa.MLDSA65PrivateKey.from_seed_bytes(
            private_bytes
        )

    # ============================================================
    # ADDITIONAL METHODS FOR ENABLING TESTING ON DIFFERENT
    # USE-CASES
    # ============================================================

    def encode_private_key(self, private_key, password):
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(
                password
            )
        )

    def load_pem_key(self, private_key, password):
        return serialization.load_pem_private_key(
            private_key,
            password
        )

    def load_private_key_bytearray(self, private_bytes):
        return mldsa.MLDSA65PrivateKey.from_seed_bytes(
            bytearray(private_bytes)
        )


# ================================================================
# ORIGINAL WORKFLOW - TEST SUITE BEGINS
# ================================================================

def test_serialize_load(adapter):
    private_key = adapter.generate_private_key()

    private_bytes = adapter.serialize_private_key(
        private_key
    )

    loaded_private_key = adapter.load_private_key(
        private_bytes
    )

    assert loaded_private_key is not None


run_test(
    "Generate serialize load",
    True,
    test_serialize_load
)


# ================================================================
# PROTECTED SERIALIZATION
# ================================================================

def test_protected_load(adapter):
    private_key = adapter.generate_private_key()

    private_bytes = adapter.encode_private_key(
        private_key,
        b"password"
    )

    loaded_private_key = adapter.load_pem_key(
        private_bytes,
        b"password"
    )

    assert loaded_private_key is not None


run_test(
    "Generate serialized encryption",
    True,
    test_protected_load
)


# ================================================================
# ASSERT KEY LENGTH
# ================================================================

def test_private_key_length(adapter):
    private_key = adapter.generate_private_key()

    private_bytes = adapter.serialize_private_key(
        private_key
    )

    assert len(private_bytes) == 32


run_test(
    "Raw private key length is 32 bytes",
    True,
    test_private_key_length
)


# ================================================================
# SAVE / LOAD
# ================================================================

def test_loaded_key_signs(adapter):
    private_key = adapter.generate_private_key()

    private_bytes = adapter.serialize_private_key(
        private_key
    )

    with open("ed25519_key.bin", "wb") as f:
        f.write(private_bytes)

    with open("ed25519_key.bin", "rb") as f:
        loaded_key = adapter.load_private_key(
            f.read()
        )

    loaded_bytes = adapter.serialize_private_key(
        loaded_key
    )

    assert type(private_key) == type(loaded_key)


run_test(
    "Loaded key correctly",
    True,
    test_loaded_key_signs
)


# ================================================================
# INVALID PRIVATE KEY LENGTHS
# ================================================================

def load_empty_key(adapter):
    private_bytes = adapter.load_private_key(
        b""
    )

    assert private_bytes is not None


run_test(
    "Zero length private key",
    False,
    load_empty_key
)


def load_short_key(adapter):
    private_bytes = adapter.load_private_key(
        b"\x00" * 16
    )

    assert private_bytes is not None


run_test(
    "Short private key",
    False,
    load_short_key
)


def load_long_key(adapter):
    private_bytes = adapter.load_private_key(
        b"\x00" * 64
    )

    assert private_bytes is not None


run_test(
    "Long private key",
    False,
    load_long_key
)


# ================================================================
# INVALID INPUT TYPES
# ================================================================

def load_string(adapter):
    private_bytes = adapter.load_private_key(
        "not bytes"
    )

    assert private_bytes is not None


run_test(
    "String input",
    False,
    load_string
)


def load_integer(adapter):
    private_bytes = adapter.load_private_key(
        1
    )

    assert private_bytes is not None


run_test(
    "Integer input",
    False,
    load_integer
)


def load_none(adapter):
    private_bytes = adapter.load_private_key(
        None
    )

    assert private_bytes is not None


run_test(
    "None input",
    False,
    load_none
)


# ================================================================
# BYTEARRAY
# ================================================================

def load_bytearray(adapter):
    key = adapter.generate_private_key()

    private_bytes = adapter.serialize_private_key(
        key
    )

    loaded_bytes = adapter.load_private_key_bytearray(
        private_bytes
    )

    assert loaded_bytes is not None


run_test(
    "Bytearray input",
    True,
    load_bytearray
)


print("\nTest execution completed.")
