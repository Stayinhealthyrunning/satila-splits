# Codex next-pass blockers and fixes

Datum: 2026-10-01  
Kandidat: `integration/codex-independent-qa-2026-10-01`  
Syfte: ett enda precist arbetsblock för nästa Codex-körning. Ändra inte EQ-källdata eller råa tider för att lösa UI-problem.

## P0 – effective analysis boundaries / Tostared

2025 43 km har stationen **Tostared 10,2 km (UID 1416266)** i metadata men **0 publicerade TIME-passager**.

Nuvarande `boundaries()` i app.js tar fortfarande med alla `is_analysis_boundary` med numerisk km. Det skapar:
- Grind → Tostared, n=0,
- Tostared → Torrås, n=0,

i stället för den källgiltiga sammanslagna tidssträckan:

> **Grind 1,2 km → Torrås 16,2 km = 15,0 timing-km, n=130 exakta positiva par.**

Fix:
- behåll Tostared i rå stationsmetadata/proveniens,
- bygg **effective analysis boundaries** från stationer som faktiskt har minst en publik TIME-observation i vald edition,
- startpunkten är fortsatt explicit t=0,
- skapa inga Tostared-passager,
- efter fix ska 2025/43 ha **7** effektiva segment,
- loppplanen ska få **7/7 historiska segment** på bred kohort och inte falla tillbaka runt Tostared.

Kör:
```bash
python tests/browser_evidence_acceptance.py
```

## P0 – gemensam pace-distance capability

Oberoende source-QA har verifierat två segment där TIME är giltig men publicerad timing-km inte bör användas som fysisk segmentdistans:

| Edition | Segment | timing-km | n | Implicerad medianfart |
|---|---|---:|---:|---:|
| 2023 43 km | Torrås → Almered | 16,0 | 84 | 23,663 km/h |
| 2024 43 km | Torrås → Almered | 16,0 | 58 | 20,285 km/h |

Detta är **inte** anledning att ändra stationernas km eller TIME. Segmenttiderna är fortsatt källgiltiga.

### Inför en gemensam hjälpfunktion

Implementera ett återanvändbart segment-capability-begrepp, exempelvis:

- `time_ok`: två verkliga positiva TIME-ankare finns,
- `distance_ok`: segmentdistansen är lämplig för pace/fart,
- `pace_ok = time_ok && distance_ok`.

Det behöver inte hårdkodas till två år om samma auditregel kan användas säkert: för segment >=3 timing-km, minst fem verkliga par, och en fältmedian som implicerar >20 km/h ska `distance_ok=false`. UI ska då säga **“Distans ej verifierad · tid visas”** eller motsvarande.

### Följande komponenter måste använda samma capability

1. **D16 `renderPacingIndex()`** – ingen pacingpunkt för time-only segment.
2. **D18 `renderClassSeries()`** – klasskurvor ska brytas på time-only segment.
3. **T04 segmenttabell** – segmenttid/median/n visas, tempo/min/km döljs eller märks ej verifierad.
4. **P0.2 segmentpodium** – ranka på verklig segmenttid; värdet ska vara segmenttid när pace saknar säker distans, inte falskt min/km.
5. **P0.3 `profileInsights()`** – “snabbast/långsammast delsträcka” får inte rankas med `seconds/km` över time-only segment. Använd relativ segmenttid mot fältmedian eller begränsa pace-baserade insikter till distance_ok.
6. **P0.3 sista verifierade segmentet** – tid får visas även om pace inte får visas.
7. **standoutsFor()** – pacebaserade standout-kategorier måste capability-gatas; placeringsbaserade kategorier påverkas inte.
8. **T03 profilens segmenttabell** – tid/fältmedian/n kvar, tempo döljs för time-only segment.
9. **T06 loppplan**:
   - historisk `segmenttid / sluttid`-andel behöver **inte** fysisk segmentdistans och ska fortsätta fungera,
   - **distansfallback får inte användas** på ett segment vars distance_ok=false,
   - tempo-kolumn döljs/markeras ej verifierad för sådant segment.
   - Om ett segment saknar både historiskt n>=5 och distance_ok ska planen säga att referensen inte kan fyllas för den kohorten, i stället för att fabricera en distansfallback.

