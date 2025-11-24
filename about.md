---
layout: default
title: About
---

# About This Project

This project was created as part of the B581 (Health Informatics) course to demonstrate a complete working ETL pipeline using FHIR APIs, clinical terminology transformation, and HL7 v2 interoperability.

---

## Project Purpose

The purpose of this ETL system is to:

1. Extract clinical data from a real FHIR server  
2. Transform that data using clinically meaningful relationships (SNOMED CT → Parent/Child → ICD-10)  
3. Load processed resources into a second FHIR server  
4. Generate an HL7 v2 ADT message for downstream legacy systems  

The ETL pipeline demonstrates how healthcare organizations move clinical data between heterogeneous systems while preserving semantic meaning and supporting operational workflows.

---

## Why This Matters in Healthcare

Healthcare organizations often grapple with:

• Multiple EHR systems  
• Varying data standards  
• Legacy HL7 v2 interfaces  
• Clinical terminology inconsistencies  
• Lack of interoperability  

This project shows:

• How FHIR improves data exchange  
• How terminology services enhance semantic accuracy  
• How ETL ensures consistency across systems  
• How HL7 v2 ensures compatibility with hospital infrastructure  

---

## Team Overview

We are a multidisciplinary student team working together to design, implement, and document the ETL pipeline.  
Each team member contributed to extraction, transformation, loading, testing, terminology research, and documentation.
