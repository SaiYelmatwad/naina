def test_scan_with_matching_skills(client, auth_headers):
    client.post(
        "/profile/skills",
        json={"name": "python", "level": 0.9, "category": "coding"},
        headers=auth_headers,
    )
    client.post(
        "/profile/skills",
        json={"name": "distributed systems", "level": 0.8, "category": "systems"},
        headers=auth_headers,
    )
    client.post(
        "/profile/skills",
        json={"name": "kubernetes", "level": 0.1, "category": "systems"},
        headers=auth_headers,
    )

    r = client.post(
        "/scan",
        json={"role_text": "Senior backend engineer. Python, distributed systems, kubernetes experience."},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["score"] <= 100
    assert body["verdict"] in {"Strong fit", "Worth applying", "Reach role"}
    matched_names = {m["skill"] for m in body["matched"]}
    assert "python" in matched_names


def test_scan_with_no_matching_profile(client, auth_headers):
    r = client.post(
        "/scan",
        json={"role_text": "Some role with no overlapping vocabulary at all xyzzy"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["score"] <= 40


def test_scan_history_persists_and_paginates(client, auth_headers):
    client.post("/profile/skills", json={"name": "python", "level": 0.9}, headers=auth_headers)
    for i in range(3):
        client.post("/scan", json={"role_text": f"python backend role {i}"}, headers=auth_headers)

    r = client.get("/scan/history?page=1&page_size=2", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["has_next"] is True

    r2 = client.get("/scan/history?page=2&page_size=2", headers=auth_headers)
    assert len(r2.json()["items"]) == 1
    assert r2.json()["meta"]["has_next"] is False


def test_scan_rejects_oversized_input(client, auth_headers):
    r = client.post("/scan", json={"role_text": "x" * 9000}, headers=auth_headers)
    assert r.status_code == 422


def test_scan_rejects_empty_input(client, auth_headers):
    r = client.post("/scan", json={"role_text": "a"}, headers=auth_headers)
    assert r.status_code == 422