Kör efter fix:

```bash
python tools/audit_segment_distance_capability.py
python tests/browser_release_pace_capability_acceptance.py
```

## P0 – release copy

Ta bort:
- **“Samma stigar”** i hero,
- **“Samma stigar. Djupare insikter.”** i footer,
- **“GOTALENDETS JÄMFÖRELSEMODELL”**.

Rekommenderad hero:
> Tre distanser. Nio resultatår. Djupare insikter.

Kör:
```bash
python tests/test_release_copy_acceptance.py
```

## P0 – browserhistorik

Nuvarande `updateQuery()` använder `history.replaceState` för användarens editionval.

Krav:
- initial deep-link ska inte skapa extra history-entry,
- **användarinitierat** byte av familj/år ska använda `pushState` eller motsvarande,
- Back/Forward ska återställa både state och UI,
- state-restaurering får inte själv pusha en ny entry.

Kör:
```bash
python tests/browser_release_navigation_acceptance.py
```

## P1 – keyboard/fokus/error state

Nuvarande mobilmeny togglas vid click men Escape stänger den inte explicit och återställer inte alltid ARIA. Race-load failure fångas på init men senare `loadRace().catch(console.error)` kan bli enbart konsolfel.

Krav:
- Escape stänger mobilmeny och `aria-expanded=false`,
- dialog/förslagsflöden behåller rimligt fokus,
- saknad race-bundle ger synligt status/error-element, gärna `role="alert"`,
- ingen användaråtgärd får bara landa i `console.error`.

Kör:
```bash
python tests/browser_release_ux_acceptance.py
```

## P1 – redan förbättrat i Codex, behåll

Codex nuvarande gren har värdefulla förbättringar som inte ska backas ur:
- D01 denominator/status-KPI,
- D03 kumulativ målgång,
- D12 5-års åldersintervall,
- D13 valbara klubb/ort-grupper + median,
- D18 upp till fem valbara klasser,
- K04 tidsstyrd Replay,
- K05 kartduell 2–5 löpare med gemensam tävlingsklocka,
- rikare `coverage.json` härledd från race-bundles/route-inventory.

Den riktade datagranskningen av Codex `coverage.json` är grön: [Actions 36855026565](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36855026565).

### K04/K05 är redan implementerade – regressionssäkra, bygg inte om

Aktuell integrationskod har:
- K04 personlig Replay med 30/60/120/180 s, play/pause/reset, följ löpare, visa hela banan och tydlig interpolationsetikett,
- K05 kartduell för **2–5 löpare**, gemensam tävlingsklocka, 0,5×/1×/2×/4×, kamera hela banan/följ ledare, leaderboard och uttrycklig märkning att ordningen mellan kontroller är illustrativ.

Nästa Codex-pass ska **inte** ersätta detta. Kör regression och förbättra bara om test visar konkret fel.

## P1/P2 – kvarvarande blueprint-gap efter ovan

Enligt Codex egen parity-audit och oberoende frontend-audit:
- D22 Course Intelligence behöver fortfarande segmentkopplad pacing/spridning/placeringsrörelse/DNF-exit.
- D23 checkpoint-ankare/höjdavbrott behöver slutverifieras.
- T04 behöver full segmentrad/proveniensparitet.
- T06 D+/D− kan bara visas om evidens faktiskt finns; hitta inte på höjd per segment.
- T07 publiceringsgrad/konfliktkolumn kan läggas till från verifierad provenance.
- T09 ålder/klubb/paginering är delvis.
- K02 ska förbli saklig tomstatus tills två auktoritativa historiska rutter finns.

## Slutordning

1. Lös P0 pace/copy/navigation.
2. Lös P1 keyboard/error.
3. Kör release-only testerna.
4. Kör `tools/run_release_candidate_checks.py --source`.
5. Kör browser-core.
6. Slutverifiera D22/D23/T04/T07/T09 utan att fabricera saknad evidens.
7. Uppdatera parity-audit och BUILD_STATE.
8. Ingen merge till main/publicering före projektägarens granskning.
