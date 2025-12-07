import json
import requests

OPENEMR_BASE = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_BASE = "http://159.203.105.138:8080/fhir"

def load_access_token():
    with open("data/access_token.json") as f:
        return json.load(f)["access_token"]

ACCESS_TOKEN = load_access_token()

def load_task1_ids():
    data = {}
    with open("data/new_primary_care_patient_id.txt") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=")
                data[k] = v.strip('"')
    return data

# Extract BP Observation from OpenEMR
def extract_openemr_bp(openemr_patient_id):
    url = f"{OPENEMR_BASE}/Observation?subject=Patient/{openemr_patient_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    entries = resp.json().get("entry", [])

    systolic = None
    diastolic = None

    for e in entries:
        obs = e["resource"]
        if obs.get("resourceType") != "Observation":
            continue

        coding = obs.get("code", {}).get("coding", [])
        if not coding:
            continue

        primary_code = coding[0]["code"]

        if primary_code == "85354-9":
            for comp in obs.get("component", []):
                c = comp["code"]["coding"][0]["code"]
                if c == "8480-6":  # systolic
                    systolic = comp["valueQuantity"]["value"]
                if c == "8462-4":  # diastolic
                    diastolic = comp["valueQuantity"]["value"]

        if primary_code == "8480-6":
            systolic = obs["valueQuantity"]["value"]

        if primary_code == "8462-4":
            diastolic = obs["valueQuantity"]["value"]
    return systolic, diastolic

def interpret_bp(value, bp_type):
    if bp_type == "sys":
        if value < 90:
            return "L", "Low"
        elif value <= 120:
            return "N", "Normal"
        else:
            return "H", "High"

    if bp_type == "dia":
        if value < 65:
            return "L", "Low"
        elif value <= 80:
            return "N", "Normal"
        else:
            return "H", "High"

    return "N", "Normal"

# Load BP Observation JSON template from file
def load_bp_template(primary_care_patient_id):
    path = "data/blood_pressure_observation.json"
    with open(path) as f:
        bp = json.load(f)

    bp["subject"] = {"reference": f"Patient/{primary_care_patient_id}"}
    return bp

def build_bp_from_openemr(primary_care_patient_id, sys_value, dia_value):
    bp = load_bp_template(primary_care_patient_id)
    bp["component"][0]["valueQuantity"]["value"] = sys_value
    bp["component"][1]["valueQuantity"]["value"] = dia_value

    sys_code, sys_text = interpret_bp(sys_value, "sys")
    bp["component"][0]["interpretation"] = [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": sys_code,
                    "display": sys_text
                }
            ],
            "text": sys_text
        }
    ]

    # Generate interpretation for diastolic
    dia_code, dia_text = interpret_bp(dia_value, "dia")
    bp["component"][1]["interpretation"] = [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": dia_code,
                    "display": dia_text
                }
            ],
            "text": dia_text
        }
    ]

    return bp

# POST Observation to Primary Care
def post_bp_to_primary_care(bp_json):
    url = f"{PRIMARY_CARE_BASE}/Observation"
    response = requests.post(url, json=bp_json)

    if response.status_code not in (200, 201):
        print("Failed to post BP observation.")
        print("Status:", response.status_code)
        print(response.text)
        return None

    return response.json()

def run_task_3():
    ids = load_task1_ids()

    openemr_patient_id = ids["openemr_patient_id"]
    primary_care_patient_id = ids["primary_patient_id"]

    print("OpenEMR Patient ID:", openemr_patient_id)
    print("Primary Care Patient ID:", primary_care_patient_id)

    # Extract values from OpenEMR
    systolic, diastolic = extract_openemr_bp(openemr_patient_id)

    if systolic is not None and diastolic is not None:
        print("Blood Pressure Observation exists in OpenEMR. Extracting values")
        bp_json = build_bp_from_openemr(primary_care_patient_id, systolic, diastolic)
    else:
        print("No Blood Pressure found in OpenEMR. Using JSON from document")
        systolic = 120
        diastolic = 60
        bp_json = build_bp_from_openemr(primary_care_patient_id, systolic, diastolic)

    created = post_bp_to_primary_care(bp_json)

    if created:
        print("Blood Pressure Observation created in Primary Care.")
        print("Observation ID:", created.get("id"))
    else:
        print("Error creating BP observation.")

if __name__ == "__main__":
    run_task_3()
