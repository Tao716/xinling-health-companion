from types import SimpleNamespace

from api.db.services.user_service import UserService


def test_password_hash_is_salted_and_verifiable():
    first = UserService._hash_password("correct horse battery staple")
    second = UserService._hash_password("correct horse battery staple")

    assert first != second
    assert UserService.verify_password(SimpleNamespace(password=first), "correct horse battery staple")
    assert not UserService.verify_password(SimpleNamespace(password=first), "wrong password")
