"""
Tests for Mergington High School API using AAA (Arrange-Act-Assert) pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture providing a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Test suite for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: No setup needed
        Act: Call GET /activities
        Assert: Returns all activities with expected structure
        """
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class", 
                             "Basketball Team", "Tennis Club", "Drama Club", 
                             "Art Studio", "Robotics Club", "Debate Team"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(activities) == 9
        for activity_name in expected_activities:
            assert activity_name in activities
    
    def test_activity_has_required_fields(self, client):
        """
        Arrange: Expected fields to check
        Act: Call GET /activities
        Assert: Each activity has description, schedule, max_participants, participants
        """
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"{field} missing from {activity_name}"
    
    def test_activity_fields_have_correct_types(self, client):
        """
        Arrange: Expected data types for activity fields
        Act: Call GET /activities
        Assert: Fields have correct types
        """
        # Arrange
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success_new_participant(self, client):
        """
        Arrange: Valid activity name and new email
        Act: POST signup with valid data
        Assert: Participant added and success message returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
        
        # Verify participant was actually added
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Invalid activity name and valid email
        Act: POST signup with non-existent activity
        Assert: Returns 404 Not Found
        """
        # Arrange
        invalid_activity = "NonexistentClub"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_participant_returns_400(self, client):
        """
        Arrange: Activity and email already in participants list
        Act: POST signup with already-registered email
        Assert: Returns 400 Bad Request
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_different_activities(self, client):
        """
        Arrange: Single student email and multiple different activities
        Act: POST signup for same email to different activities
        Assert: Student successfully added to all activities
        """
        # Arrange
        student_email = "versatile@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Drama Club"]
        
        # Act
        for activity_name in activities_to_join:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": student_email}
            )
            assert response.status_code == 200
        
        # Assert
        all_activities = client.get("/activities").json()
        for activity_name in activities_to_join:
            assert student_email in all_activities[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success_removes_participant(self, client):
        """
        Arrange: Activity with existing participant
        Act: DELETE unregister with valid activity and registered email
        Assert: Participant removed and success message returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Existing participant
        
        # Verify participant exists before test
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email in response.json()["message"]
        
        # Verify participant was actually removed
        activities_after = client.get("/activities").json()
        assert email not in activities_after[activity_name]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Invalid activity name and valid email
        Act: DELETE unregister with non-existent activity
        Assert: Returns 404 Not Found
        """
        # Arrange
        invalid_activity = "NonexistentClub"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_unregistered_participant_returns_400(self, client):
        """
        Arrange: Valid activity but email not in participants
        Act: DELETE unregister with non-registered email
        Assert: Returns 400 Bad Request
        """
        # Arrange
        activity_name = "Chess Club"
        unregistered_email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": unregistered_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_signup_then_unregister_workflow(self, client):
        """
        Arrange: A new student and an activity
        Act: Sign up, verify, then unregister
        Assert: Student successfully added and removed
        """
        # Arrange
        activity_name = "Tennis Club"
        email = "workflow@mergington.edu"
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert - Signup successful
        assert signup_response.status_code == 200
        activities_after_signup = client.get("/activities").json()
        assert email in activities_after_signup[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert - Unregister successful
        assert unregister_response.status_code == 200
        activities_after_unregister = client.get("/activities").json()
        assert email not in activities_after_unregister[activity_name]["participants"]


class TestRootEndpoint:
    """Test suite for GET / endpoint"""
    
    def test_root_redirects_to_static_home(self, client):
        """
        Arrange: No setup needed
        Act: Call GET /
        Assert: Returns redirect response to /static/index.html
        """
        # Arrange
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
