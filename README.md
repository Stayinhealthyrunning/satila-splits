# Sätila Splits

Källstyrd historisk loppanalys för Sätila Trail Run, med huvudfamiljerna **22 km, 43 km och 85 km**. Sätila bygger på samma Engine 1.0-principer som Ultravasan, Gotaleden och Österlen Spring Trail: verkliga observationer, transparenta statistiska gränser och explicit banproveniens.

> **Aktuell release-status 2026-10-05:** den senaste visuella genomgången och den Gotaleden-baserade individuella analysen publicerades via [PR #43](https://github.com/Stayinhealthyrunning/satila-splits/pull/43). PR:en hade fem gröna slutkontroller på exakt head-SHA och mergeades som releasecommit `5b6fa3b3c6645641b7dd83e3cf031a50741af376`. Efterföljande housekeeping har endast rensat färdiga engångs-workflows och gamla PR-spår. GitHub Pages-deployen efter releasen är grön ([run 37345369803](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/37345369803)); även deploy-workflowens housekeeping-körning är grön ([run 37345766323](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/37345766323)). Det finns inga öppna pull requests i detta repo.

## Verifierad publiceringsdatagrund

| Mått | Omfattning |
|---|---:|
| Officiella EQ Timing-resultatår | 2016–2019, 2021–2025 (9 år) |
| RaceEdition | 27 |
| Resultatrader | 3 272 |
| FINISHED | 2 649 |
| DNF / DNS / UNKNOWN | 128 / 494 / 1 |
| Publicerade källstödda TIME-passager | 14 466 |
| Historiska Ultra85-displayrutter | 2018, 2019, 2021–2025 |
| Källstödda 43 km-rutter | 2021–2025 |
| Arrangörs-GPX, checksummeverifierade | 5 |

EQ Timing-event 2021–2025: `57767`, `62409`, `67695`, `72918`, `77864`. De äldre åren är indexerade i `config/eqtiming-events.json`.

- Sanerade publiceringsbundlar: `docs/data/races/*.json` och `docs/data/bootstrap.json`.
- Publicerad källtäckning: `docs/data/coverage.json`, `docs/data/source-fingerprints.json`, `docs/data/route-inventory.json`.
- Publicerade displayrutter: `docs/data/routes/*.json`. Historiska deltagarspår är uttryckligen **display/proveniens**, inte automatiskt officiell avsedd bana.
- 21/43 km 2025/2026 har ett dokumenterat återanvändningsantagande. Ultra85 2026 är separat arrangörsgeometri och används inte som bevis för äldre lopp.
- Den bortvalda icke-officiella kontrollen Grind finns kvar i källarkivet men ingår inte i de 14 466 publicerade TIME-observationerna eller i analyssegmenten.
- För `2023/2024 trail43` är Torrås→Almered time-only: verklig TIME och n får visas, fysisk min/km är spärrad.
- DNF redovisas utan uppfunnen sista kontroll när någon kopplingsbar offentlig TIME saknas.

## Individuell analys

Den individuella löparanalysen följer nu Gotaledens informationsarkitektur, anpassad till Sätilas källregler:

- sammanfattning och sju toppmått,
- personlig Replay med karta och höjdprofil,
- livejämförelse mot fält, klass och könsgrupp,
- tidslucka och placeringsresa genom loppet,
- pacing-fingeravtryck segment för segment,
- fullbreddsanalys av relativ fart,
- analytisk mellantidstabell och separat källpassage-audit,
- delbar direktlänk till löparprofil.

Replay-position mellan verifierade passager är illustrativ. Resultat, tabeller och prestationsjämförelser använder källstödda EQ Timing-observationer.

## Publicering

`docs/` är den publicerbara, sanerade statiska sajten. `.github/workflows/deploy-pages.yml` publicerar **endast från `main`** och kör käll-/integritetskontroll innan Pages-artifact skapas. Den exakta publika miljöadressen styrs av GitHub Pages/custom-domain-inställningen för repot.

Detta repo publicerar inte automatiskt något kort i huvudportalen Loppanalys.se. Portaländringar hanteras separat.

## Lokal granskning och regression

Kör den aktuella koden direkt från `main`:

```bash
python tools/run_release_candidate_checks.py --source
python tools/run_release_candidate_checks.py --browser
# Browsergruppen kräver Playwright + Chromium
python tools/run_release_candidate_checks.py --all
```

De källbaserade testerna kontrollerar bland annat statusnämnare, verkliga segmentpar, n-gränser, rutt-SHA/proveniens, privatliv, historisk banjämförbarhet och publiceringspaketet. Browsertesterna täcker alla 27 editioner, karta↔höjd-synk, H2H/Replay, individuella profiler, edge cases, responsivitet och tangentbord.

Aktiva Actions-workflows är avsiktligt begränsade till nuvarande publicering, källunderhåll och regression. Färdiga engångsflöden från första byggfasen, gamla integrationsgrenar och DSM-releaseförberedelser har tagits bort från default branch.

## Arkitektur och historik

- Byggblueprint: `reports/SAETILA_SPLITS_BUILD_BLUEPRINT_2026-10-01.md`.
- Historisk Codex-paritetsgranskning: `reports/CODEX_PARITY_AUDIT.md` — historiskt checkpoint, inte aktuell att-göra-lista.
- Historiskt handoff: `reports/PRE_CODEX_FINAL_HANDOFF_2026-10-01.md`.
- Data-/metodikspår: `reports/FINAL_INTEGRATION_HANDOFF_2026-10-01.md`, `reports/COMPONENT_READINESS_MATRIX.json`.
- Maskinläsbar aktuell status: `BUILD_STATE.json`.

Råa EQ-resultatdumpningar och ursprungliga deltagar-GPX får inte publiceras i `docs/`, publikt Git-historik eller öppen release. Originalimporten i `tools/fetch_eqtiming_archive.py` och source-registry/provenancefilerna ska bevaras för reproducerbarhet.
