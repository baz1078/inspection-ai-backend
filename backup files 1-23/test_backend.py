import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_health():
    print("\n" + "="*60)
    print("Testing: Health Check")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("SUCCESS: Backend is running!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"ERROR: Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend")
        print("Make sure 'python app.py' is running")
        return False

def main():
    print("\n" + "="*60)
    print("Inspection AI Backend - Quick Test")
    print("="*60)
    
    if not test_health():
        print("\nBackend is not running")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("Backend is working!")
    print("="*60)

if __name__ == '__main__':
    main()
