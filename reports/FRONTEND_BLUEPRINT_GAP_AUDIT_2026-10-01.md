# Frontend blueprint gap audit – Sätila Splits first draft

**Datum:** 2026-10-01  
**Granskad kod:** auditgrenens frysta first-draft frontend, framför allt `docs/assets/app.js` och `docs/assets/analytics-extra.js`.  
**Syfte:** Identifiera semantiska skillnader mot blueprint D01–D27/T01–T10/K01–K06/P0.1–P0.5 utan att ändra Codex frontend parallellt.

Den här rapporten säger inte att komponenterna är visuellt dåliga. Den skiljer mellan:
- **implemented** – kärnkontraktet finns,
- **partial** – relevant komponent finns men uppfyller inte hela blueprint-semantiken,
- **gated** – korrekt att bara finnas för vissa editioner/urval,
- **not-evidenced** – saknar idag källstöd,
- **release-fix** – liten men obligatorisk releasejustering.

## Viktigaste semantiska gapen

### D16 – Fartretention per segment: **PARTIAL / fel semantik i nuvarande kort**

**Ny källkontroll:** `tools/audit_segment_distance_capability.py` visar att fartdelen dessutom måste vara capability-gated per segment. Två publicerade timing-km-segment ger uppenbart orimlig fältmedianfart och får därför vara **time-only** tills distansen verifierats:
- 2023 43 km, Torrås→Almered: 16,0 timing-km, n=84, implicerad median 23,663 km/h.
- 2024 43 km, Torrås→Almered: 16,0 timing-km, n=58, implicerad median 20,285 km/h.

Detta underkänner **inte** TIME-observationerna. Segmenttiden är giltig; det är just omräkningen till fysisk fart/min/km som spärras.

Nuvarande `renderRetention()` i `analytics-extra.js` räknar:

> antal löpare med en faktisk TIME-observation vid kontrollen relativt den första analyserbara kontrollen

Detta är en legitim **passageretention/täckningsmetrik**, men det är **inte D16** i blueprinten.

D16 kräver ungefär:

> segmentets relativa fart mot eget eller gruppens hel-loppssnitt, där 100 = referensfart.

**Codex-krav:** behåll gärna passageretention som en separat datakvalitets-/fältflödesmetrik, men implementera D16 med faktisk segmentfart/tempo-retention där timingdistansen tillåter det. Använd inte GPX-polyline-längd som ersättning för timingsegmentens kontrakterade distans.

### D11 – Starkaste avslutning / sista delsträckan: **PARTIAL**

Nuvarande `renderFinishProgress()` analyserar placeringsförändring från kontrollen närmast före 2/3 av timingdistansen till sista observerade placeringen.

Det är intressant och källbaserat, men blueprint D11 efterfrågar den **senaste verifierade delsträckans relativa styrka**, exempelvis:
- faktisk sista segmenttid,
- relativt egen hel-loppsfart eller fältmedian,
- eventuell placeringsvinst på just sista segmentet.

**Codex-krav:** behåll “sista tredjedelens progression” som extra insikt, men komplettera med explicit sista-verifierade-segment-analys.

### D18 – Välj upp till fem klass-/åldersgrupper: **PARTIAL**

Nuvarande `renderSegmentGroups()`:
- samlar klassgrupper automatiskt,
- sorterar dem efter segmentmedian,
- visar upp till tio grupper.

Blueprint kräver en **användarstyrd** jämförelse av upp till fem klass-/åldersgrupper med gemensam segmentaxel.

**Codex-krav:** lägg till gruppväljare (max fem), tydlig legend och n per grupp. Ålder får bara användas när numerisk källålder finns.

### D19 – Grupp × delsträcka heatmap: **PARTIAL**

Nuvarande `renderHeatmap()`:
- använder automatiskt de sju största klasserna,
- visar relativ segmentmedian mot totalfältet,
- respekterar n>=5.

Det är metodmässigt bra, men urvalet är inte samordnat med D18:s användarval.

**Codex-krav:** heatmap och D18 ska använda samma valda analysgrupper.

### D13 – Klubb/ort deltagande och prestation: **PARTIAL**

Nuvarande `renderClub()` visar antal resultat per klubb/ort, topp 10.

Blueprint D13 kräver både:
- deltagande,
- prestation,
- möjlighet att välja några grupper,
- full tabell vid behov.

**Codex-krav:** komplettera med minst median/sluttidsmetrik vid tillräckligt n och gemensamt gruppurval.

### D12 – Ålder i 5-årssteg + åldersklass: **PARTIAL**

Nuvarande `renderAge()` använder grova grupper:
- ≤29
- 30–39
- 40–49
- 50–59
- 60+

Blueprint säger **5-årssteg + källstödd åldersklass**, och exakt ålder ska hållas separat från klass.

**Codex-krav:** använd 5-årsintervall när numerisk ålder finns; visa separat källklass utan att inferera ålder.

### D22 – Course Intelligence: **PARTIAL**

Nuvarande `renderCourseIntel()` visar:
- timingdistans,
- antal publika kontroller,
- median sluttid,
- DNF-andel,
- GPX-displaylängd,
- rå positiv GPX-höjd.

