from app.services.auth_service import hash_password, verify_password


def test_correct_password_verifies() -> None:
    hashed = hash_password("qwerty123")
    assert verify_password("qwerty123", hashed) is True


def test_wrong_password_does_not_verify() -> None:
    hashed = hash_password("qwerty123")
    assert verify_password("wrong", hashed) is False


def test_two_hashes_of_same_password_differ() -> None:
    assert hash_password("qwerty123") != hash_password("qwerty123")
