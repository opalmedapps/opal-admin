# Patients

The `patients` app provides the central piece, the `Patient`, as well as the relationship types and relationships between a Patient and caregiver.

The design is as follows (see the [code reference][opal.patients.models] for implementation details of each class):

```mermaid
classDiagram
    class RelationshipType {

    }

    class Patient {

    }

    class Relationship {

    }

    class CaregiverProfile {
        <<caregivers>>
    }

    class Site {
        <<hospital_settings>>
    }

    class RelationshipStatus {
        <<TextChoices>>
    }

    Patient "patients 1..*" <--> "1..* caregivers" CaregiverProfile: Many-to-many through model Relationship

    Relationship --> "type" RelationshipType
```
