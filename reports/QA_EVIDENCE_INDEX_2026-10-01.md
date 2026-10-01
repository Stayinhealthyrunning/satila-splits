# Sätila Splits – QA evidence index

Datum: 2026-10-01. Detta index är avsett för slutlig integration med Codex och senare projektägargranskning.

## Nuvarande överordnade integrationsbevis – 2026-10-01

Det äldre indexet nedan dokumenterar fristående auditsteg från före full Codex-integration. **Aktuell käll- och frontendkod är verifierad gemensamt**:

- Integrationskod: `bdcf74f1c742ad7161ead8c7dbaae719c891f0d3`.
- [GitHub Actions #36869568573 – fyra av fyra SUCCESS](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36869568573): `source-and-method`, `browser-core`, `release-gates`, därefter `review-package` från samma SHA.
- Gransknings-ZIP: `satila-codex-integrated-review`, artifact ID **11166427650**, skapad först efter de övriga jobbens PASS och 44-filers allowlist/integritetsgrind.
- Faktiska Chromium-skärmbilder/loggar: `integration-browser-evidence`, artifact ID **11166422620**. Fyra full-page-bredder **1440, 900, 768, 390 px** med **0 dokumentoverflow**. Karta↔höjd och H2H i 1440/900/390; alla 27 editioner i desktop och mobil; person-/segment-/källa-E2E i 1440/390.
- `tests/browser_evidence_acceptance.py` omfattar nu också metadata-only Tostared i passagegrafen (sju verkligt observerade kontroller, ingen falsk noll-dipp), okänd DNF-station, D07 källklass, D21 variabelt n, D11 sista verifierade segmentstyrka, D18/D19 gemensam klassselection, D22 selectedSegment och T07 verifieringsreservation.
- Source- och reviewpaketverifiering sker fortfarande på committade, sanerade bundlar utan nedladdning av privata originalkällor. Granskningen efter `3b3755a` ändrade frontend/test/dokumentation – **inga filer under `docs/data/`**. Se `reports/PRE_CODEX_FINAL_HANDOFF_2026-10-01.md`.
- `BUILD_STATE.json` uppdateras därefter på integrationsgrenen. Den sista dokumentations-HEAD ska få en ny full CI före Codex handoff. Den sista gröna **kodbaslinjen** är alltid den ovan explicit verifierade; anta inte att ytterligare framtida kodcommits automatiskt är testade.

---

## Äldre, fristående käll-/metodbevis

- Workflow: **Independent Sätila source integrity**
- Senast fullständigt grön audit före visual-asset-lock-commit: [Actions 36853895683](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36853895683)
- Commit: `30e90fa92872ec4e611ed1df126fc81876f81c62`
- Artifact: `satila-source-integrity`
- Artifact ID: **11157065936**
- Artifact innehåller:
  - `satila-source-integrity.json`
  - `satila-segment-capabilities.json`
  - `satila-ui-capabilities.json`
  - `satila-history-checkpoint-alignment.json`

Den efterföljande committen `12a1f4392d276ce4dbe0c76169bfba8b2db760e8` lade enbart till Hero/design-binära lås och motsvarande CI-steg; invänta/kräv en grön run på samma eller senare HEAD innan slutintegration.

## Senaste verifierade interaktionsbevis

- Workflow: **Sätila independent interaction acceptance**
- [Actions 36853533323](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36853533323) – PASS
- Commit: `6b7e8559157abd7f841a1963c4bf7ceb55ff2f53`
- Artifact: `satila-interaction-screenshots`
- Artifact ID: **11156249512**
- Artifactstorlek: cirka 204 kB
- Testomfång i denna generation:
  - 1440×900, 900×900, 390×844
  - karta ↔ höjd tvåvägsskrubb
  - två verkliga 2025/43-resultat i H2H
  - H2H-karta ↔ profil ↔ range synk
  - gammal edition får inte modern route
  - all-edition browser acceptance finns i senare auditkod och ska ingå i nästa explicit sluttrigger.

## Frysta QA-kontrakt

Auditgrenen innehåller nu:
- alla 27 editioner / 3 272 resultatrader / 16 525 TIME,
- sex primära source/publication-gates,
- 9 statistiska syntetiska edge cases,
- 8 course comparability-cases,
- all-edition real-data oracle,
- population/summary/source-chain/rebuild/replay regression,
- representative aggregate golden cases,
- static review package allowlist,
- immutable integration diff-guard,
- 48-component D/T/K/P0 readiness manifest,
- approved Hero/design-reference binary lock.

## Release-only tester som medvetet inte är en del av dagens gröna source-CI

Dessa ska köras på **Codex-kandidaten efter implementation**, inte användas för att döma gamla first-draft:

```bash
python tests/test_release_copy_acceptance.py
python tests/browser_release_navigation_acceptance.py
```

De fångar:
- sakligt felaktigt “Samma stigar”,
- referensläckan/felstavningen “GOTALENDETS”,
- deep-link state,
- Back/Forward race/year history,
- skip-link/fokus,
- reduced-motion,
- Escape/dialog semantics.

## Slutlig integrationsregel

1. Codex pushar och öppnar sin kandidat-PR.
2. Kontrollera att `tools/audit_integration_diff.py` ger PASS för source/provenance mot verifierad build-baseline, eller genomför separat data migration review.
3. Synka/mergea audit-PR #4 mot Codex-kandidaten.
4. Uppdatera `qa.interaction.trigger` en gång och kör tung Chromium-QA på **exakt samma integrerade commit**.
5. Kör hela source-integrity-workflow på samma commit.
6. Kör de två release-only testerna.
7. Skapa ny review ZIP och screenshots från samma commit.
8. Ingen merge till `main` eller publicering innan projektägaren granskat.
