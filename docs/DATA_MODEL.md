# Sätila Splits – data model

## Core entities

### event
One held or cancelled edition of Sätila Trail.
Fields should include year, date, organizer, timing event ID and tracker event ID where known.

### race
One race family within an event, e.g. `ultra85`, `trail43`, `trail22`.

### course_version
A verified route geometry or distinct route candidate.
Do not merge years solely because both are marketed as 43 km or 85 km.

### checkpoint
Stable geographic/logical identity, e.g. Navåsen, Helsjön, Äskhult.

### event_checkpoint
A checkpoint as used in a specific event/course version.
Stores that year's actual chainage, role, cutoff and source evidence.

### result
Participant-level official result data including status, class, finish time and source identity.

### split
An official timing observation from the timing provider.

### gps_passage
A passage derived from a timestamped GPS trace.
Must never be presented as an official timing split.

### track
A GPX or equivalent route/activity trace with source type, verification state and checksum.

## Provenance classes

- OFFICIAL_ORGANIZER
- ITRA_TRACE
- RACE_TRACKER
- VERIFIED_PARTICIPANT
- RECONSTRUCTED

## Course comparison

Cross-year comparisons should anchor to checkpoint identity rather than nominal kilometer labels.
For example, Start → Navåsen remains the comparable segment even if Navåsen occurs at different chainage in different years.

Course equivalence must be established from geometry comparison, not labels.
