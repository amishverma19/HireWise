"""
HireWise: Autonomous Multi-Agent Resume Analyzer and Career Coach.
"""
import hashlib
import os
import sys

__version__ = "1.0.0"

# Disable SQLAlchemy C-extensions if on Windows or restricted environment
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

# Pure Python fallback for xxhash if native C-extension is blocked by OS Application Control policies
try:
    import xxhash  # noqa: F401
except ImportError:
    class _DummyHash:
        def __init__(self, data=b""):
            self.h = hashlib.sha256(data if isinstance(data, bytes) else str(data).encode("utf-8"))

        def update(self, val):
            self.h.update(val if isinstance(val, bytes) else str(val).encode("utf-8"))

        def digest(self):
            return self.h.digest()[:16]

        def hexdigest(self):
            return self.h.hexdigest()[:32]

        def intdigest(self):
            return int(self.h.hexdigest()[:16], 16)

    class _MockXXHashModule:
        @staticmethod
        def xxh3_128(data=b""): return _DummyHash(data)
        @staticmethod
        def xxh3_128_hexdigest(data=b""): return _DummyHash(data).hexdigest()
        @staticmethod
        def xxh3_128_digest(data=b""): return _DummyHash(data).digest()
        @staticmethod
        def xxh3_128_intdigest(data=b""): return _DummyHash(data).intdigest()
        @staticmethod
        def xxh3_64(data=b""): return _DummyHash(data)
        @staticmethod
        def xxh3_64_hexdigest(data=b""): return _DummyHash(data).hexdigest()
        @staticmethod
        def xxh3_64_digest(data=b""): return _DummyHash(data).digest()
        @staticmethod
        def xxh3_64_intdigest(data=b""): return _DummyHash(data).intdigest()
        @staticmethod
        def xxh32(data=b""): return _DummyHash(data)
        @staticmethod
        def xxh64(data=b""): return _DummyHash(data)
        version = "3.5.0"

    sys.modules["xxhash"] = _MockXXHashModule
