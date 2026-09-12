> **Note:** This was a team project completed for the B581 Health Info Standards course at IU. This fork is maintained to showcase my individual contribution. My role: **Observation and Data Transformation Specialist** — executed SNOMED CT and ICD-10 code mapping, supported FHIR data transformations, and contributed to terminology server integration.
>
# ETL Pipeline for Healthcare Interoperability  
### FHIR • SNOMED CT • ICD-10 • HL7 v2 • Python

This project implements a complete ETL (Extract, Transform, Load) pipeline that integrates healthcare data across multiple systems using FHIR APIs, SNOMED CT terminology services, and HL7 v2 message generation.  
It was developed as part of the B581 Health Info Standards course to demonstrate interoperability workflows across modern and legacy healthcare systems.

---

## Project Overview

The ETL pipeline performs the following:

- **Extracts** patient demographics, conditions, observations, and procedures from the OpenEMR FHIR server.
- **Transforms** clinical data using SNOMED CT parent/child concepts and maps SNOMED → ICD-10 using the Hermes Terminology Server.
- **Loads** transformed patient records, conditions, observations, and procedures into a separate Primary Care FHIR server.
- **Generates an HL7 v2 ADT message (Task 5)** for legacy system compatibility.

The project includes five individual coding tasks, each representing key components of a healthcare ETL workflow.

---

## How to Run the Project

Before running any task, ensure you have:

1. A valid FHIR access token stored in 
```
data/access_token.json
```
2. Ensure Python is installed in your machine and install all Python dependencies:
```
pip install -r requirements.txt
```
3. Running Each Task 
- Task 1 : Extract, Transform, Load Patient & Parent Condition
```
python src/task1.py
```
This generates:
```
data/new_primary_care_patient_id.txt
```

- Task 2 : Extract, Transform and Load Child Condition
```
python src/task2_child_condition.py
```

- Task 3 : Blood Pressure Observation
```
python src/task3.py
```
- Task 4 – Procedure
```
python src/task4.py
```
- Task 5 – HL7 ADT Message Creation
```
python src/task5.py
```

## Project Website

The full project documentation including pipeline diagrams, insights, team contributions, and presentation slides is available at:

https://pages.github.iu.edu/mahigogu/FA25_B581_Final_Project_OpenEMR_mahitha_gogu/

## Requirements and Setup
Install all Python dependencies using:
```
pip install -r requirements.txt
```
This installs
- hl7apy
- idna
- requests
- urllib3

And all additional libraries required for Authorization and ETL processing
