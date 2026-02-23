---
# SPDX-FileCopyrightText: Copyright (C) 2026 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later
number: 2
status: proposed
date: 2026-02-23
---

# Add support for patient-reported data

## Context and Problem Statement

We want to add support for patients to store health-related information.
Basically, answers to questions they are usually asked when going to a new doctor or clinic, for example, their history of surgeries, medications, alcohol use, etc.

In the end, the data needs to be provided as FHIR resources so that it can be included in the International Patient Summary (IPS).

While the IPS functionality is currently provided from the `patients` app, it needs to be considered if this is the right place, or if another app (like `health_data`) would be better suited.

## Decision Drivers

- where to store FHIR data
- how much work it is to convert from/to FHIR
- what format/technology is used to display the questionnaire to the user

## Considered Options

### Storage location

- in `patients` app
- in new app
- in `health_data` app

## Decision Outcome

### Storage format

We want to store the data as FHIR resources right away.
I.e., the app (where the data is collected from the patient) needs to do the conversion to FHIR and send the data as FHIR resources to the API endpoint.

### Storage location

While the `patients` app could be well suited, the data will be stored in the `health_data` app because it is [intended to be used for patient-reported data](../apps/health_data.md).
This is to keep the `patients` app specific to providing the main patient data as well as the relationships to caregivers.
The data to be collected is most likely health data, although it could also be the patient's demographic data.
However, we assume for now that the demographic data (like the patient's name) is already known in the system.
The name of the model shall be `PatientReportedData` and have one `JSONField` per resource, e.g., `alcohol_use` or `tobacco_use`.
