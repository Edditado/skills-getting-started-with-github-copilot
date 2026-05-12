import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

initial_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: restore the in-memory activities state before every test
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_index(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    # Arrange
    url = "/activities"

    # Act
    response = client.get(url)
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert "Chess Club" in payload
    assert payload["Chess Club"]["max_participants"] == 12
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Programming Class"
    participant_email = "alex@mergington.edu"
    path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.post(path, params={"email": participant_email})
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert "Signed up alex@mergington.edu for Programming Class" in payload["message"]
    assert participant_email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == 3


def test_signup_duplicate_participant_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    participant_email = "michael@mergington.edu"
    path = f"/activities/{quote(activity_name)}/signup"

    # Act
    response = client.post(path, params={"email": participant_email})
    payload = response.json()

    # Assert
    assert response.status_code == 400
    assert payload["detail"] == "Student already signed up for this activity"


def test_remove_participant_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    participant_email = "michael@mergington.edu"
    path = f"/activities/{quote(activity_name)}/participant"

    # Act
    response = client.delete(path, params={"email": participant_email})
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert payload["message"] == "Removed michael@mergington.edu from Chess Club"
    assert participant_email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == 1


def test_remove_missing_participant_returns_404(client):
    # Arrange
    activity_name = "Programming Class"
    participant_email = "unknown@mergington.edu"
    path = f"/activities/{quote(activity_name)}/participant"

    # Act
    response = client.delete(path, params={"email": participant_email})
    payload = response.json()

    # Assert
    assert response.status_code == 404
    assert payload["detail"] == "Participant not found for this activity"
