"""
Simple script to test API endpoints
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test health check endpoint."""
    print("\n1. Testing health check...")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_visa_requirements():
    """Test visa requirements endpoint."""
    print("\n2. Testing visa requirements...")
    response = requests.get(
        f"{BASE_URL}/visa/requirements/United States/business",
        params={"nationality": "Indian"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_create_application():
    """Test application creation."""
    print("\n3. Testing application creation...")
    
    application_data = {
        "applicant": {
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "department": "Engineering",
            "position": "Senior Developer",
            "nationality": "Indian",
            "passport_number": "A1234567",
            "passport_expiry": str(date.today() + timedelta(days=730)),
            "date_of_birth": "1990-01-15"
        },
        "visa_type": "business",
        "travel_details": {
            "destination_country": "United States",
            "purpose_of_travel": "Client meeting and training",
            "departure_date": str(date.today() + timedelta(days=30)),
            "return_date": str(date.today() + timedelta(days=40)),
            "duration_days": 10,
            "cities_to_visit": ["New York", "San Francisco"]
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/visa/applications",
        json=application_data
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Application ID: {result.get('id')}")
        print(f"Session ID: {result.get('session_id')}")
        return result.get('id')
    else:
        print(f"Error: {response.text}")
    return None

def test_session_creation():
    """Test session creation."""
    print("\n4. Testing session creation...")
    
    response = requests.post(
        f"{BASE_URL}/sessions/create",
        params={
            "employee_id": "EMP001",
            "destination": "United States"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def run_all_tests():
    """Run all API tests."""
    print("=" * 50)
    print("Travel Visa Desk API Tests")
    print("=" * 50)
    
    try:
        test_health()
        test_visa_requirements()
        application_id = test_create_application()
        test_session_creation()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API")
        print("Make sure the API is running on http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")

if __name__ == "__main__":
    run_all_tests()