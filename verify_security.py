import requests
import time
import sys
import os

BASE_URL = "http://localhost:8000"
FILE_PATH = "Ponto1.pdf"

def wait_for_api():
    print("Waiting for API to be available...")
    for _ in range(30):
        try:
            response = requests.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print("API is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    print("API failed to start.")
    return False

def test_security():
    # 1. Try to access without token
    print("Testing unauthorized access...")
    if not os.path.exists(FILE_PATH):
        print(f"File {FILE_PATH} not found.")
        return False
        
    with open(FILE_PATH, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/convert", files=files)
    
    if response.status_code != 401:
        print(f"Failed: Expected 401, got {response.status_code}")
        return False
    print("Unauthorized access blocked correctly.")

    # 2. Login
    print("Testing login...")
    response = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "secret"})
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return False
    
    token = response.json().get("access_token")
    print("Login successful, token received.")
    
    # 3. Access with token
    print("Testing authorized access...")
    headers = {"Authorization": f"Bearer {token}"}
    with open(FILE_PATH, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/convert", files=files, headers=headers)
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return False
        
    task_id = response.json().get("task_id")
    print(f"Task ID: {task_id}")
    
    # 4. Check result with token
    print("Waiting for result...")
    for _ in range(60):
        response = requests.get(f"{BASE_URL}/result/{task_id}", headers=headers)
        
        content_type = response.headers.get("content-type", "")
        if "text/csv" in content_type or response.text.startswith("Data;"):
            print(f"Conversion successful! Content-Type: {content_type}")
            return True

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
             # Ignore non-json if not csv yet (shouldn't happen often but safe to ignore)
             pass
        else:
            status = data.get("status")
            print(f"Status: {status}")
            
            if status == "failed":
                print(f"Task failed: {data.get('error')}")
                return False
            
        time.sleep(2)
        
    print("Timeout waiting for result.")
    return False

if __name__ == "__main__":
    if wait_for_api():
        if test_security():
            print("Security Verification PASSED")
            sys.exit(0)
        else:
            print("Security Verification FAILED")
            sys.exit(1)
    else:
        sys.exit(1)
