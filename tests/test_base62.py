from domain.base62 import Base62Encoder


def test_base62_round_trip() -> None:
    original = 987654321
    encoded = Base62Encoder.encode(original)
    decoded = Base62Encoder.decode(encoded)
    assert decoded == original
