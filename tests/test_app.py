from uuid import uuid4

from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_seeded_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9


def test_get_activities_items_have_expected_shape():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


def test_signup_for_activity_success():
    email = f"test-{uuid4()}@example.com"

    signup_response = client.post(f"/activities/Chess Club/signup?email={email}")
    assert signup_response.status_code == 200
    assert signup_response.json()["message"] == f"Signed up {email} for Chess Club"

    activities_response = client.get("/activities")
    assert activities_response.status_code == 200
    assert email in activities_response.json()["Chess Club"]["participants"]

    cleanup_response = client.delete(f"/activities/Chess Club/signup?email={email}")
    assert cleanup_response.status_code == 200


def test_signup_for_activity_duplicate_rejected():
    response = client.post(
        "/activities/Chess Club/signup?email=michael@mergington.edu"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_unknown_activity_returns_not_found():
    response = client.post(
        "/activities/Fake Club/signup?email=test@example.com"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_from_activity_success():
    email = f"remove-{uuid4()}@example.com"

    signup_response = client.post(f"/activities/Chess Club/signup?email={email}")
    assert signup_response.status_code == 200

    unregister_response = client.delete(f"/activities/Chess Club/signup?email={email}")
    assert unregister_response.status_code == 200
    assert unregister_response.json()["message"] == f"Unregistered {email} from Chess Club"

    activities_response = client.get("/activities")
    assert activities_response.status_code == 200
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_not_signed_up_returns_not_found():
    email = f"missing-{uuid4()}@example.com"

    response = client.delete(f"/activities/Chess Club/signup?email={email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"


def test_unregister_unknown_activity_returns_not_found():
    response = client.delete(
        "/activities/Fake Club/signup?email=test@example.com"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
