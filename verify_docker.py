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

def test_conversion():
    if not os.path.exists(FILE_PATH):
        print(f"File {FILE_PATH} not found.")
        return False

    print(f"Uploading {FILE_PATH}...")
    with open(FILE_PATH, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/convert", files=files)
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return False
    
    task_id = response.json().get("task_id")
    print(f"Task ID: {task_id}")
    
    print("Waiting for result...")
    for _ in range(60):
        response = requests.get(f"{BASE_URL}/result/{task_id}")
        
        content_type = response.headers.get("content-type", "")
        if "text/csv" in content_type or response.text.startswith("Data;"):
            print(f"Conversion successful! Content-Type: {content_type}")
            with open("output.csv", "wb") as f:
                f.write(response.content)
            print("File saved as output.csv")
            return True

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"Unexpected response: {response.text[:100]}")
            return False

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
        if test_conversion():
            print("Verification PASSED")
            sys.exit(0)
        else:
            print("Verification FAILED")
            sys.exit(1)
    else:
        sys.exit(1)
