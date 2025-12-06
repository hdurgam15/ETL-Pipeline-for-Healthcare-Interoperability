import json
import requests

OPENEMR_BASE = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_BASE = "http://159.203.105.138:8080/fhir"
TERMINOLOGY_SERVER = "http://159.203.121.13:8080/v1/snomed"

ID_OUTPUT_FILE = "data/new_primary_care_patient_id.txt"

def load_access_token():
    path = "data/access_token.json"
    with open(path) as f:
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

# Extraction from OpenEMR with name and gender search parameters
def get_patients(name=None, gender=None):
    url = f"{OPENEMR_BASE}/Patient"
    params = []
    if name:
        params.append(f"name={name}")
    if gender:
        params.append(f"gender={gender}")
    if params:
        url += "?" + "&".join(params)
    response = requests.get(url, headers=get_headers_openemr())
    response.raise_for_status()

    data = response.json()
    print("Retrieved:", data.get("total", 0), "patients")
    return data

#Extraction of a patient id
def get_patient_id(patients_data):
    entries = patients_data.get("entry", [])
    if not entries:
        raise Exception("No patient found with given search parameters.")
    return entries[0]["resource"]["id"]

#Extraction of conditions for a patient
def get_conditions_for_patient(patient_id):
    url = f"{OPENEMR_BASE}/Condition?patient={patient_id}"
    response = requests.get(url, headers=get_headers_openemr())
    response.raise_for_status()

    conditions_data = response.json()
    condition_entries = conditions_data.get("entry", [])
    print(f"Retrieved {len(condition_entries)} conditions for patient {patient_id}")
    return [entry["resource"] for entry in condition_entries]

#Extract snomed_id for a condition
def extract_snomed_from_condition(condition_resource):
    coding = condition_resource["code"]["coding"][0]
    snomed_code = coding["code"]
    display = coding.get("display", "")
    return snomed_code, display

#Extract parent condition snomed id
def get_parent_snomed(snomed_code):
    url = f"{TERMINOLOGY_SERVER}/search?constraint=>! {snomed_code}"
    response = requests.get(url)

    if response.status_code != 200:
        print("SNOMED parent lookup failed", response.text)
        return None, None

    try:
        results = response.json()
    except json.JSONDecodeError:
        print("Invalid SNOMED response.")
        return None, None, None

    if not results:
        return None, None, None

    parent = results[0]
    print(parent)
    parent_id = parent["conceptId"]
    parent_term = parent["term"]
    parent_preferredTerm = parent["preferredTerm"]
    return parent_id, parent_term, parent_preferredTerm

#Transformation of FHIR Patient record to primary care patient record
def transform_openemr_patient_to_primary(patient_resource):
    identifiers = patient_resource.get("identifier", [])

    cleaned_identifiers = []
    for id_obj in identifiers:
        cleaned_identifiers.append({
            "use": id_obj.get("use", "official"),
            "type": id_obj.get("type", {}),
            "system": id_obj.get("system", ""),
            "value": id_obj.get("value", "")
        })

    # NAME
    names = patient_resource.get("name", [])
    cleaned_names = []
    for n in names:
        cleaned_names.append({
            "use": n.get("use", "official"),
            "family": n.get("family", ""),
            "given": n.get("given", [])
        })

    # ADDRESS
    addresses = patient_resource.get("address", [])
    cleaned_addresses = []
    for addr in addresses:
        cleaned_addresses.append({
            "use": addr.get("use", "home"),
            "type": addr.get("type", "both"),
            "line": addr.get("line", "Not Available"),
            "city": addr.get("city", "Not Available"),
            "district": addr.get("district", "Not Available"),
            "state": addr.get("state", "Not Available"),
            "postalCode": addr.get("postalCode", "Not Available"),
            "period": addr.get("period", {})
        })


    transformed = {
        "resourceType": "Patient",
        "meta": {
            "profile": [
                "https://dentalinformatics.online/B581/StructureDefinition/patient-profile"
            ]
        },
        "active": patient_resource.get("active", True),
        "name": patient_resource.get("name", "No Name Available"),
        "gender": patient_resource.get("gender"),
        "birthDate": patient_resource.get("birthDate", "dd-mm-yyyy"),
        "address": cleaned_addresses,
        "identifier": patient_resource.get("identifier", "NA"),
        "telecom": patient_resource.get("telecom", "NA"),
        "deceasedBoolean": patient_resource.get("deceasedBoolean", False)
    }
    return transformed

