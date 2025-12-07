import json
import requests
from pathlib import Path
from src.registration import data_dir

# API URLs
OPENEMR_BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_BASE_URL = "http://159.203.105.138:8080/fhir"


def get_access_token():
    """Load access token from file"""
    file_path = Path(data_dir / "access_token.json")
    with open(file_path, 'r') as f:
        data = json.load(f)
        return data.get("access_token")


def get_openemr_headers():
    """Create headers with access token for OpenEMR"""
    token = get_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/fhir+json"
    }


def check_procedure(patient_id):
    """
    Step 1: Check if Procedure exists in OpenEMR
    """
    print("\n=== STEP 1: CHECK FOR PROCEDURE ===")

    url = f"{OPENEMR_BASE_URL}/Procedure?patient={patient_id}"
    print(f"URL: {url}")
    print(f"Searching for Procedures...")

    try:
        response = requests.get(url, headers=get_openemr_headers(), timeout=10)
        data = response.json()

        total = data.get('total', 0)
        print(f"Found {total} Procedures")

        if 'entry' in data and len(data['entry']) > 0:
            procedure = data['entry'][0]['resource']
            print(f"✓ Procedure exists")
            print(f"Procedure ID: {procedure['id']}")
            return procedure
        else:
            print("✗ No Procedure found in OpenEMR")
            return None

    except requests.exceptions.JSONDecodeError:
        print("✗ Invalid response from OpenEMR (empty or non-JSON)")
        return None
    except requests.exceptions.Timeout:
        print("✗ Request timeout")
        return None
    except Exception as e:
        print(f"✗ Error checking procedure: {e}")
        return None


def create_procedure(patient_id):
    """
    Step 2: Create Procedure on Primary Care EHR
    """
    print("\n=== STEP 2: CREATE PROCEDURE ===")

    procedure = {
        "resourceType": "Procedure",
        "text": {
            "status": "generated",
            "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Appendectomy procedure</p></div>"
        },
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-procedure"]
        },
        "status": "completed",
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "80146002",
                "display": "Appendectomy"
            }],
            "text": "Appendectomy"
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "performedDateTime": "2024-11-20T14:00:00Z"
    }

    url = f"{PRIMARY_CARE_BASE_URL}/Procedure"
    headers = {"Content-Type": "application/fhir+json"}

    print(f"Creating Procedure...")
    print(f"Procedure: Appendectomy (SNOMED: 80146002)")
    print(f"Status: completed")
    print(f"Date: 2024-11-20")

    try:
        response = requests.post(url, headers=headers, json=procedure, timeout=10)
        response.raise_for_status()

        created_procedure = response.json()
        procedure_id = created_procedure['id']
        print(f"✓ Procedure created with ID: {procedure_id}")

        return created_procedure

    except requests.exceptions.Timeout:
        print("✗ Request timeout")
        return None
    except Exception as e:
        print(f"✗ Error creating procedure: {e}")
        return None


def main():
    """Main execution for Task 4"""
    print("\n" + "=" * 60)
    print("CODING TASK 4: PROCEDURE")
    print("=" * 60)

    # Get patient from Task 1
    openemr_patient_id = "9d035909-a26e-4271-ab8f-e57ca59d2286"

    # Step 1: Check if procedure exists in OpenEMR
    procedure = check_procedure(openemr_patient_id)

    # Step 2: Create procedure on Primary Care EHR
    # Load Task 1 results to get Primary Care patient ID
    results_file = Path(data_dir / "task1_results.json")

    try:
        with open(results_file, 'r') as f:
            task1_results = json.load(f)

        primary_care_patient_id = task1_results['patient_id']

    except FileNotFoundError:
        print("✗ Task 1 results file not found. Please run Task 1 first.")
        return
    except Exception as e:
        print(f"✗ Error reading Task 1 results: {e}")
        return

    new_procedure = create_procedure(primary_care_patient_id)

    if not new_procedure:
        print("\n✗ Failed to create procedure")
        return

    # Summary
    print("\n" + "=" * 60)
    print("✓ TASK 4 COMPLETED")
    print("=" * 60)
    print(f"OpenEMR Patient ID: {openemr_patient_id}")
    print(f"Primary Care Patient ID: {primary_care_patient_id}")
    print(f"Procedure: Appendectomy")
    print(f"New Procedure ID: {new_procedure['id']}")
    print("=" * 60)

    # Save results
    results = {
        "patient_id": primary_care_patient_id,
        "procedure_id": new_procedure['id'],
        "procedure_code": "80146002",
        "procedure_name": "Appendectomy"
    }

    results_file = Path(data_dir / "task4_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {results_file}")


if __name__ == '__main__':
    main()