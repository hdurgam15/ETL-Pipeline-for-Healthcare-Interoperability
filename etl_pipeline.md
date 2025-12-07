---
title: "ETL Pipeline Documentation"
layout: default
---
# ETL Project

[Home](index.md) | [Team Contributions](team_contributions.md) | [Insights](insights.md) | [Presentation](presentation.md)

## ETL Pipeline Documentation  
A detailed walkthrough of all five ETL tasks completed in this project.

---

## 1. Overview of the ETL Pipeline

This project implements a complete **Extract → Transform → Load** workflow for integrating healthcare data from **OpenEMR** into a **Primary Care FHIR Server**, followed by generating **HL7 v2 ADT messages** for legacy interoperability.

The ETL pipeline uses:

- **FHIR REST APIs** for patient, condition, procedure, and observation data  
- **Hermes Terminology Server** for SNOMED CT parent/child queries and ICD-10 mapping  
- **Python** (`requests`, `json`, `hl7apy`) to orchestrate all tasks  
- **HL7 v2** to produce legacy-compatible messages  

---

## 2. Extraction

### 2.1 API Endpoints Used

| System | Endpoint Base URL |
|--------|-------------------|
| OpenEMR FHIR Server | `https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir` |
| Primary Care FHIR Server | `http://159.203.105.138:8080/fhir` |
| Hermes Terminology Server | `http://159.203.121.13:8080/v1/snomed` |

---

### 2.2 Authentication & Authorization

All extraction calls to OpenEMR use a Bearer token for Authorization stored in:
```
data/access_token.json
```
Example:

```json
{
  "access_token": "<token>"
}
```

passed in the request headers as shown below:

```
headers = {
    "Authorization": f"Bearer {load_access_token()}",
    "Accept": "application/fhir+json"
}
```

### 2.3 Extracting Patient Data with FHIR Search Parameters

Example search calls used in our project:

Search for patient by name and gender:
```
GET /Patient?name=Smith&gender=male
```

Extract the patient ID:
```
patient_id = patients_data["entry"][0]["resource"]["id"]
```

Extract all conditions for the selected patient:

```
GET /Condition?patient=<patient_id>
```

Code:
```
url = f"{OPENEMR_BASE}/Condition?patient={patient_id}"
response = requests.get(url, headers=get_headers_openemr())
conditions = [entry["resource"] for entry in response.json().get("entry", [])]
```

### 2.4 Error Handling in Extraction

```
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print("API Error:", e)
```

We validate:
- response errors
- missing FHIR elements
- empty search results

## 3. Transformation

Transformation includes:

- SNOMED CT parent concept lookup and transform primary care EMR request body (Task 1)
- SNOMED CT child concept lookup and transform primary care EMR request body(Task 2)
- Populating Blood Pressure Observations (Task 3)  
- Populating Procedure resources (Task 4)  
- SNOMED → ICD-10 mapping (Task 5)

Cleaning and formatting of FHIR resources
Constructing valid FHIR Patient, Condition, Observation, Procedure JSON

### 3.1 SNOMED Parent Lookup (Task 1)

We use ECL constraint syntax:```>! <snomed_code>```

Meaning: direct parents

```
url = f"{TERMINOLOGY_SERVER}/search?constraint=>! {snomed_code}"
response = requests.get(url)
parent = response.json()[0]
parent_id = parent["conceptId"]
parent_term = parent["term"]
parent_preferredTerm = parent["preferredTerm"]
```

### 3.2 SNOMED Child Lookup (Task 2)

We use:
```<! <snomed_code>```

Meaning: direct children
```
url = f"{TERMINOLOGY_SERVER}/search?constraint=<! {concept_id}"
child = response.json()[0]
child_id = child["conceptId"]
child_term = child["term"]
child_preferredTerm = child["preferredTerm"]
```
### 3.3 BP Observation Handling (Task 3)

Task 3 required a conditional transformation:

Case 1 : BP Observation exists in OpenEMR

We extract the existing values and map them to our BP template.
```
component = resource["component"]
sys_value = component[0]["valueQuantity"]["value"]
dia_value = component[1]["valueQuantity"]["value"]
```

We then merge these values into the template JSON:
```
bp_template["component"][0]["valueQuantity"]["value"] = sys_value
bp_template["component"][1]["valueQuantity"]["value"] = dia_value
bp_template["subject"] = {"reference": f"Patient/{primary_id}"}
```

We also generate clinical interpretations:
```python
def interpret_bp(sys, dia):
    if sys < 90 or dia < 60:
        return "L", "Low"
    if sys > 140 or dia > 90:
        return "H", "High"
    return "N", "Normal"
```

Interpretation fields are inserted before loading.

Case 2 : BP Observation does NOT exist in OpenEMR

We load a JSON template:
```
data/blood_pressure_observation.json
```
This template includes systolic/diastolic codes, category, status, etc.
We then append:
- subject reference
- default interpretation fields
- effective datetime

```python
bp_template = load_bp_template(primary_id)
bp_template["subject"] = {"reference": f"Patient/{primary_id}"}
```
### 3.4 Procedure Handling (Task 4)

Task 4 is similar to that of Task 3

Case 1 : Procedure exists in OpenEMR

