def test_register_and_login(client):
    r = client.post(
        "/auth/register",
        json={"email": "a@b.com", "password": "supersecret1", "full_name": "A B"},
    )
    assert r.status_code == 201
    assert r.json()["email"] == "a@b.com"

    r2 = client.post("/auth/login", data={"username": "a@b.com", "password": "supersecret1"})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_duplicate_register_rejected(client):
    client.post("/auth/register", json={"email": "dup@b.com", "password": "supersecret1"})
    r = client.post("/auth/register", json={"email": "dup@b.com", "password": "supersecret1"})
    assert r.status_code == 400


def test_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "c@b.com", "password": "supersecret1"})
    r = client.post("/auth/login", data={"username": "c@b.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    r = client.get("/profile/me")
    assert r.status_code == 401
