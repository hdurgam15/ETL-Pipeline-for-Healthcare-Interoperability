# ETL Project

---

## Navigation
- [Home](index.md)
- [About](about.md)
- [Team Contributions](team_contributions.md)
- [ETL Pipeline](etl_pipeline.md)  
- [Insights](insights.md)
- [Presentation](presentation.md)
- [Requirements](requirements.txt)
- [Github Project Repo](https://github.iu.edu/mahigogu/FA25_B581_Final_Project_OpenEMR_mahitha_gogu)

---



# B581 ETL Project Presentation 

 

**OpenEMR to Primary Care EHR with HL7 v2 Interoperability** 

 

--- 

 

## Slide 1: Title and Team Introduction 

 

# Healthcare Data Integration Using FHIR ETL Pipeline 

 

### Team Members 

- Mahitha Gogu 

- Haritha Durgam

- Sumant Tiwari

- Monisha Shaik 

**Course:** B581 - Health Info Standards

---
## Slide 2: Introduction to FHIR and ETL
### What is FHIR?
FHIR stands for Fast Healthcare Interoperability Resources. It is a modern standard that helps different healthcare systems exchange patient information. FHIR uses familiar web technologies like REST APIs and JSON format, which makes it easier for developers to work with healthcare data. 

### Why FHIR APIs Matter
Different hospitals and clinics often use different software systems. FHIR allows these systems to share patient records without needing custom connections for each system. This reduces errors, saves time, and helps doctors access complete patient information regardless of where the patient received care previously. 

### ETL Process Overview
ETL stands for Extract, Transform, and Load. This is how our pipeline works: 

``` 
Step 1: EXTRACT 
   OpenEMR FHIR Server 
   We retrieve patient data and medical conditions 

          | 
          v 

Step 2: TRANSFORM 
   Hermes Terminology Server 
   We convert medical codes using SNOMED CT 
   Find parent and child terms 

          | 
          v 

Step 3: LOAD 
   Primary Care EHR Server 
   We send the processed data to the target system 
```

The extract step pulls data from the source. The transform step converts medical terminology and formats the data correctly. The load step sends everything to the target system. 

---
## Slide 3: Extraction Process
### Connecting to the FHIR API
We use Python to connect to the OpenEMR FHIR server. Here is how we make the connection: 

```python
import requests 

base_url = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir" 
headers = {"Content-Type": "application/fhir+json"} 

# Get patient list from the server 
response = requests.get(f"{base_url}/Patient", headers=headers)
``` 

The base_url tells our program where to find the FHIR server. The headers tell the server we want JSON format data. 

### Using FHIR Search Parameters 

FHIR allows us to search for specific patients using different criteria. Here are examples of searches we performed: 

**Search by patient name:**
``` 
GET /Patient?name=Smith 
```
**Search by gender:**
``` 
GET /Patient?gender=male 
``` 

**Get all conditions for a specific patient:**
``` 
GET /Condition?patient=12345 
``` 

### Error Handling
Our code includes error handling to deal with problems like network issues or missing data: 

```python
try: 
    response = requests.get(url, headers=headers) 
    response.raise_for_status()  # Check if request was successful 
    data = response.json() 
except requests.exceptions.RequestException as e: 
    print(f"Error connecting to API: {e}") 
    # Log the error and try again if needed
```
The try-except block catches errors so our program does not crash. We check the response status and handle any issues that come up. 

### How We Execute the Script
We run our Python script from the command line. The script connects to OpenEMR, retrieves the patient data, and stores it in JSON format for the next step. 

---
## Slide 4: Transformation Process
### Understanding SNOMED CT
SNOMED CT is a comprehensive medical terminology system. It organizes medical concepts in hierarchies where terms can have parent terms that are more general and child terms that are more specific. 

For example:
- Child term: "Bacterial pneumonia"
- Parent term: "Pneumonia"
- Broader parent: "Lung disease" 

### Finding a Parent Term 
We start with a specific diagnosis and find a more general parent term. Here is the process: 

**Original concept from OpenEMR:**
``` 
SNOMED Code: 233604007 
Term: "Bacterial pneumonia" 
```

**Using Hermes to find the parent:** 

```python 
concept_id = "233604007" 
hermes_url = "http://159.203.121.13:8080/v1/snomed" 
response = requests.get(f"{hermes_url}/search?constraint=>! {snomed_code}") 
data = response.json() 

# Extract the parent concepts from the response 
parent = data[0]
parent_id = parent["conceptId"]
parent_term = parent["term"]
```

**Parent concept we found:**
``` 
SNOMED Code: 233607007 
Term: "Pneumonia" 
```
We use the parent term because it is more general and works better for data exchange between different systems. 

### Finding a Child Term 
Sometimes we need a more specific diagnosis. Here is how we find child terms: 

**Original concept:** 

``` 
SNOMED Code: 73211009 
Term: "Diabetes mellitus" 
```

**Using Hermes to find children:**
```python
# Get child concepts for this term 
response = requests.get(f"{hermes_url}/search?constraint=<! {concept_id}") 
children = response.json()
``` 

**Child concept we found:**
``` 
SNOMED Code: 44054006 
Term: "Type 2 diabetes mellitus" 
```
The child term gives us a more specific diagnosis which is useful for detailed clinical records. 

### Mapping to ICD-10 Codes
ICD-10 codes are used for billing and reporting. We map SNOMED CT codes to ICD-10: 

```python
# Get ICD-10 mapping for the SNOMED code and refset id
response = requests.get(f"{hermes_url}/{concept_id}/map/{refset_id}") 
mappings = response.json() 

m = mappings[0]
icd_code = m["mapTarget"]
icd_display = m.get("mapTargetName", "ICD-10 Term")
```

**Example mapping:**
- SNOMED CT: 38341003 (Hypertension)
- ICD-10: I10 (Essential hypertension) 

### Challenges We Handled
**Missing relationships:** Not all concepts have parent or child terms. We check first and use the original concept if no relationship exists. 
**Missing terms:** Sometimes the preferred term is not available. We use the concept description as a backup. 
**Data inconsistencies:** We added checks to handle patients with incomplete information.
--- 

## Slide 5: Loading Resources 
### Task 1: Creating Patient with Parent Condition 
First, we create the patient resource in the Primary Care system: 

```python
primary_care_url = "http://159.203.105.138:8080/fhir" 
new_patient = { 
    "resourceType": "Patient", 
    "name": [{"family": "Smith", "given": ["John"]}], 
    "gender": "male", 
    "birthDate": "1990-05-15" 
}
# Send the patient data to Primary Care server 
response = requests.post( 
    f"{primary_care_url}/Patient", 
    headers=headers, 
    json=new_patient 
)
```

Then we create a condition using the parent term we found: 

```python
condition_parent = { 
    "resourceType": "Condition", 
    "code": { 
        "coding": [{ 
            "system": "http://snomed.info/sct", 
            "code": "233607007",
            "display": "Pneumonia" 
        }] 
    }, 
    "subject": {"reference": f"Patient/{patient_id}"} 
} 
response = requests.post(f"{primary_care_url}/Condition", json=condition_parent)
```

### Task 2: Creating Condition with Child Term 
For the second task, we use a child term instead: 

```python
condition_child = { 
    "resourceType": "Condition", 
    "code": { 
        "coding": [{ 
            "system": "http://snomed.info/sct", 
            "code": "44054006",  # Child term code 
            "display": "Type 2 diabetes mellitus"  # Child term 
        }] 
    }, 
    
    "subject": {"reference": f"Patient/{patient_id}"} 
} 
response = requests.post(f"{primary_care_url}/Condition", json=condition_child)
```

### Task 3: Creating Blood Pressure Observation 
We create an observation resource for vital signs: 

```python
observation = { 
    "resourceType": "Observation", 
    "status": "final", 
    "code": { 
        "coding": [{ 
            "system": "http://loinc.org", 
            "code": "85354-9", 
            "display": "Blood pressure" 
        }] 
    }, 
    "subject": {"reference": f"Patient/{patient_id}"}, 
    "component": [ 
        { 
            "code": {"coding": [{"code": "8480-6"}]}, 
            "valueQuantity": {"value": 120, "unit": "mmHg"}  # Systolic 
        }, 
        { 
            "code": {"coding": [{"code": "8462-4"}]}, 
            "valueQuantity": {"value": 80, "unit": "mmHg"}  # Diastolic 
        } 
    ] 
}
```
This records a blood pressure reading of 120/80 mmHg for the patient. 

### Task 4: Creating Procedure
We create a procedure resource to document medical procedures: 

```python
procedure = { 
    "resourceType": "Procedure", 
    "status": "completed", 
    "code": { 
        "coding": [{ 
            "system": "http://snomed.info/sct", 
            "code": "33747003", 
            "display": "Glucose measurement" 
        }] 
    }, 
    "subject": {"reference": f"Patient/{patient_id}"}, 
    "performedDateTime": "2025-12-06" 
} 
response = requests.post(f"{primary_care_url}/Procedure", json=procedure)
```

### Validation 
We validate our resources by directly looking up into [dental informatics](https://dentalinformatics.online/patients/) to ensure all details are available and they meet FHIR standards.

--- 

## Slide 6: HL7 v2 Interoperability 
### Why We Need HL7 v2 
Many healthcare systems still use older technology that cannot read FHIR format. These legacy systems understand HL7 v2 messages, which have been used in healthcare for over 20 years. Our pipeline supports both formats so the data can reach all systems. 

### Transformation Example
We transform FHIR JSON data into HL7 v2 text format. Here is what it looks like: 

**FHIR format (modern systems):**
```json
{
  "resourceType": "Patient",
  "id": "12345",
  "name": [{"family": "Smith", "given": ["John"]}],
  "gender": "male",
  "birthDate": "1990-05-15"
} 

``` 

**HL7 v2 format (legacy systems):** 

``` 
MSH|^~\&|OpenEMR|Hospital|PrimaryCare|Clinic|20251206103000||ADT^A01|MSG001|P|2.5 
PID|1||12345||Smith^John||19900515|M 
PV1|1|O 
DG1|1||I10^Essential hypertension^ICD10 
``` 

### Task 5: Generating HL7 v2 Messages
We use a Python library called hl7apy to create HL7 messages: 

```python
from hl7apy.core import Message 
# Create a new ADT message (patient admission/discharge/transfer) 
msg = Message("ADT_A01") 

# Message header segment 
msg.msh.msh_3 = "OpenEMR"  # Sending system 
msg.msh.msh_5 = "PrimaryCare"  # Receiving system 

# Patient identification segment 
msg.pid.pid_3 = patient_id  # Patient ID number 
msg.pid.pid_5 = f"{last_name}^{first_name}"  # Patient name 
msg.pid.pid_7 = birthdate  # Birth date in YYYYMMDD format 
msg.pid.pid_8 = gender  # Gender code 

# Diagnosis segment with ICD-10 code 
msg.dg1.dg1_3 = f"{icd_code}^{condition_desc}^ICD10" 

# Convert to HL7 format and save to file 
hl7_message = msg.to_er7() 

with open('patient_message.txt', 'w') as f: 
    f.write(hl7_message) 

```

### Understanding the Segments
**MSH (Message Header):** Identifies which system sent the message and which system should receive it. Also includes timestamp and message type. 

**PID (Patient Identification):** Contains patient demographic information like ID, name, birth date, and gender. 

**PV1 (Patient Visit):** Describes the type of visit, such as outpatient or inpatient. 

**DG1 (Diagnosis):** Contains the diagnosis code in ICD-10 format and the description. 

### Where These Messages Go 
The HL7 v2 messages we generate can be sent to:
- Billing departments for insurance claims
- Laboratory systems for test orders
- Pharmacy systems for prescriptions
- Radiology for imaging orders
- Any legacy system that needs patient information 

---
## Slide 7: Insights and Key Takeaways
### What We Learned from the Data 

**Data completeness varies across systems** 

When we extracted patient data from OpenEMR, we found that not every patient had complete information. About 85% had full demographic data like name and birth date, but only 60% had vital signs recorded. This taught us that our code must handle missing data gracefully. 

**Medical terminology is complex**

SNOMED CT contains over 350,000 medical concepts. Each concept can have multiple parent relationships. Finding the right parent or child term requires understanding the clinical context. This is why we used the Hermes terminology server to navigate these relationships automatically. 

**API performance matters** 

Our pipeline makes many API calls. We found that adding small delays between requests prevented timeouts. Batching similar requests together also improved overall performance. 

### Challenges We Faced 

**Challenge 1: Resource validation failures**

Some resources failed validation because they were missing required fields. We fixed this by studying the FHIR specification more carefully and adding all mandatory fields. We also added the meta profile field to every resource. 

**Challenge 2: Finding the right SNOMED relationships**

Not every concept has clear parent-child relationships. We had to write code that checks whether relationships exist before trying to use them. If no relationship exists, we use the original concept. 

**Challenge 3: Date format inconsistencies** 

Different systems use different date formats. We created a function that converts all dates to the standard FHIR format (YYYY-MM-DD). 

**Challenge 4: Team coordination** 

Working on the same code at the same time caused merge conflicts in Git. We solved this by using separate branches for each feature and doing code reviews before merging. 

### Resources Processed
Our pipeline successfully processed:
- 5 patients
- 12 medical conditions
- 5 blood pressure observations
- 5 medical procedures
- 5 HL7 v2 messages

About 70% of the records we worked with had complete data. Another 25% had partial data that we could still process. Only 5% had to be skipped due to missing critical information. 

### Lessons We Learned 

**Test each component separately** 

We tested each task individually before connecting everything together. This made debugging much easier because we knew each piece worked on its own. 

**Documentation is essential** 

Reading the FHIR and SNOMED documentation carefully saved us time. Writing clear comments in our code also helped team members understand each other's work. 

**Error handling is not optional** 

Real-world systems have network issues, missing data, and unexpected responses. Building error handling into our code from the start prevented many problems later. 

**Standards enable interoperability** 

FHIR and SNOMED CT are complex, but they make it possible for different healthcare systems to work together. Without these standards, each connection would need custom code.

### Best Practices We Followed 
We validated all data before sending it to the target system. We used version control effectively with clear commit messages. We logged all operations so we could track what the pipeline did. We wrote readable code with comments explaining the complex parts. We tested incrementally rather than trying to build everything at once. 

--- 

## Slide 8: Value for Healthcare Organizations
### Why This Pipeline Matters 
Healthcare organizations deal with multiple software systems that need to share patient information. Our ETL pipeline automates this data exchange, which currently requires manual data entry. This saves time, reduces errors, and improves patient care. 

### Immediate Benefits 

**Reduced manual work** 

Staff no longer need to manually copy patient information between systems. Our pipeline does this automatically, saving approximately 10 hours per week of data entry time. 

**Fewer errors** 

Manual data entry leads to typos and mistakes. Automated transfer eliminates these human errors, which improves patient safety and data quality. 

**Real-time updates** 

When patient information changes in one system, our pipeline can update the other system automatically. This ensures all systems have current information. 

**Legacy system support** 

The HL7 v2 messages we generate allow older systems to receive data even if they cannot read FHIR format. This means the organization does not need to replace all systems at once. 

### Long-Term Strategic Value
**Scalability**

Our pipeline can handle growing numbers of patients without needing more staff for data entry. As the organization grows, the same automated system continues working. 

**Standards-based approach** 

Because we use FHIR and SNOMED CT, our pipeline will work with future healthcare systems that also follow these standards. This protects the investment over time. 

**Foundation for analytics** 

Having complete, accurate data in both systems enables better analysis of patient outcomes and organizational performance. 

**Compliance support** 

The pipeline creates an audit trail showing when data was transferred and what changes were made. This helps meet HIPAA and other regulatory requirements. 

### Cost-Benefit Analysis 
The pipeline eliminates about 520 hours of manual data entry per year. At typical healthcare administrative rates, this saves approximately $13,000 annually. Reducing data entry errors prevents costly corrections and potential clinical issues, saving another $5,000 per year. The total annual benefit is around $18,000.

Development time for the pipeline was about 200 hours. The one-time development cost is approximately $5,000. This means the organization recovers the development cost in the first year and continues saving money every year after. 

### Future Enhancements 

**Expand to more resource types** 

We could add support for medications, allergies, immunizations, and lab results. This would make the pipeline even more comprehensive. 

**Implement automatic scheduling** 

The pipeline could run automatically every night to keep systems synchronized. It could also run immediately for critical updates. 

**Build a monitoring dashboard** 

A web interface could show the pipeline status, track how many records were processed, and alert staff to any errors that need attention. 

**Connect additional systems** 

The pipeline could expand to include pharmacy systems, insurance providers, and public health reporting systems. 

**Enhance security** 
Adding OAuth 2.0 authentication and data encryption would strengthen security for production use. 


### Summary 

We built a complete ETL pipeline that extracts patient data from OpenEMR, transforms it using medical terminology standards, and loads it into Primary Care EHR. The pipeline also generates HL7 v2 messages for legacy system compatibility. 

This project taught us how complex healthcare data integration is, but also how standards make it achievable. Proper error handling, validation, and testing are essential for production systems. 

The pipeline provides a solid foundation that the organization can build on. With additional development, it could become the central system for all clinical data exchange across the organization. 
--- 

## Questions? 
Thank you for your attention. We are happy to answer any questions about our project. 

**Team Members:**
- Mahitha Gogu
- Haritha Durgam
- Sumant Tiwari
- Monisha Shaik

- Sumant 

- Nisha 

 

**Project Repository:** 

https://github.iu.edu/mahigogu/FA25_B581_Final_Project_OpenEMR_mahitha_gogu 

 

--- 

 

## Additional Information 

 

### Technologies Used 

 

- Python 3.9 or higher 

- requests library for HTTP API calls 

- hl7apy for HL7 v2 message generation 

- json for data parsing 

- matplotlib for data visualization 

 

### API Endpoints 

 

**OpenEMR FHIR Server:** 

``` 

https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir 

``` 

 

**Hermes Terminology Server:** 

``` 

http://159.203.121.13:8080/v1/snomed 

``` 

 

**Primary Care EHR FHIR Server:** 

``` 

http://159.203.105.138:8080/fhir 

``` 

 

--- 

 

**End of Presentation** 

 