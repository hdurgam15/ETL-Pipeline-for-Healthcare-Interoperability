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

# Extract procedure details from OpenEMR if one exists
def extract_procedure_from_openemr(openemr_patient_id):
    url = f"{OPENEMR_BASE}/Procedure?subject=Patient/{openemr_patient_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    bundle = resp.json()
    entries = bundle.get("entry", [])

    if not entries:
        return None

    proc = entries[0]["resource"]

    coding = proc.get("code", {}).get("coding", [{}])[0]
    snomed_code = coding.get("code", "")
    snomed_display = coding.get("display", "")

    performed = proc.get("performedDateTime", "2024-12-07T12:00:00Z")

    performer = None
    recorder = None
    note_text = None

    perf_list = proc.get("performer", [])
    if perf_list:
        performer = perf_list[0].get("actor", {})

    recorder = proc.get("recorder", {})

    notes = proc.get("note", "")
    if notes:
        note_text = notes[0].get("text", "")

    return {
        "snomed_code": snomed_code,
        "snomed_display": snomed_display,
        "performed": performed,
        "performer": performer,
        "recorder": recorder,
        "note": note_text
    }

def load_procedure_template(primary_care_patient_id, extracted_proc=None):
    path = "data/add_procedure.json"

    with open(path) as f:
        proc = json.load(f)

    proc["subject"] = {"reference": f"Patient/{primary_care_patient_id}"}

    if extracted_proc:

        proc["code"]["coding"][0]["code"] = extracted_proc["snomed_code"]
        proc["code"]["coding"][0]["display"] = extracted_proc["snomed_display"]
        proc["code"]["text"] = extracted_proc["snomed_display"]

        proc["performedDateTime"] = extracted_proc["performed"]

        if extracted_proc["recorder"]:
            proc["recorder"] = extracted_proc["recorder"]

        if extracted_proc["performer"]:
            proc["performer"] = [
                {"actor": extracted_proc["performer"]}
            ]

        if extracted_proc["note"]:
            proc["note"] = [{"text": extracted_proc["note"]}]

    return proc

# POST procedure to Primary Care Server
def post_procedure(proc_json):
    url = f"{PRIMARY_CARE_BASE}/Procedure"
    response = requests.post(url, json=proc_json)

    if response.status_code not in (200, 201):
        print("Failed to post Procedure")
        print("Status:", response.status_code)
        print(response.text)
        return None

    return response.json()

def run_task_4():
    ids = load_task1_ids()

    openemr_patient_id = ids["openemr_patient_id"]
    primary_care_patient_id = ids["primary_patient_id"]

    print("OpenEMR Patient ID:", openemr_patient_id)
    print("Primary Care Patient ID:", primary_care_patient_id)

    extracted_proc = extract_procedure_from_openemr(openemr_patient_id)

    if extracted_proc:
        print("Procedure exists in OpenEMR — importing details.")
        proc_resource = load_procedure_template(primary_care_patient_id, extracted_proc)
    else:
        print("No Procedure exists in OpenEMR — using template.")
        proc_resource = load_procedure_template(primary_care_patient_id)

    created = post_procedure(proc_resource)

    if created:
        print("Procedure successfully created on Primary Care Server.")
        print("Procedure ID:", created.get("id"))
    else:
        print("Error creating procedure.")

if __name__ == "__main__":
    run_task_4()
