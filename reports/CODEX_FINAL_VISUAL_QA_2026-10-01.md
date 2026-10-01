# Sätila Splits – final visual QA och release candidate

Datum: 2026-10-01  
Status: **READY_FOR_INTEGRATION_QA**  
Draft PR: skapas efter att denna rapport har committats och pushats.

## Bas och avgränsning

- Källgren: `origin/integration/codex-independent-qa-2026-10-01`.
- Exakt bas-SHA: `e8a5be1fe542d669f8939bdc1186ef0e12cd55de`.
- Senast tidigare fullt integrerade funktionella kod-SHA: `790dcd7818781eaf405f0f5ef271f9b5ba0bdf9f`.
- Ny isolerad gren: `codex/saetila-final-visual-qa-2026-10-01`.
- Ny lokalt fulltestad implementations-SHA: `94268506bb36b40eb59f3a20f859e03230c2e958`.
- Den ursprungliga worktreen `C:\Git\satila-splits`, grenen `codex/saetila-complete-first-draft` och dess `reports/qa-local/` har lämnats orörda.
- Ingen merge till `main`, publicering, ändring av issue #6 eller ändring av skyddade visuella original har gjorts.

## Reproducerade och rättade fel

### 1. Releasepaketets ZIP-kontrakt var inte Windows-portabelt

Reproduktion:

~~~powershell
python tools/run_release_candidate_checks.py --all
~~~

På Windows avbröts `test_review_package_contract.py` med `FileNotFoundError` eftersom testet skrev till den hårdkodade POSIX-sökvägen `/tmp`, som blev `\\tmp`.

Korrigering:

- `tests/test_review_package_contract.py` använder nu `tempfile.gettempdir()`.
- Testet verifierar att temporärkatalogen finns innan ZIP-filen skapas.
- Samma manifest-, sökvägs- och innehållshashkontroller är kvar oförsvagade.

### 2. Kontrollnamnen överlappade i D21:s Q25–Q75-diagram

Reproduktion:

1. Öppna 2025, 43 km på 1440 px.
2. Gå till Delsträckelabbet → Fältets spridning.
3. De högra etiketterna `Ramhulta`, `Smälteryd` och `Mål` låg visuellt över varandra.

Korrigering:

- `docs/assets/app.js` reserverar nu en separat axelmarginal och roterar kontrollnamnen.
- Den sista etiketten riktas åt motsatt håll för att hålla sig fri från föregående namn och högerkant.
- `tests/browser_evidence_acceptance.py` verifierar sju axeltexter och icke överlappande renderade gränser på 1440 och 390 px.

### 3. Fullsidiga QA-bilder kunde bevara en intern tabells tidigare scrolläge

Reproduktion:

1. Browser-smoke öppnar en profil via knappen längst till höger i resultattabellen.
2. Playwright scrollar då den lokala tabellbehållaren horisontellt.
3. Den efterföljande fullsidesskärmbilden visade tabellens högra kolumner trots att en ny besökare börjar längst till vänster.

Korrigering:

- `tests/browser_smoke.py` återställer lokala tabell- och diagrambehållare till `scrollLeft=0` före bildfångst och verifierar tillståndet.
- Samma test sparar nu även kartduellen och verifierar att dialogen saknar horisontell överrinning.
- `tests/browser_synced_scrub_acceptance.py` verifierar och fångar profil, direktjämförelse samt karta/höjd på desktop och mobil.

## Undersökta misstankar som inte var produktfel

- `docs/assets/analytics-extra.js` laddas inte som en andra runtime från `index.html`. Dess produktionskod är integrerad i `app.js`; därför uppstår inga dubbla event handlers. Filen ligger kvar i det uttryckligt tillåtna statiska granskningsmanifestet och påverkar inte initial nätverksladdning.
- Den tidigare högerskrollade mobila resultattabellen var ett tillstånd i QA-harnessen, inte dokumentoverflow. Tabellen har lokal scroll, synlig svepanvisning och börjar nu korrekt med år/distans i granskningsbilderna.
- Historiska upplagor utan godkänd GPX visar avsiktlig tomstatus. Ingen modern rutt lånas.
- Tostared 2025/43 finns korrekt som metadata med noll TIME men skapar inget falskt segment. Grind → Torrås är fortsatt den observerade bron med n=130 och sju effektiva segment.
- `Torrås → Almered` 2023/2024 behåller verkliga tider men undertrycker fysisk pace där timingdistansen är osäker.

## Visuell Chromiumgranskning

Jämförelse gjordes mot `docs/assets/design-reference.webp`, den låsta Hero-bilden och fullsidiga Chromiumrenderingar.

