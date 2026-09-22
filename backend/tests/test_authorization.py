def _register_and_login(client, email, password="password123"):
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_cannot_see_another_users_skills(client):
    headers_a = _register_and_login(client, "usera@x.com")
    headers_b = _register_and_login(client, "userb@x.com")

    client.post("/profile/skills", json={"name": "python", "level": 0.9}, headers=headers_a)

    skills_b = client.get("/profile/skills", headers=headers_b).json()
    assert skills_b == []


def test_user_cannot_delete_another_users_skill(client):
    headers_a = _register_and_login(client, "usera2@x.com")
    headers_b = _register_and_login(client, "userb2@x.com")

    skill = client.post(
        "/profile/skills", json={"name": "python", "level": 0.9}, headers=headers_a
    ).json()

    r = client.delete(f"/profile/skills/{skill['id']}", headers=headers_b)
    assert r.status_code == 404

    still_there = client.get("/profile/skills", headers=headers_a).json()
    assert len(still_there) == 1


def test_user_cannot_patch_another_users_application(client):
    headers_a = _register_and_login(client, "usera3@x.com")
    headers_b = _register_and_login(client, "userb3@x.com")

    app_row = client.post(
        "/applications",
        json={"company": "Acme", "role_title": "SWE", "status": "applied"},
        headers=headers_a,
    ).json()

    r = client.patch(
        f"/applications/{app_row['id']}",
        json={"company": "Acme", "role_title": "SWE", "status": "offer"},
        headers=headers_b,
    )
    assert r.status_code == 404


def test_invalid_email_rejected_at_registration(client):
    r = client.post("/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert r.status_code == 422


def test_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "short@x.com", "password": "abc"})
    assert r.status_code == 422


def test_duplicate_skill_name_rejected(client, auth_headers=None):
    headers = _register_and_login(client, "dupskill@x.com")
    r1 = client.post("/profile/skills", json={"name": "python", "level": 0.5}, headers=headers)
    assert r1.status_code == 201
    r2 = client.post("/profile/skills", json={"name": "python", "level": 0.7}, headers=headers)
    assert r2.status_code == 409  # unique constraint -> handled, not a raw 500


def test_invalid_application_status_rejected(client):
    headers = _register_and_login(client, "badstatus@x.com")
    r = client.post(
        "/applications",
        json={"company": "Acme", "role_title": "SWE", "status": "ghosted"},
        headers=headers,
    )
    assert r.status_code == 422


def test_expired_or_garbage_token_rejected(client):
    r = client.get("/profile/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_deleting_user_cascades_skills(client):
    """Not exposed via API (no delete-user endpoint yet), so this exercises
    the ON DELETE CASCADE constraint directly against the DB."""
    from app import models
    from app.auth import hash_password
    from app.database import SessionLocal

    db = SessionLocal()
    user = models.User(email="cascade@x.com", hashed_password=hash_password("password123"))
    db.add(user)
    db.commit()
    db.refresh(user)

    skill = models.Skill(owner_id=user.id, name="python", level=0.5)
    db.add(skill)
    db.commit()

    db.delete(user)
    db.commit()

    remaining = db.query(models.Skill).filter(models.Skill.owner_id == user.id).all()
    assert remaining == []
    db.close()
