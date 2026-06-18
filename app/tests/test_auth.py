"""Tests de los endpoints /auth/register, /auth/login y /auth/me/password."""

VALID_PASSWORD = "securepass123"


def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": VALID_PASSWORD, "full_name": "Alice"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["full_name"] == "Alice"
    assert "id" in body
    assert "hashed_password" not in body
    assert "password" not in body


def test_register_without_full_name(client):
    response = client.post(
        "/auth/register",
        json={"email": "no_name@example.com", "password": VALID_PASSWORD},
    )
    assert response.status_code == 201
    assert response.json()["full_name"] is None


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "dup@example.com", "password": VALID_PASSWORD}
    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409
    assert "ya está registrado" in second.json()["detail"].lower()


def test_register_invalid_email_returns_422(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": VALID_PASSWORD},
    )
    assert response.status_code == 422


def test_register_short_password_returns_422(client):
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "x"},
    )
    assert response.status_code == 422


def test_login_success_returns_jwt(client):
    client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": VALID_PASSWORD},
    )
    response = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": VALID_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"].count(".") == 2  # JWT tiene 3 partes separadas por puntos


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": VALID_PASSWORD},
    )
    response = client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert "inválidas" in response.json()["detail"].lower()


def test_login_nonexistent_user_returns_401(client):
    response = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": VALID_PASSWORD},
    )
    assert response.status_code == 401


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def _register_and_login(client, email="change@example.com", password=VALID_PASSWORD):
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def test_change_password_success(client):
    token = _register_and_login(client)
    response = client.patch(
        "/auth/me/password",
        json={"old_password": VALID_PASSWORD, "new_password": "newSecurePass1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "exitosamente" in response.json()["detail"]

    # Verificar que funciona con la nueva contraseña
    resp = client.post(
        "/auth/login",
        json={"email": "change@example.com", "password": "newSecurePass1"},
    )
    assert resp.status_code == 200


def test_change_password_wrong_old_password_returns_401(client):
    token = _register_and_login(client)
    response = client.patch(
        "/auth/me/password",
        json={"old_password": "wrong-old-pass", "new_password": "newSecurePass1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "no es correcta" in response.json()["detail"].lower()


def test_change_password_without_token_returns_401(client):
    response = client.patch(
        "/auth/me/password",
        json={"old_password": VALID_PASSWORD, "new_password": "newSecurePass1"},
    )
    assert response.status_code == 403


def test_change_password_short_new_password_returns_422(client):
    token = _register_and_login(client)
    response = client.patch(
        "/auth/me/password",
        json={"old_password": VALID_PASSWORD, "new_password": "x"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