| Viewport | Resultat |
| --- | --- |
| 1440 × 900 | Hero, tre familjekort, tvåkolumnslayout, KPI, diagram, D21-axel, karta/loppplan, historik, proveniens, grupper, resultat, metod och footer granskade. Inget dokumentoverflow. |
| 900 × 900 | Hero/crop, navigation, familjekort och tvåkolumnslayout behåller balans och läsbarhet. Inget dokumentoverflow. |
| 768 × 900 | Mellanbredden behåller full navigation, korten ligger inom viewport och text/knappar klipps inte. Inget dokumentoverflow. |
| 390 × 844 | Mobilmeny, staplade familjekort, upplageväljare, KPI, alla analyskort, vald segmentmarkering, lokalt scrollande tabeller, svepanvisningar, karta, loppplan, profil, Replay, direktjämförelse och kartduell granskade. Inget dokumentoverflow eller dialogoverflow. |

Hero, typografi, skogsgrön palett, guldaccent, ytor och fokusmarkering följer designreferensens godkända uttryck. Initialavatarer används; inga externa personbilder har införts.

Lokala, ej committade QA-bevis:

- `C:\Git\satila-final-visual-qa\reports\qa-final\satila-1440.png`
- `C:\Git\satila-final-visual-qa\reports\qa-final\satila-900.png`
- `C:\Git\satila-final-visual-qa\reports\qa-final\satila-768.png`
- `C:\Git\satila-final-visual-qa\reports\qa-final\satila-390.png`
- `C:\Git\satila-final-visual-qa\reports\qa-final\map-duel-{1440,900,768,390}.png`
- `C:\Git\satila-final-visual-qa\reports\qa-final\interaction\profile-{1440,900,390}.png`
- `C:\Git\satila-final-visual-qa\reports\qa-final\interaction\duel-{1440,900,390}.png`
- `C:\Git\satila-final-visual-qa\reports\qa-final\interaction\duel-map-{1440,900,390}.png`

De stora genererade PNG-filerna är medvetet inte committade.

## Full regression på implementations-SHA

Godkänt:

~~~text
node --check docs/assets/app.js
node --check docs/assets/analytics-extra.js
python tools/run_release_candidate_checks.py --all
python tests/browser_synced_scrub_acceptance.py
python tests/browser_all_editions_acceptance.py
python tests/browser_evidence_acceptance.py
python tests/browser_smoke.py
python tests/browser_release_selection_state_acceptance.py
~~~

Resultat:

- 27/27 historiska upplagor laddas på desktop och mobil.
- 3 272 resultat, 2 649 FINISHED, 128 DNF, 494 DNS, 1 UNKNOWN och 16 525 offentliga TIME-observationer.
- Fem checksumlåsta arrangörsrutter.
- Inga oväntade page errors, console errors eller saknade lokala fetches.
- Noll dokumentnivå-horisontell overflow på 1440, 900, 768 och 390 px.
- K03, K04, K05, T01 och T06 har passerat sina browsergrindar.
- 2025/43 Tostared/Grind–Torrås, 2023/43 n=8, 2016/85 två kvinnliga målgångar, DNF Okänt och 2023/2024 pace-grinden passerar.
- Mobilmeny, Escape, reduced motion, deep links, Back/Forward, profilsök/fokusåterställning, filter, sortering, pagination och editionslokalt urval passerar.
- Publiceringspaketet innehåller exakt 44 tillåtna statiska sajtfiler och inga privata råkällor.

Den tidigare fyrjobbsintegrationskörningen 36878403527 gäller baslinjen `790dcd78`. Denna nya feature branch är lokalt fulltestad men har inte felaktigt tillskrivits samma integrerade workflowresultat.

## Oförändrad källa och proveniens

`git diff e8a5be1..9426850 -- docs/data config` är tom.

- Inga race bundles, källfingeravtryck, coverage-filer, route-assets eller GPX-checksummor har ändrats.
- Inga råa EQ Timing-importer, `contestants.json`, privata deltagarspår, databaser eller arkiv har lagts under `docs/`.
- 2020 är fortsatt en lucka och inga 2026-resultat har skapats.

## Återstående

### Faktiska kvarvarande defekter

Inga reproducerbara kod- eller layoutdefekter återstår efter denna korrigering och fulla lokala regression.

### Funktioner spärrade av evidens

- K01/D23: fysiska checkpointankare och numerisk segment-D+/D−.
- K02: historisk tvåbanoverlay.
- D25: sammanhängande flerårig helbaneprestation.
- D26: jämförbara rekord över upplagor.
- Exakt geografisk DNF-avbrottspunkt.

Dessa kräver nya accepterade källor eller jämförbarhetsbeslut och har inte fabricerats.

### Ägarens visuella beslut

- Slutligt godkännande av fullsidans informationsdensitet och den exakta balansen mellan långa analyssektioner.
- Slutligt godkännande av Hero-beskärning och familjekort på de fyra skärmstorlekarna.
- Beslut om integration efter att alla fyra jobben i `.github/workflows/integration-candidate.yml` har körts grönt på den slutligt integrerade SHA:n och ett gransknings-ZIP har skapats från samma SHA.

