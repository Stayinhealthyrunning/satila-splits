# Sätila Splits – data model

Core entities follow Loppanalys Engine 1.0 semantics: event, race family, RaceEdition, CourseVersion, checkpoint, result, split and track.

## Provenance
- OFFICIAL_ORGANIZER
- ITRA_TRACE
- RACE_TRACKER
- VERIFIED_PARTICIPANT
- RECONSTRUCTED

Official timing observations and display geometry are separate evidence classes. A GPX route never creates an official split. Cross-year comparison uses explicit CourseVersion/comparison-group evidence rather than nominal distance labels.
