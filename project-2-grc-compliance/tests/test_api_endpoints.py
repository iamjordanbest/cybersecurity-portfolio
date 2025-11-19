#!/usr/bin/env python3
"""
Test API Endpoints

Starts the API and tests each endpoint.
"""

import subprocess
import time
import requests
import sys

def test_api():
    print("\n" + "="*70)
    print("GRC Analytics API - Endpoint Testing")
    print("="*70)
    
    # Start API in background
    print("\nStarting API server...")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"API process started with PID: {api_process.pid}")
    
    try:
        # Wait for API to start
        print("Waiting for API to become healthy...")
        health_url = "http://127.0.0.1:8000/health"
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(health_url)
                if response.status_code == 200:
                    print("API is healthy!\n")
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        else:
            print("[FAIL] Timeout waiting for API to start")
            return False

        # Test endpoints
        base_url = "http://127.0.0.1:8000/api/v1"
        tests_passed = 0
        tests_failed = 0
        
        # Test 1: Root endpoint
        print("Testing: GET /")
        try:
            response = requests.get("http://127.0.0.1:8000/")
            if response.status_code == 200:
                print(f"  [OK] Status: {response.status_code}")
                tests_passed += 1
            else:
                print(f"  [FAIL] Status: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            tests_failed += 1
        
        # Test 2: Risk summary
        print("\nTesting: GET /api/v1/risk/summary")
        try:
            response = requests.get(f"{base_url}/risk/summary")
            if response.status_code == 200:
                data = response.json()
                print(f"  [OK] Status: {response.status_code}")
                print(f"  Frameworks returned: {len(data)}")
                tests_passed += 1
            else:
                print(f"  [FAIL] Status: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            tests_failed += 1
        
        # Test 3: Frameworks list
        print("\nTesting: GET /api/v1/frameworks")
        try:
            response = requests.get(f"{base_url}/frameworks")
            if response.status_code == 200:
                data = response.json()
                print(f"  [OK] Status: {response.status_code}")
                print(f"  Frameworks: {len(data)}")
                tests_passed += 1
            else:
                print(f"  [FAIL] Status: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            tests_failed += 1
        
        # Test 4: Controls list
        print("\nTesting: GET /api/v1/controls?limit=5")
        try:
            response = requests.get(f"{base_url}/controls?limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"  [OK] Status: {response.status_code}")
                print(f"  Controls returned: {len(data)}")
                tests_passed += 1
            else:
                print(f"  [FAIL] Status: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            tests_failed += 1
        
        # Test 5: Risk calculate endpoint
        print("\nTesting: POST /api/v1/risk/calculate")
        try:
            payload = {
                "control_id": "AC-1",
                "status": "fail",
                "control_weight": 2.0,
                "business_impact": "high"
            }
            response = requests.post(f"{base_url}/risk/calculate", json=payload)
            if response.status_code == 200:
                data = response.json()
                print(f"  [OK] Status: {response.status_code}")
                print(f"  Risk Score: {data.get('risk_score')}")
                tests_passed += 1
            else:
                print(f"  [FAIL] Status: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            tests_failed += 1
        
        # Summary
        print("\n" + "="*70)
        print(f"Tests Passed: {tests_passed}/{tests_passed + tests_failed}")
        print("="*70)
        
        return tests_failed == 0
        
    except Exception as e:
        print(f"\n[FAIL] Exception occurred: {e}")
        return False
        
    finally:
        # Cleanup
        print("\nStopping API process...")
        api_process.terminate()
        try:
            api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_process.kill()
        print("API process stopped")

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
