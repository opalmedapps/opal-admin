# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Features

* Hospital-settings app (!1)
* API endpoints for hospital-settings (!3)
* Model translations and localization in code (!2)
* Automatic audit logging (!7)
* Add authentication backend to authenticate against fed auth web service (!15)
* REST API endpoints for authentication (!8)
* CORS headers required for cross-site requests (#26 via !8)
* New Frontend and views for hospital-settings app (!31)
* Users app with custom user model (!39)
* Enforce authenticated requests to the API endpoints (!41)
* Enforce authenticated user for all URLs (!72)
* feat: Add direction url field for sites (!73)
* feat: Add user patient relationship type model (!84)
* Add user types (!91)
* Add patient model (!98)
* Feat: Get all data needed for the app home view request (!118)
* feat: Registration encryption info endpoint (!170)
* Add logo (image) field to the Institution model (!159)
* feat: create permissions class to check caregiver-patient access (!169)
* Adjust legacy chart api endpoint to use legacy_id (!185)
* feat: add model for a user's mobile device (!187)
* Add hospital service for communication with the OIE (!173)
* Add REST API endpoint for the questionnaire report generation
* Add REST API endpoint for the patient's caregiver(s) relationship(s) (!222)
* feat: Add can_answer_questionnaire field to RelationshipType model (!689)
* Add unique constraint to Relationship model (!655)
* Generate a random uuid for the caregiver username (!267)
* Add a "Manage Caregiver Access to Patient Data" page (!271)
* Add date_of_death field to Patients model (!714)
* Generate a random uuid for the caregiver username (!267)
* feat: Add ePRO questionnaire reporting tool with custom access permission (!275)
* feat: Build QR code new UI (!148)
* feat: Add wearables UI accesible from ORMS (!359)
* feat: add patient demographics API endpoint (!309)
* feat: unified Manage Caregivers module/page to manage the access to caregivers of patients (!492)
* feat: Add TwilioService and twilio modules (!520)
* feat: management command to send data from consenting patients to the databank (!679)
* feat: add test_results app to store pathology and lab results (!709)
* feat: add blood pressure types for the QuantitySample (!690)
* feat: show systolic and diastolic blood pressure measurements on the same chart (!708)
* feat: add REST API endpoint for creating pathology reports (!724)
* feat: add a pathology PDF generator for producing reports (!791)
* feat: add usage_statistics app to store users' and patients' activity statistics (!1100)
* feat: add management command for populating statistics to DailyUserAppActivity and DailyUserPatientActivity models (!1133)

### Documentation

* Add mkdocs-based documentation site (!35)
* Improve getting started documentation for Windows users (!42)

### Miscellaneous Chores

* build: Docker support (#5)
* build: CI setup (#2)
* build: Switch to MariaDB from PostgreSQL (!16)
* Add pre-commit (!26)
* Add wemake-python-styleguide for improved code quality (!19)
* deps: Add Renovate Bot configuration (!6)
* fix: Better migration names for hospital-settings (!38)
* chore: Add vscode extension recommendations (!40)
* build: Fix broken documentation build (!52)
* i18n: Add French translations for the hospital settings app (!46)
* fix: Add permission class to caregiver list end point (!240)
