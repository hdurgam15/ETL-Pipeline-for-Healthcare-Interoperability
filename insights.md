---
layout: default
title: Insights
--- 

# ETL Project

---
## Navigation
- [Home](index.md)
- [Team Contributions](team_contributions.md)
- [ETL Pipeline](etl_pipeline.md)  
- [Insights](insights.md)
- [Presentation](presentation.md)
- [Requirements](requirements.txt)
- [Github Project Repo](https://github.iu.edu/mahigogu/FA25_B581_Final_Project_OpenEMR_mahitha_gogu)
---

# Project Insights and Reflections 

This page summarizes the key insights, lessons learned, challenges addressed, and meaningful observations derived from our ETL project. It also includes reflections on interoperability, terminology usage, and system integration across the OpenEMR FHIR server, the Hermes SNOMED CT Terminology Server, and the Primary Care FHIR server.

--- 

## Key Insights 

### Insight 1: FHIR Data Quality Varies Across Systems   

During extraction, we observed differences in how resources are populated in OpenEMR. Several Patient and Condition resources lacked complete demographic or clinical information. This required the ETL pipeline to incorporate error checking, defensive programming, and fallback values to ensure robust execution. 

### Insight 2: SNOMED CT Is Highly Structured but Not Always Complete   

SNOMED CT parent and child relationships were not available for every concept. Some conditions had no parent; others had no children. We addressed this by iterating through multiple conditions until a valid parent or child concept was found. This emphasized the importance of terminology flexibility in real-world clinical systems. 

### Insight 3: ICD Mapping Requires Careful Selection of Refsets   

The SNOMED CT “extended” structure contains multiple refsets. Not all refsets include ICD-10 mappings. Selecting an appropriate mapping source required trying multiple refsets and gracefully handling cases where no ICD mapping was available. 

### Insight 4: FHIR Is Flexible, HL7 v2 Is Structured   

FHIR’s JSON-based data model is flexible, human-readable, and extensible. In contrast, HL7 v2 ADT messages require strict segment formatting. Using hl7apy showed how legacy systems continue to rely on tightly formatted messages. This reinforced an understanding of how modern and legacy healthcare systems interoperate.

--- 


## Visual Insights (Optional) 

If presenting visually, the following charts would add value:
- A bar chart showing the count of conditions for selected patients
- A pie chart of gender distribution from extracted patients
- A simple diagram showing the ETL workflow
- A mapping illustration showing SNOMED Code → Parent/Child → ICD-10   

(Visuals can be added later to this page using simple images.) 

--- 

## Challenges Encountered 

### Challenge 1: Missing or Sparse Data   

Some OpenEMR patients lacked address, telecom, or additional identifiers.   

**Solution:** Added optional field handling and fallbacks to avoid breaking the pipeline. 

### Challenge 2: Terminology Gaps   

Not all SNOMED concepts contained parent or child relationships.   

**Solution:** Implemented conditional retries until a valid medical concept was found. 

### Challenge 3: Inconsistent Mapping Availability   

ICD-10 mappings were present in some refsets but missing in others.   

**Solution:** The pipeline attempted mappings from all available mapping refsets and used the first available ICD term. 

### Challenge 4: Multiple Systems With Different Standards   

We had to integrate three different systems: a FHIR source, a terminology service, and a FHIR target.

**Solution:** Standardized the ETL logic so that extracted JSON could be safely passed into transformation and then loaded into the target server. 

--- 

## Lessons Learned 

### Lesson 1: Healthcare Data Requires Defensive Programming   

Real clinical data often has missing fields or inconsistencies. A robust ETL pipeline must account for incomplete demographic and clinical information. 

### Lesson 2: Terminology Servers Are Crucial for Interoperability   

The Hermes Terminology Server allowed us to explore parent-child SNOMED relationships and obtain ICD mappings. Without terminology resolution, meaningful cross-system integration would not be possible. 

### Lesson 3: Modern and Legacy Systems Must Coexist   

FHIR supports modern REST-based healthcare integration, while HL7 v2 remains dominant inside hospitals. This project demonstrated how both standards can work together through transformation. 

### Lesson 4: Logging and ID Storage Are Essential   

Storing patient IDs, SNOMED codes, and other identifiers in text files (such as new_primary_care_patient_id.txt) ensured that subsequent tasks in the pipeline remained consistent and reproducible.

--- 

## Potential Improvements 

- Implement caching of SNOMED and ICD lookups to improve performance
- Add retry logic for unstable server connections   
- Improve selection logic for best parent or child concept (e.g., filtering irrelevant SNOMED hierarchies)   
- Expand HL7 message generation beyond ADT_A01 to include ORU or ORM messages   
- Add visual dashboards to display ETL performance and statistics   

--- 

## Final Reflection 

This project provided hands-on experience with real-world healthcare interoperability challenges. Working with APIs, terminology servers, and FHIR resources strengthened our understanding of: 

- Clinical terminologies
- Mapping between SNOMED CT and ICD-10   
- Cross-system ETL workflows   
- Legacy HL7 integration