We extract fields such as:
```python
procedure_code = proc["code"]["coding"][0]["code"]
performed_date = proc.get("performedDateTime", "2024-01-01")
notes = proc.get("note", [])
````

We build the transformed JSON:
```
proc_json = load_procedure_template(primary_id)
proc_json["code"]["coding"][0]["code"] = procedure_code
proc_json["performedDateTime"] = performed_date
proc_json["note"] = notes
proc_json["subject"] = {"reference": f"Patient/{primary_id}"}
```

This ensures the Primary Care system receives a procedurally identical representation.

Case 2 : Procedure does NOT exist in OpenEMR

We load the fallback template:

```
data/add_procedure.json
```

### 3.5 SNOMED → ICD-10 Mapping (Task 5)

We pull ICD-10 mapping from a SNOMED refset:

```python
extended = get_extended_snomed(snomed_code)
refset_id = extended["refsets"][-1]

url = f"{HERMES_BASE}/{snomed_code}/map/{refset_id}"
mapping = requests.get(url).json()[0]

icd_code = mapping["mapTarget"]
icd_display = mapping.get("mapTargetName", "ICD-10 Term")
```

### 3.6 Patient Resource Transformation

We transform the OpenEMR patient resource to match the Primary Care Patient profile.
```python
transformed = {
    "resourceType": "Patient",
    "meta": {
        "profile": ["https://dentalinformatics.online/B581/StructureDefinition/patient-profile"]
    },
    "active": patient.get("active", True),
    "name": patient.get("name", []),
    "gender": patient.get("gender"),
    "birthDate": patient.get("birthDate"),
    "identifier": patient.get("identifier", []),
    "telecom": patient.get("telecom", [])
}
```

Address transformation is handled as below
```python
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
    transform["address"] = cleaned_addresses
```

## 4. Loading

Loading refers to writing transformed data into the Primary Care FHIR server.

All POST requests follow:

```
[POST]
response = requests.post(
    f"{PRIMARY_CARE_BASE}/<ResourceType>",
    headers=get_headers_primary(),
    json=payload
)
response.raise_for_status()
```

## 5. Detailed Documentation of All Five Tasks
### Task 1
Extract patient + conditions → transform using SNOMED parent → load patient & parent condition

Steps:
1. Search & retrieve OpenEMR patient
2. Extract all patient conditions
3. Get SNOMED parent term
4. Transform patient to Primary Care format
5. Create patient in Primary Care
6. Create condition in Primary Care
7. Save resource id in ```data/new_primary_patient.txt``` for future reference

### Task 2
Extract patient → transform using SNOMED child → load new child condition

Steps:
1. Reload stored patient ID from Task 1 file
2. Extract all conditions again
3. Lookup child SNOMED term
4. POST new Condition resource to Primary Care

### Task 3
Extract BP observation → transform → load into Primary Care
Steps:
1. Load Blood Pressure Observation JSON template from ```data/blood_pressure_observation.json``` document
```
If OpenEMR has BP, extract systolic & diastolic → interpret values → update template → load
If OpenEMR does not have BP, use template with default values → load
```
2. Add Patient to Subject field in JSON template
```
"subject": {
            "reference": f"Patient/{patient_id}"
        },
```

3. Load BP Observation to Primary Care EMR
Example BP posting:
```
response = requests.post(f"{PRIMARY_CARE_BASE}/Observation", json=bp_resource)
```

### Task 4
Extract Procedure → transform → load into Primary Care
Steps:
1. Load add procedure JSON template from ```data/add_procedure.json``` document
```
If Procedure exists in OpenEMR: extract + transform fields
If not: use template JSON
```
2. Add patient reference to subject field in JSON
```
"subject": {
            "reference": f"Patient/{patient_id}"
        },
```
3. Post to Primary Care EMR
Example Procedure posting:
```
response = requests.post(f"{PRIMARY_CARE_BASE}/Procedure", json=add_resource)
```
### Task 5
Create HL7 v2 ADT_A01 message

Steps:
1. Load patient resource id from task1 output file
2. Extract all conditions of a patient and pick a condition
3. Get the snomed id of the condition.
```python
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
```
4. Get the refsets using the terminology server
```python
url = f"{HERMES_BASE}/{concept_id}/extended"
resp = requests.get(url)
resp.raise_for_status()
return resp.json()

refsets = extended.get("refsets", [])
```

5. Get the ICD-mapping using the refset
```python
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
```
6. Create ADT message Using hl7apy:

```python
msg = Message("ADT_A01")

msg.msh.msh_1 = "|"
msg.msh.msh_2 = "^~\\&"
msg.msh.msh_3 = "OpenEMR"
msg.msh.msh_4 = "OpenEMR_FHIR"
msg.msh.msh_5 = "PrimaryCareEHR"

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

msg.dg1.dg1_1 = "1"
msg.dg1.dg1_3 = f"{icd_code}^{icd_display}^I10"
msg.dg1.dg1_4 = snomed_term

```

7. Save the message in a file:
```
data/patient_adt_message.txt
```

## 6. Challenges & Resolutions

| Team Member                       | Role                                                                  |
|-----------------------------------|-----------------------------------------------------------------------|
| Missing SNOMED parent/child terms | Iterated conditions until valid relationship found                    |
| Incomplete FHIR fields            | Added default values such as Not Available, undefined in the structure |
| API timeouts / errors | Added raise_for_status() and exception handling |            |
| HL7 formatting complexities | Used hl7apy for segment validation |

## 7.Summary

This ETL pipeline demonstrates:

- Complex interoperability across multiple FHIR systems
- Use of SNOMED CT for terminology enhancement
- ICD-10 mapping for diagnosis classification
- Transformation from FHIR JSON → HL7 v2 
- Robust extraction, transformation, and loading workflow 
- The pipeline forms a reusable foundation for real healthcare system integration.