Det är korrekta separata dimensioner, men D22 kräver mer **segmentkopplad** Course Intelligence:
- stigning/geometri där tillåtet,
- pacing loss,
- spridning,
- placeringsrörelse,
- DNF,
- synk till vald delsträcka/karta/tabell.

**Codex-krav:** bygg D22 runt samma `selectedSegment` som segmenttabell/karta/höjd. Fortsätt uttryckligen undvika ett sammanvägt “svårighetsbetyg”.

### D20 – Fältets målprogression: **behöver explicit komponentverifiering**

Blueprint D20 är:

> tidpunkter då 10/25/50/75/90 % av fullföljarna gått i mål.

Nuvarande kod har måltidshistogram/percentiler och flera progressioner, men det finns inte en tydligt separat komponent vars kontrakt direkt motsvarar D20.

**Codex-krav:** antingen implementera en explicit målprogressionsvy eller visa tydligt att befintlig percentil-/målgångskomponent faktiskt uppfyller exakt 10/25/50/75/90%-kontraktet.

### D26 – Årets fingeravtryck/rekord: **PARTIAL**

Nuvarande `renderFingerprint()` visar fyra oberoende mått:
- volym,
- stationer,
- median,
- DNF.

Det är bra att inget syntetiskt index skapas. Men blueprinten anger även prestationsreferens/rekord inom verifierat jämförbara år.

**Codex-krav:** behåll de oberoende dimensionerna; komplettera endast prestationsdelen där explicit whole-course-grupp finns. Ingen jämförbarhetsgrupp = ingen rekordjämförelse.

## Komponenter där first draft redan ligger nära kontraktet

- **D01** KPI/status/denominator – metodiskt starkt och separat testat.
- **D02** sluttidshistogram – stabila bins och könsserier.
- **D03** percentiler – n-gating finns.
- **D04** kön × fullföljande – korrekt känd-startstatusnämnare.
- **D08** observerad måltid → placering – tydligt märkt som observerat fält, inte prognos.
- **D09** DNF sista verkliga observation – separat regression finns.
- **D10** placeringsresa – minst två faktiska placeringspassager.
- **D14/D15** median/Q25–Q75/Q10–Q90 – rätt n=5/10/20.
- **D17** kvinna/man segmentmedian – rätt n>=5 per kön.
- **D21** kontrollspridning – faktiska passager; saknat fylls inte ut.
- **D24** deltagande/statushistorik – 2020 behandlas inte som nollår.
- **D27** könsandel över tid – källstött kön och okänd täckning separat.
- **T01–T08/T10** har i huvudsak datakontrakt och UI-ytor; full Codex-release måste ändå browserverifieras.
- **K01/K03/K04/K05** har källkontrakt och first-draft-browserbevis på tillåtna 2025-editioner.
- **P0.1/P0.4/P0.5** har fungerande first-draft-kärnor och separat browser-QA.

## K02 – Historisk banjämförelse: **BLOCKED BY EVIDENCE, inte frontendfel**

Detta är viktigt att inte “fixa” genom att låna en modern bana bakåt.

Det finns deltagarbaserade 43-km-kandidater:
- 2021–2022,
- 2023–2025,

men de är ännu inte promoted till auktoritativa publicerbara CourseVersions i current source contract.

**Rätt UI:** saklig tomstatus + förklaring. Inte en falsk historisk overlay.

## P0.2 – Podium kvinnor/män: **implemented men måste förbli source-count-aware**

2016 85 km har bara två kvinnliga FINISHED. Nuvarande och framtida UI ska:
- visa två kvinnor,
- inte skapa brons,
- inte skapa könsmedian n<5.

## P0.3 – Individuell analys: **implemented core, men kan fördjupas**

First draft har:
- profil,
- observerade segment,
- placeringsresa,
- jämförelse,
- replay när route tillåts.

Codex bör lägga på den rikare berättelsen från blueprinten:
- starkaste/svagaste verifierade segment,
- största relativa gain/loss mot fält,
- tydlig sista-segmentstyrka,
- vändpunkter,
- varje insikt med n/metod.

## Release-specifika text-/navigationsgap

Separata tester finns:
- `tests/test_release_copy_acceptance.py`
- `tests/browser_release_navigation_acceptance.py`
- `tests/browser_release_ux_acceptance.py`

De ska fånga:
- “Samma stigar”,
- “GOTALENDETS”,
- Back/Forward/deep-link history,
- Escape för mobilmeny,
- fokus efter dialog,
- synligt error-state.

## Rekommenderad Codex-prioritet

1. Behåll den käll-/metodlogik som redan är verifierad.
2. Korrigera **D16** så att fartretention faktiskt är fartretention.
3. Separera **D11** sista segmentstyrka från “sista tredjedelens placeringsprogression”.
4. Gör **D18/D19** gemensamt användarstyrda med max fem grupper.
5. Fördjupa **D13/D12/D22/D26** enligt ovan.
6. Verifiera **D20** explicit.
7. Kör hela release-browser-QA på den integrerade kandidaten.

**Ingen av dessa punkter kräver ny EQ Timing-import eller ombyggnad av de 27 race-bundlarna.**
