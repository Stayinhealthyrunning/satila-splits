# Sätila Splits

Analysverktyg för Sätila Trail Run – historiska resultat, mellantider och banversioner för 22 km, 43 km och 85 km.

## EQ Timing-resultatimport

Resultatinhämtningen följer samma provenance-first-princip som Österlen Spring Trail men använder en EQ Timing-adapter.

Verifierade officiella EQ Timing-event: 2021 `57767`, 2022 `62409`, 2023 `67695`, 2024 `72918`, 2025 `77864`.

`tools/fetch_eqtiming_archive.py` öppnar varje publik resultatsida i headless Chromium och arkiverar de XHR/fetch/JSON-svar som EQ:s egen klient använder. URL, status, content-type, SHA-256 och rå payload bevaras. Ett SQLite-index byggs över råarkivet.

`tools/inspect_eqtiming_archive.py` inventerar JSON-payloaderna för resultat- och splitstrukturer. Saknade fält fabriceras aldrig.

GitHub Actions-workflow: **Import EQ Timing results**. Körningen producerar ett råarkiv som artifact för vidare konservativ normalisering till Loppanalys Engine 1.0.
