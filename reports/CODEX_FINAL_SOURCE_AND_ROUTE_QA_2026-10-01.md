# Sätila Splits – slutlig käll- och rutt-QA

Datum: 2026-10-01

Status: **READY_FOR_INTEGRATION_QA**

Draft PR: https://github.com/Stayinhealthyrunning/satila-splits/pull/9
Fullständigt lokalt testad implementations-SHA: `e994e5b108f8ab3f3f537e35ade9bd3f5d52c7a9`

## Bas och avgränsning

- Arbetsgren: `codex/saetila-final-visual-qa-2026-10-01`.
- PR-bas: `integration/codex-independent-qa-2026-10-01` vid `e8a5be1fe542d669f8939bdc1186ef0e12cd55de`.
- Föregående PR-head: `2c0af15925c452446ae333a3f77731ab0b288626`.
- Arbetet avser issue [#10](https://github.com/Stayinhealthyrunning/satila-splits/issues/10) och [#11](https://github.com/Stayinhealthyrunning/satila-splits/issues/11).
- Ingen merge, publicering, ändring av integrationsgrenen eller stängning av issue #6 har gjorts.

## Verifierade GPX-original

De fem arrangörsfilerna återfanns i det lokala privata arkivet `satilatrail_gpx_2026.zip`, utanför repositoryt. Arkivets SHA-256 är `5595d8a47c4b8ef20b2cc2372b3ea7ee244c4dd8d997c4570793f2779a76684e`. Filerna extraherades endast till en temporär lokal katalog för omexport. Rå-GPX har inte ändrats, committats eller lagts i publiceringspaketet.

| Familj | Originalfil | Råpunkter | Verifierad SHA-256 |
| --- | --- | ---: | --- |
| 5 km | `Sätila Trail 5 - 2026.gpx` | 187 | `304fe04cba9ae22840253a99589fe142c31971ee129cc3fb38dde0ecfbc7144d` |
| 10 km | `Sätila Trail 10 - 2026.gpx` | 408 | `24fc6f0ff6eca90dade4471e4743dccbed2272c02fe88b6619c46c6ece9d7c91` |
| 21/22 km | `Sätila Trail 21 - 2026.gpx` | 781 | `c78872ddd3d9e0575eb260227a2d9b40455d7841d0d8a4dcfe71614356a06c39` |
| 43 km | `Sätila Trail 43 - 2026.gpx` | 1 380 | `4b10bee2201e8f2493a1bf564c1603c5431c123fdc8d19dfb432655fb04ee827` |
| 85 km | `Sätila Trail 85 - 2026.gpx` | 2 727 | `c5c313faf2b137cfeacf3b90cee4638094070793d70c8a88ca00944360f582c0` |

Samtliga filhashar matchar `config/source-registry.json` exakt.

## Issue #10 – korrigerad kartgeometri

### Orsak

Den tidigare exporten valde högst cirka 250 koordinater, eller 350 för ultran, med jämna intervall längs källans kumulativa distans. Den numeriska distansaxeln var riktig, men raka linjer mellan de glesa punkterna skar över kurvor och slingor.

### Korrigering

`tools/build_satila.py` behåller nu varje geometriskt unik originalpunkt. Endast direkt efterföljande punkter med exakt noll ny sträcka utelämnas. Varje publicerad punkt innehåller fortsatt:

1. kumulativ haversine-distans från den orörda GPX-punktföljden;
2. latitud och longitud;
3. GPX-höjd där sådan finns.

`geometry_length_km`, slutpunktens kedjelängd och kartans/höjdprofilens gemensamma punktlista använder sex decimalers distansprecision. Exporten deklarerar `geometry_export_method=all_geometrically_unique_source_trackpoints` och redovisar även den faktiskt ritade polylinjens längd.

### Före och efter

| Bana | Punkter före | Punkter efter | GPX-km | Ritad km före | Ritad km efter | Förkortning före | Förkortning efter |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 km | 156 | 187 | 5,532991 | 5,486386 | 5,532991 | 0,842 % | 0,000 % |
| 10 km | 227 | 408 | 10,876375 | 10,550493 | 10,876375 | 2,993 % | 0,000 % |
| 21/22 km | 251 | 781 | 23,042558 | 21,828183 | 23,042558 | 5,272 % | 0,000 % |
| 43 km | 251 | 1 380 | 42,254254 | 38,741922 | 42,254254 | 8,312 % | 0,000 % |
| 85 km 2026 | 351 | 2 727 | 87,866144 | 78,325743 | 87,866144 | 10,858 % | 0,000 % |

Avrundade sexdecimaliga publicerade koordinater behåller 100,000 % av källkedjans längd inom mätprecision för samtliga fem banor.

### Payload och interaktion

| Mått | Före | Efter |
| --- | ---: | ---: |
| Fem ruttfiler, rå JSON | 40 737 byte | 192 318 byte |
| Fem ruttfiler, gzip nivå 9 | 15 790 byte | 68 556 byte |
| Största fil, 85 km rå/gzip | 11 609 / 4 685 byte | 95 652 / 33 811 byte |

Webbplatsen laddar endast rutten för vald upplaga. Den förbättrade 43-km-geometrin passerar klick/scrub, höjdprofil, Replay, kartduell och 390-pixelsvyn utan browserfel eller dokumentoverflow. Den totala råstorleken ligger under testbudgeten 512 kB och varje ruttfil under 256 kB.

### Käll- och editionsgränser

- 5/10/21/43 behåller den uttryckliga 2025/2026-återanvändningen.
- 85-km-filen har fortsatt endast `edition_references: [2026]`.
- Ingen 2026-geometri har kopplats till 2025 års ultra eller någon äldre upplaga.
- Inga kontrollpunkter har fått geografiska positioner och inga deltagar-GPX har publicerats.

## Issue #11 – separata historiska distansbegrepp

`nominal_km=82` är bevarat oförändrat i 2019 och 2021 års EQ Timing-bundles. Ett nytt källstyrt tillägg i `config/edition-distance-metadata.json` ger endast de två berörda upplagorna:

- `eq_timing_leg_km: 82.0`;
- `organizer_advertised_km: 85.0`;
- `distance_semantics_status: organizer_eq_discrepancy`;
- arrangörsinbjudans URL och en uttrycklig källreservation.

`measured_route_geometry_km` sätts endast på de två upplagor som faktiskt har en godkänd publicerad ruttkoppling, 2025/22 och 2025/43. Fältet saknas för 2019/85 och 2021/85 eftersom en accepterad årsspecifik GPX inte finns.

Frontend visar nu 2019/2021 som 85 km i editionsväljaren, men redovisar samtidigt `85,0 km annonserat · EQ Timing 82,0 km` i resultat och separata dimensioner i Course Intelligence och provenienstabellen. Helbanetempo, pacingindex och relativa helbanefartsberäkningar döljs för de två upplagorna eftersom nämnaren är källmässigt tvetydig. Verkliga sluttider, segmenttider, placeringar och tidsbaserade loppplaner är kvar.

Måltidsplanens historiska tidsandelar ändras inte. Standardmåltiden i formuläret följer den källbelagda annonserade distansen, medan eventuell distansfallback fortsatt är tydligt märkt som timing-km och inga GPS-kontrollpunkter skapas.

Övriga ultraår får inte automatiskt `organizer_advertised_km=85` genom familjen `ultra85`. Den externa UTMB-uppgiften 84,4 km har inte gjorts till GPX-längd eller officiellt distansfält.

## Regression och teststatus

Godkänt på implementations-SHA `e994e5b108f8ab3f3f537e35ade9bd3f5d52c7a9`:

~~~text
node --check docs/assets/app.js
node --check docs/assets/analytics-extra.js
python tools/run_release_candidate_checks.py --all
python tests/browser_smoke.py
python tests/browser_release_selection_state_acceptance.py
~~~

Den fulla releasekontrollen inkluderade bland annat:

- source integrity, privacy, review ZIP och tillgänglighets-/prestandabudget;
- fem checksumlåsta rutter och en syntetisk bana med snäva kurvor;
- K03 synkad karta/höjd, K04 Replay och K05 kartduell;
- alla 27 upplagor på 1440 och 390 px;
- 2025/22 och 2025/43 med förbättrad ruttgeometri;
- editionsväxling, navigation, 2023/2024 pace-grind och 2019/2021 distanskonflikt;
- full browser-smoke vid 1440, 900, 768 och 390 px med noll dokumentoverflow.

Oförändrade källsummor:

- 27 upplagor;
- 3 272 resultatrader;
- 2 649 FINISHED;
- 128 DNF;
- 494 DNS;
- 1 UNKNOWN;
- 16 525 observerade TIME-passager.

Inga oväntade page errors, saknade lokala fetches eller integritetsfel rapporterades.

## QA-bevis och kvarvarande begränsningar

De befintliga lokala, ocommittade Chromiumbilderna under `reports/qa-final/` uppdaterades av smoke-körningen. De stora PNG-filerna ingår inte i Git-commit eller publiceringspaket.

Kvarstående evidensgränser:

- 2019 och 2021 saknar accepterad årsspecifik GPX; exakt uppmätt banlängd är därför inte fastställd i applikationen.
- Ingen historisk 85-km-rutt tilldelas från 2026-filen.
- Timingkontrollernas geografiska lägen, segment-D+/D− och exakta DNF-positioner är fortsatt spärrade utan ny källevidens.
- PR #9 är lokalt fulltestad men har inte tillskrivits den tidigare integrationsgrenens fyrjobbsresultat. Samtliga fyra jobb och review-ZIP måste köras på den slutligt integrerade SHA:n.

