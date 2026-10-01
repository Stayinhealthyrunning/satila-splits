# Pending Codex release gates – Sätila Splits

Datum: 2026-10-01. Detta dokument avser endast sådant som den oberoende ChatGPT-auditen **inte ska implementera i Codex frontend parallellt**.

## Redan verifierat och ska inte göras om från noll

- 27 historiska editioner / 3 272 resultatrader / 16 525 publika TIME-observationer.
- Status/denominator, exact segment pairs, pacing-normalisering, GPX-proveniens, route gating, replay source anchors, H2H two-way scrub, publiceringsintegritet och statiskt granskningspaket.
- Tre skärmstorlekar för karta/höjd/H2H i första utkastet.
- Alla 48 D/T/K/P0 blueprint-komponenter finns i `reports/COMPONENT_READINESS_MATRIX.json` med evidensstatus.

## Codex-releasekrav som fortfarande måste verifieras på den nya kandidaten

### 1. Saklig hero/footer-copy

Nuvarande gamla förstautkast innehåller formuleringen **“Samma stigar”** trots verifierade kursavvikelser mellan år. Den ska inte finnas i releasekandidaten.

Rekommenderad hero-copy:

> Tre distanser. Nio resultatår. Djupare insikter.

Footer får använda Sätila/Lygnern-identitet men ska inte hävda oförändrad historisk bana.

Dessutom ska referensläckan/felstavningen **“GOTALENDETS JÄMFÖRELSEMODELL”** ersättas av en Sätila-native rubrik eller korrekt “Gotaledens” om referensen verkligen ska stå kvar.

Kör efter ändring:

```bash
python tests/test_release_copy_acceptance.py
```

### 2. Deep links och Back/Forward

Första utkastet bevarar delbar `family/year`-hash men använder `history.replaceState` på användarval. Det innebär att val av år/distans inte skapar användbar webbläsarhistorik.

Releasekandidaten ska:

- öppna `#family=trail43&year=2023` direkt i rätt edition,
- skriva en ny historikpost när användaren väljer annan edition,
- Back återställa föregående distans/år,
- Forward återställa nästa val,
- inte skapa loopar vid programmatisk state-restaurering.

Kör efter implementation:

```bash
python tests/browser_release_navigation_acceptance.py
```

### 3. Codex frontend måste testas på exakt integrationscommit

Gamla gröna browserkörningar är inte bevis för den nya designen. På den slutliga kandidatcommitten ska minst följande köras:

```bash
python tests/browser_synced_scrub_acceptance.py
python tests/browser_all_editions_acceptance.py
python tests/browser_evidence_acceptance.py
python tests/browser_release_navigation_acceptance.py
python tests/test_accessibility_performance.py
```

samt hela `.github/workflows/source-integrity.yml`.

### 4. Källa/proveniens får inte drifta av frontendarbete

Före merge jämförs verified build-baseline med Codex-kandidaten:

```bash
python tools/audit_integration_diff.py <verified-baseline-checkout> <codex-candidate-checkout>
```

Frontend får ändras. `docs/data/*`, `config/eqtiming-events.json`, `config/course-versions.json` får däremot inte ändras tyst som bieffekt av designarbete.

### 5. Kända source-edge-cases ska synas korrekt

- 2025 43 km: Tostared 10,2 km har 0 TIME; historiskt segment är Grind→Torrås, n=130.
- 2023 43 km: två segment n=8, F=4/M=4; pooled median ja, kvartiler/könsmedian nej.
- 2016 85 km: två kvinnliga FINISHED; inget fabricerat brons.
- 2020: frånvaro av source edition, aldrig “0 deltagare”.
- K02 historisk kartoverlay: **blocked_by_evidence** tills två lämpliga publicerbara historiska route assets verifierats.

## Slutregel

Ingen av ovanstående punkter motiverar att Codex gör om datalagret. De är små release- och integrationskrav ovanpå den redan verifierade källbasen.
