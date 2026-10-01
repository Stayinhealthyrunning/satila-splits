# Sätila Splits – QA evidence index

Datum: 2026-10-01. Detta index är avsett för slutlig integration med Codex och senare projektägargranskning.

## Senaste verifierade käll-/metodbevis

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
