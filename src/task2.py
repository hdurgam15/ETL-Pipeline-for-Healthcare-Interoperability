import json
import requests

OPENEMR_BASE = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_BASE = "http://159.203.105.138:8080/fhir"
TERMINOLOGY_SERVER_BASE_URL = "http://159.203.121.13:8080/v1/snomed"

def load_access_token():
    with open("data/access_token.json") as f:
        return json.load(f)["access_token"]


def get_headers_openemr():
    return {
        "Authorization": f"Bearer {load_access_token()}",
        "Accept": "application/fhir+json"
    }


def get_headers_primary():
    return {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }

def load_task1_ids():
    data = {}
    with open("data/new_primary_care_patient_id.txt") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=")
                data[key] = value.strip('"')
    return data

#Extraction of patient records from OpenEMR using search parameters
def get_patients(name=None, gender=None):
    url = f"{OPENEMR_BASE}/Patient"
    params = []

    if name:
        params.append(f"name={name}")
    if gender:
        params.append(f"gender={gender}")

    if params:
        url += "?" + "&".join(params)

    res = requests.get(url, headers=get_headers_openemr())
    res.raise_for_status()
    return res.json()

#Extracting conditions of a patient from OpenEMR
def get_conditions_for_patient(patient_id):
    url = f"{OPENEMR_BASE}/Condition?patient={patient_id}"
    res = requests.get(url, headers=get_headers_openemr())
    res.raise_for_status()
    bundle = res.json()
    entries = bundle.get("entry", [])
    print(f"Retrieved {len(entries)} conditions for patient {patient_id}")
    return [entry["resource"] for entry in entries]

#Extract snomed concept id
def get_snomed_concept_id(condition_resource):
    return condition_resource["code"]["coding"][0]["code"]

#Extract child concept id using the Terminology Server
def get_child_concept(concept_id):
    url = f"{TERMINOLOGY_SERVER_BASE_URL}/search?constraint=<! {concept_id}"
    resp = requests.get(url)
    resp.raise_for_status()

    data = resp.json()
    if data:
        child = data[0]
        return child["conceptId"], child["term"], child["preferredTerm"]
    return None, None, None

#load the child condition into primary care server
def create_primary_care_condition(new_patient_id, concept_id, term, preferred_term):
    url = f"{PRIMARY_CARE_BASE}/Condition"

    condition_resource = {
        "resourceType": "Condition",
        "meta": {
            "profile": [
                "https://dentalinformatics.online/B581/StructureDefinition/condition-profile"
            ]
        },
        "clinicalStatus": {
            "coding": [
                {"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}
            ]
        },"category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "undefined",
                "display": "Undefined"
            }]
        }],
        "verificationStatus": {
            "coding": [{"system": "http://hl7.org/fhir/condition-ver-status", "code": "confirmed"}]
        },
        "bodySite": [{
            "coding": [{"system": "http://snomed.info/sct", "code": "undefined", "display": "undefined"}],
            "text": "Undefined"
        }],
        "severity": {
            "coding": [{"system": "http://snomed.info/sct", "code": "Undefined", "display": "Undefined"}]
        },
        "code": {
            "coding": [
                {"system": "http://snomed.info/sct", "code": str(concept_id), "display": preferred_term}
            ],
            "text": term
        },
        "subject": {"reference": f"Patient/{new_patient_id}"},
        "onsetDateTime": "2024-01-01"
    }

    resp = requests.post(url, json=condition_resource)
    resp.raise_for_status()
    created = resp.json()
    print("Created Primary Care Condition ID:", created.get("id"))
    return created

def main():
    # Load stored Task 1 identifiers
    ids = load_task1_ids()
    stored_openemr_id = ids["openemr_patient_id"]
    stored_primary_id = ids["primary_patient_id"]

    print("Stored OpenEMR Patient ID:", stored_openemr_id)
    print("Stored Primary Care Patient ID:", stored_primary_id)

    conditions = get_conditions_for_patient(stored_openemr_id)
    child_concept_id = None
    child_term = None

    for cond in conditions:
        snomed = get_snomed_concept_id(cond)
        child_concept_id, child_term, child_preferredTerm = get_child_concept(snomed)
        if child_concept_id:
            print(f"Using SNOMED {snomed} and its Child {child_concept_id}")
            break

    if child_concept_id is None:
        raise Exception("No valid child SNOMED concept found in any condition")

    create_primary_care_condition(
        new_patient_id=stored_primary_id,
        concept_id=child_concept_id,
        term=child_term,
        preferred_term = child_preferredTerm
    )

    print("Completed Task 2")

if __name__ == "__main__":
    main()
