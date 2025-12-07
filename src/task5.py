import json
import requests
from datetime import datetime
from hl7apy.core import Message

OPENEMR_BASE = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
HERMES_BASE = "http://159.203.121.13:8080/v1/snomed/concepts"

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

# Extract Patient record from OpenEMR
def get_patient(openemr_patient_id):
    url = f"{OPENEMR_BASE}/Patient/{openemr_patient_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

# Extract Patient Conditions
def get_patient_conditions(openemr_patient_id):
    url = f"{OPENEMR_BASE}/Condition?patient={openemr_patient_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    bundle = resp.json()
    entries = bundle.get("entry", [])

    if not entries:
        raise Exception("No conditions found for this patient in OpenEMR")

    condition = entries[0]["resource"]
    coding = condition["code"]["coding"][0]

    snomed_code = coding["code"]
    snomed_term = coding.get("display", "")

    return snomed_code, snomed_term

# Extract snomed using concept id
def get_extended_snomed(concept_id):
    url = f"{HERMES_BASE}/{concept_id}/extended"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

# Extract ICD Mapping using refset
def get_icd_mapping(concept_id, refset_id):
    url = f"{HERMES_BASE}/{concept_id}/map/{refset_id}"
    resp = requests.get(url)
    resp.raise_for_status()

    mappings = resp.json()

    if not mappings:
        return "UNKNOWN", "No ICD mapping available"

    m = mappings[0]
    icd_code = m["mapTarget"]
    icd_display = m.get("mapTargetName", "ICD-10 Term")

    return icd_code, icd_display

# Build HL7 ADT Message
def create_adt_message(patient, snomed_code, snomed_term, icd_code, icd_display):
    msg = Message("ADT_A01")

    msg.msh.msh_1 = "|"
    msg.msh.msh_2 = "^~\\&"
    msg.msh.msh_3 = "OpenEMR"
    msg.msh.msh_4 = "OpenEMR_FHIR"
    msg.msh.msh_5 = "PrimaryCareEHR"
    msg.msh.msh_6 = "HL7_Module"
    msg.msh.msh_7 = datetime.now().strftime("%Y%m%d%H%M%S")
    msg.msh.msh_9 = "ADT^A01"
    msg.msh.msh_10 = "MSG00001"
    msg.msh.msh_11 = "P"
    msg.msh.msh_12 = "2.5"

    name = patient["name"][0]
    family = name.get("family", "")
    given = name.get("given", [""])[0]

    msg.pid.pid_1 = "1"
    msg.pid.pid_3 = patient["id"]
    msg.pid.pid_5 = f"{family}^{given}"
    msg.pid.pid_7 = patient.get("birthDate", "").replace("-", "")
    msg.pid.pid_8 = patient.get("gender", "U")[0].upper()

    if "address" in patient:
        addr = patient["address"][0]
        line = addr.get("line", [""])[0]
        city = addr.get("city", "")
        state = addr.get("state", "")
        postal = addr.get("postalCode", "")
        district = addr.get("district", "")

        msg.pid.pid_11 = f"{line}^{city}^{state}^{postal}^{district}^H"

    msg.pv1.pv1_1 = "1"
    msg.pv1.pv1_2 = "I"

    msg.dg1.dg1_1 = "1"
    msg.dg1.dg1_3 = f"{icd_code}^{icd_display}^I10"
    msg.dg1.dg1_4 = snomed_term

    return msg

# Save HL7 message to text file
def save_message(msg):
    out_path = "data/patient_adt_message.txt"
    with open(out_path, "w") as f:
        f.write(msg.to_er7())
    return out_path


def run_task_5():
    ids = load_task1_ids()
    openemr_patient_id = ids["openemr_patient_id"]
    snomed_code = ids["snomed_code"]

    # Extraction
    patient = get_patient(openemr_patient_id)
    _, snomed_term = get_patient_conditions(openemr_patient_id)

    extended = get_extended_snomed(snomed_code)

    refsets = extended.get("refsets", [])
    if not refsets:
        raise Exception("No SNOMED → ICD mapping refsets available")

    #Picking 1 refset
    refset = refsets[-1]

    icd_code, icd_display = get_icd_mapping(snomed_code, refset)

    # Build message
    msg = create_adt_message(
        patient,
        snomed_code,
        snomed_term,
        icd_code,
        icd_display
    )

    # Save
    hl7_path = save_message(msg)
    print("ADT HL7 message saved to:", hl7_path)


if __name__ == "__main__":
    run_task_5()
