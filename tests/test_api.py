from datetime import date, timedelta


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_home_page_lists_programs(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Fat Loss" in resp.data and b"Muscle Gain" in resp.data


def test_programs_endpoint(client):
    data = client.get("/api/programs").get_json()
    assert len(data) == 3


def test_program_detail_and_404(client):
    assert client.get("/api/programs/bg").get_json()["calorie_factor"] == 26
    assert client.get("/api/programs/XX").status_code == 404


def test_calories_endpoint(client):
    resp = client.post("/api/calories", json={"weight_kg": 60, "program": "MG"})
    assert resp.get_json() == {"calories": 2100}


def test_calories_endpoint_validation(client):
    resp = client.post("/api/calories", json={"weight_kg": -1, "program": "MG"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_calories_endpoint_without_body(client):
    assert client.post("/api/calories").status_code == 400


def test_bmi_endpoint(client):
    resp = client.post("/api/bmi", json={"height_cm": 175, "weight_kg": 70})
    assert resp.get_json() == {"bmi": 22.9, "category": "Normal"}


def test_bmi_endpoint_validation(client):
    resp = client.post("/api/bmi", json={"height_cm": 0, "weight_kg": 70})
    assert resp.status_code == 400
    assert "height_cm" in resp.get_json()["error"]


def test_create_client_computes_calories(client):
    resp = client.post("/api/clients", json={"name": "Priya", "weight": 60, "program": "bg"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["program"] == "BG"
    assert body["calories"] == 1560
    assert body["membership_status"] == "Active"


def test_create_client_requires_name(client):
    assert client.post("/api/clients", json={"weight": 60}).status_code == 400


def test_create_client_rejects_unknown_program(client):
    assert client.post("/api/clients", json={"name": "X", "program": "ZZ"}).status_code == 400


def test_create_client_rejects_bad_weight(client):
    resp = client.post("/api/clients", json={"name": "X", "weight": -10, "program": "FL"})
    assert resp.status_code == 400
    assert client.get("/api/clients/X").status_code == 404


def test_create_client_without_program_has_no_calories(client):
    body = client.post("/api/clients", json={"name": "Walk-in", "weight": 70}).get_json()
    assert body["program"] is None and body["calories"] is None


def test_duplicate_client_conflict(client, member):
    assert client.post("/api/clients", json={"name": member}).status_code == 409


def test_list_and_get_client(client, member):
    assert [c["name"] for c in client.get("/api/clients").get_json()] == [member]
    assert client.get(f"/api/clients/{member}").get_json()["calories"] == 1760
    assert client.get("/api/clients/Nobody").status_code == 404


def test_progress_logging_and_average(client, member):
    client.post(f"/api/clients/{member}/progress", json={"week": "W1", "adherence": 80})
    client.post(f"/api/clients/{member}/progress", json={"week": "W2", "adherence": 90})
    data = client.get(f"/api/clients/{member}/progress").get_json()
    assert len(data["entries"]) == 2
    assert data["average_adherence"] == 85.0


def test_progress_empty_has_no_average(client, member):
    assert client.get(f"/api/clients/{member}/progress").get_json()["average_adherence"] is None


def test_progress_validation(client, member):
    url = f"/api/clients/{member}/progress"
    assert client.post(url, json={"week": "W1", "adherence": 150}).status_code == 400
    assert client.post(url, json={"adherence": 50}).status_code == 400
    missing = client.post("/api/clients/Nobody/progress", json={"week": "W1", "adherence": 50})
    assert missing.status_code == 404


def test_workout_logging(client, member):
    url = f"/api/clients/{member}/workouts"
    resp = client.post(url, json={"workout_type": "Strength", "duration_min": 45, "date": "2026-03-01"})
    assert resp.status_code == 201
    workouts = client.get(url).get_json()
    assert workouts[0]["workout_type"] == "Strength"


def test_workout_validation(client, member):
    url = f"/api/clients/{member}/workouts"
    assert client.post(url, json={"duration_min": 30}).status_code == 400
    assert client.post(url, json={"workout_type": "Cardio", "duration_min": 0}).status_code == 400
    assert client.post(url, json={"workout_type": "Cardio", "duration_min": "30"}).status_code == 400
    assert client.post(url, json={"workout_type": "Cardio", "duration_min": True}).status_code == 400
    assert client.get("/api/clients/Nobody/workouts").status_code == 404


def test_workout_defaults_to_today(client, member):
    url = f"/api/clients/{member}/workouts"
    resp = client.post(url, json={"workout_type": "Mobility", "duration_min": 20})
    assert resp.get_json()["date"] == date.today().isoformat()


def test_membership_active_and_expired(client):
    future = (date.today() + timedelta(days=30)).isoformat()
    past = (date.today() - timedelta(days=1)).isoformat()
    client.post("/api/clients", json={"name": "Active", "membership_end": future})
    client.post("/api/clients", json={"name": "Lapsed", "membership_end": past})
    assert client.get("/api/clients/Active/membership").get_json()["status"] == "Active"
    assert client.get("/api/clients/Lapsed/membership").get_json()["status"] == "Expired"
    assert client.get("/api/clients/Nobody/membership").status_code == 404


def test_membership_with_unparseable_date_keeps_stored_status(client):
    client.post("/api/clients", json={"name": "Odd", "membership_end": "next month"})
    body = client.get("/api/clients/Odd/membership").get_json()
    assert body == {"client": "Odd", "status": "Active", "renewal_date": "next month"}


def test_workout_rejects_invalid_date(client, member):
    url = f"/api/clients/{member}/workouts"
    resp = client.post(url, json={"workout_type": "Cardio", "duration_min": 30, "date": "banana"})
    assert resp.status_code == 400
