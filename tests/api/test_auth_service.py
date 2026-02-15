from app.services.auth_service import hash_password, verify_password, create_access_token, verify_token


def test_password_hash_and_verify():
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_and_verify_token():
    user_id = "test-user-id-123"
    token = create_access_token(user_id)
    assert isinstance(token, str)

    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == user_id


def test_verify_invalid_token():
    payload = verify_token("invalid-token")
    assert payload is None
