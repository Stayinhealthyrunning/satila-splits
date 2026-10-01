# Sätila Splits

Källstyrd historisk loppanalys för Sätila Trail Run, med huvudfamiljerna **22 km, 43 km och 85 km**. Sätila bygger på samma Engine 1.0-principer som Ultravasan, Gotaleden och Österlen Spring Trail: verkliga observationer, transparenta statistiska gränser och explicit banproveniens.

> **Utvecklingsstatus:** första omfattande integrationsversionen för ägargranskning, ännu **inte** mergad till `main` eller publicerad på Loppanalys.se. Den aktiva kandidaten är `integration/codex-independent-qa-2026-10-01` i [Draft PR #7](https://github.com/Stayinhealthyrunning/satila-splits/pull/7). Fortsätt därifrån, inte från äldre buildgrenar.

## Verifierad publicerad datagrund

| Mått | Omfattning |
|---|---:|
| Officiella EQ Timing-resultatår | 2016–2019, 2021–2025 (9 år) |
| RaceEdition | 27 |
| Resultatrader | 3 272 |
| FINISHED | 2 649 |
| DNF / DNS / UNKNOWN | 128 / 494 / 1 |
| Faktiska publika TIME-passager | 16 525 |
| Arrangörs-GPX, kontrollerade mot SHA-256 | 5 |

EQ Timing-event 2021–2025: `57767`, `62409`, `67695`, `72918`, `77864`. De äldre åren är också indexerade i `config/eqtiming-events.json`.

- Frysta, sanerade publiceringsbundlar: `docs/data/races/*.json` och `docs/data/bootstrap.json`.
- Publicerad källtäckning: `docs/data/coverage.json`, `docs/data/source-fingerprints.json`, `docs/data/route-inventory.json`.
- Officiella sanerade displayrutter: `docs/data/routes/*.json`. Av dessa får historiska editioner använda rutt **endast** om den är uttryckligt knuten till editionen. Organisatörsfilerna för 21/43 km har ett dokumenterat återanvändningsantagande för 2025/2026; 85 km 2026 är en separat framtida rutt utan 2026-resultat.
- `2025-trail43`: Tostared är stationsmetadata utan TIME. Det legitima sammanhängande observerade intervallet Grind→Torrås har n=130. `2023-trail43`: två n=8-segment får median men inte kvartiler. `2016-ultra85`: endast två kvinnor med FINISHED.
- För `2023/2024 trail43` är Torrås→Almered time-only: verklig TIME och n får visas, fysisk min/km ska vara spärrad. Inget av dagens 128 DNF har kopplingsbar offentlig TIME; redovisa okänd sista station, inte noll avbrott.

## Granska webbappen lokalt

Välj senaste **grönt verifierade** arbetsflöde [Codex + independent QA integration](https://github.com/Stayinhealthyrunning/satila-splits/actions/workflows/integration-candidate.yml). Ladda ned artifact `satila-codex-integrated-review`, packa upp både Actions-arkivet och dess `satila-codex-integrated-review.zip`. Starta sedan en HTTP-server från undermappen `site/` (inte via `file://`):

```bash
cd site
python -m http.server 8080
# Besök http://localhost:8080/
```

Ingen automatisk produktionspublicering görs av integrationsworkflowen. `review-package` körs endast om `source-and-method`, `browser-core` och `release-gates` alla lyckas **på samma commit**.

## Regressionstester

```bash
python tools/run_release_candidate_checks.py --source
python tools/run_release_candidate_checks.py --browser
# Kräver: pip install playwright && python -m playwright install chromium
python tools/run_release_candidate_checks.py --all
```

De källbaserade testerna kontrollerar bland annat statusnämnare, verkliga segmentpar, n≥5/10/20, rutt-SHA, källarkiv, privatliv, historisk banjämförbarhet och publika tabeller. Browsertesterna provar alla 27 editioner, riktig karta↔höjd-synk, H2H/Replay, personlig loppplan, sakliga edge cases, editionsspecifikt state, responsivitet, URL-historik, tangentbord och prestandakrav. Se `tests/browser_evidence_acceptance.py` för Tostared/DNF/D11/D18/D19/D22/T07.

## Arkitektur och överlämning

- Byggblueprint: `reports/SAETILA_SPLITS_BUILD_BLUEPRINT_2026-10-01.md`.
- Historisk Codex-paritetsgranskning: `reports/CODEX_PARITY_AUDIT.md` (äldre checkpoint; en del komponentstatusar där har redan passerats).
- **Nuvarande integrationsdelta och exakt Codex-återstart:** `reports/PRE_CODEX_FINAL_HANDOFF_2026-10-01.md`.
- Data-/metodikspår: `reports/FINAL_INTEGRATION_HANDOFF_2026-10-01.md`, `reports/COMPONENT_READINESS_MATRIX.json`.
- Maskinläsbar status: `BUILD_STATE.json`.
- Säkerhetskopiera den tidsbegränsade privata EQ Timing-källan enligt [issue #6](https://github.com/Stayinhealthyrunning/satila-splits/issues/6) före den 31 oktober 2026 (rekommenderat senast 25 oktober). Råa EQ-resultatdumpningar och individuella deltagar-GPX ska **aldrig** publiceras i `docs/`, publikt Git-historik eller öppen release.

Originalimport: `tools/fetch_eqtiming_archive.py` arkiverar publika XHR/JSON-svar och bevarar URL, status, content-type, SHA-256 och rå payload i privat råarkiv. Reproduktion och jämförelse mot de 36 publicerade JSON-byten dokumenteras i `reports/FULL_REBUILD_EQ_TIMING_VERIFICATION_2026-10-01.md`.
