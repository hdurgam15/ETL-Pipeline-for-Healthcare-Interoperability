---
layout: default
title: Introduction
---

# Introduction

This project demonstrates how modern healthcare systems exchange clinical data using FHIR APIs, SNOMED CT mappings, and HL7 interoperability standards.

## What is FHIR?

FHIR (**Fast Healthcare Interoperability Resources**) defines REST-based APIs for:

- Patient demographics  
- Clinical observations  
- Conditions  
- Procedures  
- Terminology services  

FHIR enables modern EHR systems to exchange information using secure HTTPS APIs.

## What is an ETL Pipeline?

Our ETL pipeline performs:

### Extract  
Retrieve patient data, conditions, observations from OpenEMR using FHIR REST endpoints.

### Transform  
Convert SNOMED codes to:
- Parent concepts  
- Child concepts  
- ICD-10 codes  
Using the Hermes Terminology Server.

### Load  
Insert transformed patient, condition, observation, and procedure resources into the Primary Care EHR server.

### Interoperability  
Convert the FHIR extracted data into an **HL7 v2 ADT message** for legacy systems.

## Pipeline Overview Diagram  
(add screenshot here: `assets/images/etl_diagram.png`)

