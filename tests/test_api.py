from datetime import date, datetime, timezone


def wp(i=0):
    return {
        "name": "Push",
        "exercise": f"Bench {i}",
        "sets": 3,
        "reps": 10,
        "weight_kg": 60,
        "performed_at": datetime.now(timezone.utc).isoformat(),
    }


def np(i=0):
    return {
        "date": str(date.today()),
        "calories": 2200 + i,
        "protein_g": 160,
        "carbs_g": 200,
        "fat_g": 70,
        "notes": "training",
    }


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "healthy"


def test_auth(client):
    assert (
        client.post(
            "/auth/register",
            json={"email": "a@example.com", "password": "StrongPass123!"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/auth/register",
            json={"email": "a@example.com", "password": "StrongPass123!"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/auth/login", json={"email": "a@example.com", "password": "bad"}
        ).status_code
        == 401
    )
    t = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "StrongPass123!"}
    ).json()["access_token"]
    assert (
        client.get("/auth/me", headers={"Authorization": f"Bearer {t}"}).status_code
        == 200
    )
    assert client.get("/workouts").status_code == 401


def test_workout_crud_pagination_stats(client, auth_headers):
    for i in range(5):
        assert (
            client.post("/workouts", json=wp(i), headers=auth_headers).status_code
            == 201
        )
    r = client.get("/workouts?page=2&page_size=2", headers=auth_headers)
    assert r.status_code == 200 and r.json()["total"] == 5
    assert len(r.json()["items"]) == 2

    # First stats call misses the cache, second hits it (fakeredis in conftest).
    r = client.get("/workouts/stats", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total_workouts"] == 5 and r.json()["cache_hit"] is False
    r = client.get("/workouts/stats", headers=auth_headers)
    assert r.json()["cache_hit"] is True and r.json()["total_workouts"] == 5

    wid = client.get("/workouts?page=1&page_size=1", headers=auth_headers).json()[
        "items"
    ][0]["id"]
    assert (
        client.patch(
            f"/workouts/{wid}", json={"weight_kg": 65}, headers=auth_headers
        ).status_code
        == 200
    )
    # Mutation invalidates the cached stats.
    r = client.get("/workouts/stats", headers=auth_headers)
    assert r.json()["cache_hit"] is False
    assert client.delete(f"/workouts/{wid}", headers=auth_headers).status_code == 204
    assert client.get(f"/workouts/{wid}", headers=auth_headers).status_code == 404


def test_user_isolation(client):
    for e in ("a@e.com", "b@e.com"):
        client.post("/auth/register", json={"email": e, "password": "StrongPass123!"})
    hs = []
    for e in ("a@e.com", "b@e.com"):
        t = client.post(
            "/auth/login", json={"email": e, "password": "StrongPass123!"}
        ).json()["access_token"]
        hs.append({"Authorization": f"Bearer {t}"})
    wid = client.post("/workouts", json=wp(), headers=hs[0]).json()["id"]
    assert client.get(f"/workouts/{wid}", headers=hs[1]).status_code == 404


def test_nutrition(client, auth_headers):
    for i in range(3):
        assert (
            client.post("/nutrition", json=np(i), headers=auth_headers).status_code
            == 201
        )
    r = client.get("/nutrition?page=1&page_size=2", headers=auth_headers)
    assert r.status_code == 200 and r.json()["total"] == 3
    eid = r.json()["items"][0]["id"]
    assert (
        client.patch(
            f"/nutrition/{eid}", json={"protein_g": 170}, headers=auth_headers
        ).status_code
        == 200
    )
    assert client.delete(f"/nutrition/{eid}", headers=auth_headers).status_code == 204


def test_summary_and_queue(client, auth_headers, monkeypatch):
    r = client.get("/summaries/weekly/latest", headers=auth_headers)
    assert r.status_code == 200 and r.json()["workout_count"] == 0
    from app.routers import summaries

    class Dummy:
        id = "task-1"

    monkeypatch.setattr(summaries.weekly_summary, "delay", lambda uid: Dummy())
    r = client.post("/summaries/weekly", headers=auth_headers)
    assert r.json() == {"task_id": "task-1", "status": "queued"}


def test_validation(client, auth_headers):
    assert (
        client.post(
            "/workouts",
            json={
                "name": "",
                "exercise": "x",
                "sets": 0,
                "reps": 1,
                "weight_kg": 1,
                "performed_at": "bad",
            },
            headers=auth_headers,
        ).status_code
        == 422
    )


def test_refresh_token_rotation_and_logout(client):
    assert (
        client.post(
            "/auth/register",
            json={"email": "refresh@example.com", "password": "StrongPass123!"},
        ).status_code
        == 201
    )
    pair = client.post(
        "/auth/login",
        json={"email": "refresh@example.com", "password": "StrongPass123!"},
    ).json()
    assert pair["access_token"] and pair["refresh_token"]

    # Rotate: old refresh token dies, new pair works. (Access tokens may be
    # byte-identical when issued within the same second; refresh tokens never
    # are, because each carries a unique jti.)
    pair2 = client.post(
        "/auth/refresh", json={"refresh_token": pair["refresh_token"]}
    ).json()
    assert pair2["refresh_token"] != pair["refresh_token"]
    r = client.post("/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert r.status_code == 401  # reuse of rotated token is rejected

    # Logout revokes the current refresh token.
    assert (
        client.post(
            "/auth/logout", json={"refresh_token": pair2["refresh_token"]}
        ).status_code
        == 204
    )
    r = client.post("/auth/refresh", json={"refresh_token": pair2["refresh_token"]})
    assert r.status_code == 401

    # An access token can never be used as a refresh token.
    r = client.post("/auth/refresh", json={"refresh_token": pair2["access_token"]})
    assert r.status_code == 401


def test_workout_filters(client, auth_headers):
    today = date.today().isoformat()
    client.post("/workouts", json=wp(0), headers=auth_headers)
    squat = dict(wp(1), exercise="Back Squat", name="Legs")
    client.post("/workouts", json=squat, headers=auth_headers)

    r = client.get("/workouts?exercise=squat", headers=auth_headers)
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["exercise"] == "Back Squat"

    r = client.get(f"/workouts?date_from={today}&date_to={today}", headers=auth_headers)
    assert r.json()["total"] == 2

    r = client.get(
        "/workouts?date_from=2000-01-01&date_to=2000-01-02", headers=auth_headers
    )
    assert r.json()["total"] == 0


def test_request_id_header(client):
    r = client.get("/health")
    assert r.headers.get("x-request-id")
    r = client.get("/health", headers={"x-request-id": "abc123"})
    assert r.headers["x-request-id"] == "abc123"


def test_beat_schedule_configured():
    from app.tasks.celery_app import celery

    schedule = celery.conf.beat_schedule
    assert "weekly-summaries" in schedule
    entry = schedule["weekly-summaries"]
    assert entry["task"] == "weekly_summary_all_users"
    # Mondays at 00:00 UTC.
    assert entry["schedule"].hour == {0} and entry["schedule"].minute == {0}


def test_weekly_summary_task_retries():
    from app.tasks.summary import weekly_summary

    assert weekly_summary.autoretry_for == (Exception,)
    assert weekly_summary.retry_kwargs["max_retries"] == 3
