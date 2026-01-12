"""
Test script for the premium intake flow
Tests the 5-step intake process and portal redirect
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_intake_flow():
    print("=" * 60)
    print("Testing Premium Intake Flow")
    print("=" * 60)

    # Create a session to maintain cookies
    session = requests.Session()

    # Step 1: Login as test user
    print("\n[1/7] Logging in as test user...")
    login_data = {
        'email': 'tester@usefylr.app',
        'password': 'Password123!'
    }

    response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=True)

    if response.status_code == 200 or response.status_code == 302:
        print("   SUCCESS: Logged in successfully")
    else:
        print(f"   FAILED: Login failed with status {response.status_code}")
        return False

    # Step 2: Access intake page
    print("\n[2/7] Accessing intake page...")
    response = session.get(f"{BASE_URL}/intake")

    if response.status_code == 200:
        print("   SUCCESS: Intake page loaded")
    else:
        print(f"   FAILED: Could not access intake page (status {response.status_code})")
        return False

    # Step 3: Submit step 1 data (Identity)
    print("\n[3/7] Submitting Step 1 (Identity)...")
    step1_data = {
        'step': 1,
        'data': {
            'name': 'Test User',
            'industry': 'Software Development'
        }
    }

    response = session.post(
        f"{BASE_URL}/intake",
        json=step1_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   SUCCESS: Step 1 completed, next step: {result.get('next_step')}")
        else:
            print(f"   FAILED: Step 1 returned unexpected response: {result}")
            return False
    else:
        print(f"   FAILED: Step 1 failed with status {response.status_code}")
        return False

    # Step 4: Submit step 2 data (Entity)
    print("\n[4/7] Submitting Step 2 (Entity Type)...")
    step2_data = {
        'step': 2,
        'data': {
            'entity_type': 'llc'
        }
    }

    response = session.post(
        f"{BASE_URL}/intake",
        json=step2_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   SUCCESS: Step 2 completed, next step: {result.get('next_step')}")
        else:
            print(f"   FAILED: Step 2 returned unexpected response: {result}")
            return False
    else:
        print(f"   FAILED: Step 2 failed with status {response.status_code}")
        return False

    # Step 5: Submit step 3 data (Revenue)
    print("\n[5/7] Submitting Step 3 (Annual Revenue)...")
    step3_data = {
        'step': 3,
        'data': {
            'revenue': 150000
        }
    }

    response = session.post(
        f"{BASE_URL}/intake",
        json=step3_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   SUCCESS: Step 3 completed, next step: {result.get('next_step')}")
        else:
            print(f"   FAILED: Step 3 returned unexpected response: {result}")
            return False
    else:
        print(f"   FAILED: Step 3 failed with status {response.status_code}")
        return False

    # Step 6: Submit step 4 data (Complexity)
    print("\n[6/7] Submitting Step 4 (Complexity Flags)...")
    step4_data = {
        'step': 4,
        'data': {
            'complexity': ['contractors', 'multiple_states']
        }
    }

    response = session.post(
        f"{BASE_URL}/intake",
        json=step4_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"   SUCCESS: Step 4 completed, next step: {result.get('next_step')}")
        else:
            print(f"   FAILED: Step 4 returned unexpected response: {result}")
            return False
    else:
        print(f"   FAILED: Step 4 failed with status {response.status_code}")
        return False

    # Step 7: Submit step 5 data (Final step - should redirect to portal)
    print("\n[7/7] Submitting Step 5 (Finalization)...")
    step5_data = {
        'step': 5,
        'data': {}
    }

    response = session.post(
        f"{BASE_URL}/intake",
        json=step5_data,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('redirect') == '/portal':
            print(f"   SUCCESS: Step 5 completed, redirect to: {result.get('redirect')}")
        else:
            print(f"   FAILED: Step 5 did not return portal redirect: {result}")
            return False
    else:
        print(f"   FAILED: Step 5 failed with status {response.status_code}")
        return False

    # Verify portal access
    print("\n[BONUS] Verifying portal access...")
    response = session.get(f"{BASE_URL}/portal")

    if response.status_code == 200:
        print("   SUCCESS: Portal page accessible")
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return True
    else:
        print(f"   WARNING: Could not access portal (status {response.status_code})")
        print("\n" + "=" * 60)
        print("TESTS COMPLETED WITH WARNINGS")
        print("=" * 60)
        return True

if __name__ == "__main__":
    try:
        test_intake_flow()
    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