#Loading patient record into Primary Care Server
def create_primary_patient(primary_patient_json):
    url = f"{PRIMARY_CARE_BASE}/Patient"
    response = requests.post(url, headers=get_headers_primary(), json=primary_patient_json)
    response.raise_for_status()
    data = response.json()
    print("Created Primary Care Patient:", data["id"])
    return data["id"]

#Trasnforming and loading condition from FHIR record to Primary Care record
def create_primary_condition(new_patient_id, parent_id, parent_term, parent_preferredTerm):
    url = f"{PRIMARY_CARE_BASE}/Condition"
    condition_resource = {
        "resourceType": "Condition",
        "meta": {
            "profile": [
                "https://dentalinformatics.online/B581/StructureDefinition/condition-profile"
            ]
        },
        "clinicalStatus": {
            "coding": [{"system": "http://hl7.org/fhir/condition-clinical", "code": "active"}]
        },
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "undefined",
                "display": "Undefined"
            }]
        }],
        "verificationStatus": {
            "coding": [{"system": "http://hl7.org/fhir/condition-ver-status", "code": "confirmed"}]
        },
        "code": {
            "coding": [{"system": "http://snomed.info/sct", "code": parent_id, "display": parent_preferredTerm}],
            "text": parent_term
        },
        "bodySite": [{
            "coding": [{"system": "http://snomed.info/sct", "code": "undefined", "display": "undefined"}],
            "text": "Undefined"
        }],
        "severity": {
            "coding": [{"system": "http://snomed.info/sct", "code": "Undefined", "display": "Undefined"}]
        },
        "subject": {"reference": f"Patient/{new_patient_id}"},
        "onsetDateTime": "2024-01-01"
    }
    response = requests.post(url, headers=get_headers_primary(), json=condition_resource)
    response.raise_for_status()
    data = response.json()
    print("Created Primary Care Condition:", data.get("id"))
    return data.get("id")

def main():

    # Extraction
    patients_data = get_patients(name="Smith", gender="male")
    openemr_patient_id = get_patient_id(patients_data)
    print("OpenEMR Patient ID:", openemr_patient_id)

    conditions = get_conditions_for_patient(openemr_patient_id)
    parent_id = None
    parent_term = None
    snomed_code = None
    snomed_term = None

    for cond in conditions:
        snomed_code, snomed_term = extract_snomed_from_condition(cond)
        parent_id, parent_term, parent_preferredTerm = get_parent_snomed(snomed_code)

        if parent_id is not None:
            print(f"Selected Condition SNOMED code is {snomed_code} and Parent ID is {parent_id}")
            break

    if parent_id is None:
        raise Exception("No valid parent SNOMED term found in any condition.")

    #Transform
    openemr_patient_resource = patients_data["entry"][0]["resource"]
    transformed_patient = transform_openemr_patient_to_primary(openemr_patient_resource)

    #Load
    primary_patient_id = create_primary_patient(transformed_patient)
    primary_condition_id = create_primary_condition(primary_patient_id, parent_id, parent_term, parent_preferredTerm)

    #Fetching Patient Name
    patient_name = openemr_patient_resource["name"][0]["text"] if "text" in openemr_patient_resource["name"][0] else \
        openemr_patient_resource["name"][0]["family"] + ", " + \
        openemr_patient_resource["name"][0]["given"][0]

    # Save ID for next tasks
    with open(ID_OUTPUT_FILE, "w") as f:
        f.write('openemr_patient_id="{id}"\n'.format(id=openemr_patient_id))
        f.write('primary_patient_id="{id}"\n'.format(id=primary_patient_id))
        f.write('patient_name="{name}"\n'.format(name=patient_name))
        f.write('snomed_code="{snomed_code}"\n'.format(snomed_code=snomed_code))
        f.write('snomed_term="{snomed_term}"'.format(snomed_term=snomed_term))

    print("Task 1 completed. Patient ID saved to:", ID_OUTPUT_FILE)


if __name__ == "__main__":
    main()
