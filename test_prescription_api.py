#!/usr/bin/env python3
"""
Test script for prescription creation API
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8001"
USERNAME = "doctor1"
PASSWORD = "doctor123"

def test_prescription_creation():
    print("🧪 Testing Prescription Creation API...")
    
    # Step 1: Login
    print("📝 Step 1: Login...")
    login_url = f"{BASE_URL}/api/auth/login/"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        auth_data = response.json()
        token = auth_data.get('access_token')
        print(f"✅ Login successful, token: {token[:20]}...")
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Get sample data
    print("📊 Step 2: Getting sample data...")
    
    # Get patients
    patients_response = requests.get(f"{BASE_URL}/api/patients/", headers=headers)
    if patients_response.status_code == 200:
        patients = patients_response.json()
        if isinstance(patients, dict) and 'results' in patients:
            patients = patients['results']
        patient_id = patients[0]['id'] if patients else None
        print(f"✅ Found patient: {patients[0]['full_name'] if patients else 'None'}")
    else:
        print(f"❌ Failed to get patients: {patients_response.status_code}")
        return
    
    # Get drugs
    drugs_response = requests.get(f"{BASE_URL}/api/drugs/", headers=headers)
    if drugs_response.status_code == 200:
        drugs = drugs_response.json()
        if isinstance(drugs, dict) and 'results' in drugs:
            drugs = drugs['results']
        drug_id = drugs[0]['id'] if drugs else None
        print(f"✅ Found drug: {drugs[0]['name'] if drugs else 'None'}")
    else:
        print(f"❌ Failed to get drugs: {drugs_response.status_code}")
        return
    
    # Step 3: Test prescription creation
    print("🏥 Step 3: Creating prescription...")
    
    prescription_data = {
        "patient": patient_id,
        "doctor": 1,  # Using doctor profile ID 1
        "prescription_type": "OUTPATIENT",
        "diagnosis": "Test diagnosis from API",
        "notes": "Test notes",
        "special_instructions": "Test special instructions",
        "items": [
            {
                "drug": drug_id,
                "quantity": 10,
                "dosage_per_time": "1 viên",
                "frequency": "TID",
                "route": "PO",
                "duration_days": 7,
                "instructions": "Uống sau ăn"
            }
        ]
    }
    
    print(f"📤 Sending prescription data:")
    print(json.dumps(prescription_data, indent=2))
    
    create_url = f"{BASE_URL}/api/prescriptions/"
    response = requests.post(create_url, json=prescription_data, headers=headers)
    
    print(f"📥 Response: {response.status_code}")
    print(f"📄 Response body: {response.text}")
    
    if response.status_code == 201:
        print("✅ Prescription created successfully!")
        prescription = response.json()
        print(f"📋 Prescription ID: {prescription.get('id')}")
        print(f"📋 Prescription Number: {prescription.get('prescription_number')}")
    else:
        print(f"❌ Prescription creation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"💥 Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"💥 Error text: {response.text}")

if __name__ == "__main__":
    test_prescription_creation()
