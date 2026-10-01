# Sätila Splits – huvudspecifikation och sprintstyrt byggkontrakt
Version 1.0 · 2026-10-01 · Status: BYGGBESLUTSUNDERLAG (ingen frontend implementerad i detta dokument)

## 0. Uppdrag, definition av klar och arbetsregel

Bygg ett **komplett, granskningsbart första utkast** för Sätila Trail Run med tre huvudfamiljer (`ultra85`, `trail43`, `trail22`), officiella resultat och verkliga EQ Timing-passager där de finns, verkliga lokalt godkända GPX-/ruttassets där sådana finns, historik, analyser, profil, jämförelse, karta och replay **endast när underlaget medger det**. Utseende: en egen Sätila-identitet, inte klonad ÖST-kust eller Ultravasan-vinter.

Ett granskningsbart utkast innebär: publicerbar statisk `docs/`-app med riktig, normaliserad data; alla tre distanser kan väljas; resultatdatabas/profiler/översikt fungerar för tillgängliga år; splitberoende analys visas automatiskt där faktisk datatäckning finns; minst en tillåten kart-/replaykontext är demonstrerbar om lokala filer faktiskt finns; CI + Chromium går grönt; rapport visar alla avsiktligt inaktiva funktioner. Ingen dummydatabaserad skärm eller tyst lånad rutt räknas som klar. Ingen publicering på loppanalys.se utan separat distributionsgrind.

**Bygg när uppdraget ges, utan nya designvalfrågor:** genomför sprint 0→11 i ordning; spara kod och verifierad status efter varje sprint; om en valfri funktion blockeras av bristfällig källdata, registrera begränsningen och fortsätt. Stoppa enbart vid blockerande fel som skulle ge falska data eller en osäker publicering. Ingen asynkron fortsättning antas: varje körning lämnar ett körbart commitläge och maskinläsbar återstartspunkt.

### Frysta referenser (inventerade i GitHub)
- Ultravasan 2.0: `Stayinhealthyrunning/ultravasan-analys@8d1ef31c7a820a594adf89783453154ccab4751e`; särskilt `docs/assets/{runner-replay,runner-analysis,course-intelligence,history-intelligence,data-loader,map-engine}.js` och `reports/U4–U8`.
- Gotaleden: `Stayinhealthyrunning/gotaleden-splits@bd9f2aaf0466f2ad65b50d35e25981e4597350f1`; särskilt `docs/assets/{charts,interactive-analysis,course-difficulty,goal-pace,map-duel,head-to-head,profile-journey,analysis-help}.js`, `reports/ENGINE_1_0.md`, `config/engine-contract-v1.json`.
- ÖST: `Stayinhealthyrunning/osterlen-spring-trail-analys@f30619f6a967210b416d8bd604acd92a928a9052`; särskilt `docs/assets/{app,views,charts,map-engine}.js`, `config/{analysis-feature-policy,frontend-performance-budget}.json`, `reports/{OST_SPLITS_BUILD_REPORT,OST_SPLITS_VISUAL_QA,OST_SYSTEM_AUDIT_2026-09-29,OST_UX_PARITY_GAP_ANALYSIS}.md`.
- Sätila startpunkt: `Stayinhealthyrunning/satila-splits@0a5d5fbce305f68d5f8f50a46dff8d397df83509` på `main`; öppen PR #1 `setup/foundation` innehåller separat GPX-/proveniens-/coursearbete. **Båda spåren måste förenas**. Kontrollera nya commits innan implementation börjar.

Detta är en källkods-/kontraktsgranskning kompletterad med respektive projekts browser- och visuella QA-rapporter, inte en påstådd ny manuell pixelgranskning av alla publicerade webbsidor. Bedömningen nedan är ett designbeslut för Sätila, inte ett objektivt poängsystem för de tre produkterna.

## 1. Beslut på systemnivå: vad återanvänds varifrån?

| Lager / produktdel | Primär referens | Sekundär referens | Sätila-beslut |
|---|---|---|---|
| Semantisk domänmodell | Gotaleden Engine 1.0 | UV U1/U2 | Event → RaceFamily → RaceEdition → CourseVersion; source-bound appearance, status, split. |
| Källsäkerhet, datakapabiliteter | ÖST | UV U6/U7 | Feature per edition; källstatus och n/exakta passager styr, inte distansnamn. |
| EQ Timing import | Sätila nuvarande import | Gotaleden EQ-adapter | Återanvänd råarkiv; bygg en adapter, duplicera inte scrape/logik. |
| Webbleverans/prestanda | ÖST | UV U3 | Bootstrap + vald race bundle; historikaggregat on demand; karta/höjd/replay lazy. |
| Frontendens sidflöde och kompakt layout | ÖST efter UX-rundan | Gotaleden komponentkontrakt | Hero → Individ → Lopp/upplaga → Översikt → Dynamik → Delsträckor → Bana → Historik → Metod; Resultatdatabas separat tydligt verktyg. |
| Personprofil och djup Replay | Ultravasan U5 / runner-replay | ÖST:s kompakta profildialog | Journey, jämförelsemarkörer, karta direkt i modal där stödd, hover/sök i höjdprofil. |
| Direktjämförelse (exakt två) | Gotaleden | ÖST:s kompakta modal | Gemensam passage-/segmentduell, tidsgap, placeringsresa, kontext. |
| Kartduell (2–5) | Gotaleden map-duel | UV MapEngine/Playback + ÖST fallback | Samma race/kompatibel bana, tidslinje, markörer, höjdprofil, tillgängliga kameraval. |
| Basdiagram och interaktivitet | Gotaleden charts | ÖST charts/visual QA | SVG med könstoggles, förklaring, filter och tabellalternativ; undvik duplicerade diagram. |
| Fördjupad kurs-/segmentanalys | UV U6 | Gotaleden course-difficulty | Synkat segmentval för rutt, höjd, fart och segmenttabell; separata verifierbara dimensioner, **ingen sammanvägd syntetisk svårighetspoäng**. |
| Loppplan/måltempo | UV U6 beräkningskontrakt | Gotaleden goal-pace | Samma CourseVersion/explicit kohort, medianfördelning; märkt distansfallback. |
| Flerårig historik | UV U7 | ÖST:s historik/fingeravtryck | Deltagande alla källstödda år; prestation endast i explicit whole-course comparison group. |
| Metodhjälp och tillgänglighet | ÖST QA / UV U8 | Gotaleden help | Kort lokal (i) på varje analyskort, full metod sist, keyboard och reduced motion. |
| Visuell särprägel | Ny Sätila-identitet | ÖST:s fotohero och kortbalans | Skog, sjö, höst, stig; egen kvalitativ bild/illustration; ingen lånad Österlen-/Vasaloppsmedia. |

**Återanvänd matematiska och semantiska kontrakt, inte tre parallella frontendkopior.** Gör en Sätila-adapter och samlade komponenter. Importera endast faktiskt kompatibel JS/kod med kontrollerad anpassning, behåll proveniens för återanvända moduler.

## 2. Startdata och källgrind

### 2.1 Resultat
`main` innehåller `config/eqtiming-events.json` med verifierade event-ID 2016:25781, 2017:35491, 2018:43641, 2019:49225, 2021:57767, 2022:62409, 2023:67695, 2024:72918, 2025:77864. Historiska distansnamn 2016–2019 ska mappas till familjer med bevarad originalklass/distans: 80/82/85, ~42/43, 21/22, utan att låtsas att banorna är samma. 2020: ingen konfigurerad edition; ange **ej verifierat i denna import** tills källstatus utretts, inte noll deltagare. Höstens 2026-upplaga är ännu framtida den 1 oktober 2026: katalogstatus `planned` endast med tillförlitlig eventkälla, aldrig konstruerade resultat.

Actions-import `36818159977` lyckades 2026-10-01; råarkivet `satila-eqtiming-raw-36818159977` (~6,6 MB ZIP) har 30 dagars retention. **Säkra/avläs arkivet i sprint 0, före utgången; detta är ännu inte en incheckad kuraterad databas.** Råa event-/contestants-/publika station-/resultatsidor och manifest bevaras; kontrollera konkret antal och datakvalitet mot samtliga råfiler. Ingen summerad resultatobservationssiffra får förväxlas med unika målgångar: samma person förekommer på flera stationer.

### 2.2 Geometri (rapport från tidigare arbete; verifiera fysisk åtkomst vid byggets preflight)
- `trail43` fem verkliga Suunto/Sports Tracker-deltagarspår 2021–2025. PR #1:s analys: två tydligt skilda kursfamiljer: 2021–2022 och 2023–2025. PR:n har checksummor för **sanerade normaliserade kandidater**: tidig 44,415 km / 1091 punkter, sen 41,595 km / 944 punkter. GPX-deltagaruppgifter får inte offentliggöras. Felvägar i råspåren för 2021/2022 är dokumenterade; omedelbart användbara analyskandidater är inte automatiskt officiella banor.
- `ultra85` spår har identifierats för 2021–2025 genom tidigare Trace de Trail-/uppladdningsarbete; 2023 cirka 84,91 km, 2024 cirka 84,92 km och ultramarathon.se:s publicerade 2025-spår cirka 87,08 km. **Filerna finns inte som incheckade filer på Sätilas main vid denna granskning**. Kontrollera bytes/checksum innan markerade `route_available=true`; 2023/2024 och 2025 får separata kandidater i väntan på geometrijämförelse.
- `trail22`: ett identifierat Wikiloc-spår från 2019 (cirka 22,38 km) är ett forskningsspår, inte en bevisad lokal och godkänd GPX för 2021–2025. Första utkastet kan och ska ha fullt resultat-/statistik-/profilstöd för 22 km även utan karta, ruttbaserad fart, replay eller kartduell. Ingen lånad 43 km-rutt och ingen påhittad GPX.
- Behåll originalkällans typ och tillgänglighetsstatus: `OFFICIAL_ORGANIZER`, `ITRA_TRACE`, `RACE_TRACKER`, `VERIFIED_PARTICIPANT`, `RECONSTRUCTED`. Skilj evidence, normalized route candidate, approved public display asset, exakt officiell CourseVersion och jämförbarhetsgrupp. Original-GPX med namn/tidsstämplar ska inte commitas publikt. Skapa sanerade `route.json` och `elevation.json` först efter verifierad filåtkomst.

### 2.3 Kontrakt
Implementera `loppanalys-engine-1.0` från Gotaleden utan att förväxla family med course-version. Resultat är race edition-bound appearances; käll-UID är konservativt eventscopat tills annan identitet är bevisad. Timingdistance och GPX-displaydistance skiljs. En officiell aid station utan publikt timingpayload är **inte** en källstyrkt split. Auxiliary/speaker-tider får endast fungera som tydligt deklarerade ankarpunkter.

Två oberoende jämförbarheter:
1. `same_course_version`/explicit compatible checkpoint-segment key för segment.
2. `whole_course_comparison_group` explicit styr flerårig helbanetid/fart/rekord. Samma nominella 85 eller 43 km räcker inte. Undvik automatisk promotion av preliminära 43 km-grupper till definitiv `exact` whole-course-paritet.

## 3. Slutlig informationsarkitektur, uppifrån och ned

1. **Hero / Sätila Splits:** egen bred skogs-/höstidentitet; rubrik, löparsök (namn, startnummer), knappar `Hitta en löpare`, `Utforska loppen`, `Jämför`; låg höjd, vänstertoning, mobilanpassning.
2. **Distans- och årväljare:** 85 km / 43 km / 22 km som tydliga lika stora familjekort eller knappar, källstödda år 2016–2025 per familj; ändrat historiskt officiellt distansnamn visas under rubriken. Förvalt år = senaste **genomförda med resultat**, i nuläget 2025.
3. **Sticky sektionsnavigation:** Översikt · Loppets dynamik · Delsträckor (när stödd) · Bana · Historik · Metod. Resultatdatabas öppnas från egen tydlig navigationsåtgärd. `aria-current`; utan deep link alltid scroll högst upp.
4. **Individverktyg nära toppen:** Sök med tangentbordsautocomplete → profildialog. Favoriter lokalt per publicerat result-ID. Jämför använder vald-räknare/Rensa val; Direktjämförelse 2 resultat; Kartduell 2–5 när replay-grinden klar.
5. **Välj lopp & upplaga + filter:** år, distans, källbadge, antal rapporterade/filtrerade. Gemensamma filter: kön (endast källa), klass, status, klubb/ort, tempoenhet min/km eller km/h; återställ. Person- och jämförelsesök påverkas inte i tysthet av fältfilter.
6. **Översikt:** KPI-rad → Måltider och percentiler i balanserad tvåkolumnsrad → kvinna/man och klasser i balanserad rad. Inga onödiga fristående fullbreddskort.
7. **Loppets dynamik:** Status + Fältflöde, därefter Tid mot placering, könsstatus + DNF-lokalisering, Starkt avslut, ålder och klubb/ort. Visa inte duplicerad percentiltrappa här.
8. **Delsträckelabb (när faktiska splits finns):** median/spridning, retention, placeringsresa, valbart segment, gruppjämförelse, avrinnings-/DNF-tabell, observerad prestationslista.
9. **Bana & loppplan:** proveniens först; lokal rutt och synkad höjdprofil där godkänd; först därefter terräng-/pacingkombination och måltempo med metod/fallback. För result-only: saklig ruttstatus utan tom kartmodul.
10. **Historik:** årstabell och volymtrend för hela dokumenterade familjen; fingeravtryck, rekord och prestation med whole-course-gating; banversionsband och explicit luckor.
11. **Metod:** full beskrivning av källa, datum, tillstånd, distansaxlar, urval, n, formel, GPX-proveniens, CourseVersion och jämförbarhetsregler.
12. **Resultatdatabas (separat fokuserad vy/del):** alla rader, sök/sort/paginering, tydlig avgränsning år/familj/status, klick/tangentbord till profil. Samma dataadapter som analysen.

## 4. Diagram-för-diagram: Sätilas obligatoriska visuella kontrakt

I tabellen betyder A = alla race editions med tillräckliga finishdata, S = splitbaserat, G = godkänd lokal geometri, H = historik, D = källstödd demografi. Saknad kapabilitet leder till meningsfull beskrivning eller dolt kort, **aldrig fiktiv serie**.

| # | Diagram / kort | Basreferens | Datakrav | Interaktion och utformning |
|---|---|---|---|---|
| D01 | KPI: anmälda/registrerade där känt, startande, fullföljare, DNF/DNS/DSQ/UNKNOWN, median, completion | ÖST | A; statuskällor explicit | n och denominator, status är skilda mängder. Inget null→0. |
| D02 | Måltidshistogram i fasta konsekventa intervall | Gotaleden charts + ÖST könsserie | A; D för kön | All/F/M toggle, hover antal/tidsintervall, urval vs total; samma bin-gränser vid könsväxling. |
| D03 | P10/P25/P50/P75/P90 och kumulativa målgångsstaplar | ÖST/UV | A | Gemensam tröskelaxel; när D finns separat kvinna/man med n; inte dubblerad senare. |
| D04 | Könsöversikt / completion | ÖST | A+D | Källstödda kön; egen statusdenominator; okänt kön som egen täckningsuppgift. |
| D05 | Klassfördelning | ÖST visual polish | A och verifierade klasser | 5–6 prioriterade horisontella staplar, klick = klassfilter, hela tabellen expanderbar. |
| D06 | Statusfördelning + Fältflöde kontroll för kontroll | Gotaleden/ÖST | A; S för fältflöde | Källa observerad passage; skippa trivial Start=100%; räkna inte "saknas" som DNF. |
| D07 | Tid mot totalplacering (scatter) | Gotaleden med ÖST klikbarhet | A med placering | Tooltip namn/tid/klass; klick/Enter öppnar profil; zoom/reset; D-toggle om stödd. |
| D08 | Vad krävs? Måltidssimulator / placeringströskel | Gotaleden | A och faktisk sluttidsfördelning | Ange måltid, visa observerad placering/percentil i vald edition; inte prognos för nästa år. |
| D09 | DNF:s sista observerade kontroll | UV U6 / ÖST | S, dokumenterad DNF | Sista exakta passage; visa okänd plats separat; ingen extrapolerad brytpunkt. |
| D10 | Största avancemang/placeringsresa | Gotaleden | S + officiella positionspar | Start/slut, vunna platser, n; ingen ranking på estimerade positionspar. |
| D11 | Starkaste avslutning / sista delsträckan | UV U7 + Gotaleden | S, separat verifierad sista timingkontroll före mål | Separat senaste segment, normalisera ev. placeringvinst mot startfält; annars dölj. |
| D12 | Ålder i 5-årssteg + åldersklass | ÖST QA | D (exakt ålder vs klass separeras) | Kompakta staplar; analytiska grupper valbara utan inferens av exakt ålder ur klass. |
| D13 | Klubb/ort deltagande och prestation | Gotaleden interactive analysis | Källstödd klubb/ort och A | Horisontella staplar; välj högst fyra grupper, behåll full tabell på begäran. |
| D14 | Segmentmedian med Q25–Q75 | Gotaleden charts | S, minst 5 exakta segmentpar för median; ≥10 band | Hover/tangentbord väljer segment; tidsbaserad vy om officiell segmentdistans saknas. |
| D15 | Q10–Q90 detaljband | Gotaleden/ÖST | S och n≥20 | Visa i fördjupad segmentvy med tydlig n; undvik falsk precision. |
| D16 | Fartretention per segment | UV U8 + Gotaleden | S, finish och kontrakterad segmentdistans | 100 = eget/gruppens hel-loppssnitt; tydlig referenslinje och medianbaserad redovisning. |
| D17 | Kvinna/man-pacing per segment | Gotaleden/ÖST | S+D, tillräckligt n per grupp | Toggla serier utan att flytta tidsaxel; jämför inte populationer med helt olika källtäckning oannonserat. |
| D18 | Välj upp till 5 klass-/åldersgrupper, medianfart/retention | Gotaleden | S, D eller källklass | Samma segmentaxel och urval; grupplinjer med legend, små n markeras. |
| D19 | Analysgrupp × delsträcka (heatmap) | Gotaleden | S + klass/grupp | Visa värde + n i cell; tomma celler = saknad evidens, inte nolltempo. |
| D20 | Fältets målprogression | Gotaleden | A | Visa tidsnivåer då 10/25/50/75/90 % av fullföljare är i mål; definiera denominator. |
| D21 | Fältets spridning genom kontroller | Gotaleden | S | Samma giltiga kohort eller märk när populationen förändras. Officiell/källstödd passage. |
| D22 | Course Intelligence: stigning, pacing loss, spridning, placeringsrörelse, DNF | UV U6; Gotaleden course-difficulty | S+G samt tillräcklig evidens per mått | Visa dimensionerna separat, inte övergripande svårighetsindex; synka vald delsträcka med karta och tabell. |
| D23 | Banhöjdprofil | Gotaleden elevation + UV synkning | G med höjd | Samma route-distance som karta, markera verifierade checkpoint-ankare, saknad höjd bryter kurva; ingen falsk D+/D−. |
| D24 | Historik: startande/fullföljare/DNF och källstatus per år | UV U7/ÖST | H | Verkliga källår, luckor ej noll; ingen banjämförbarhetsrestriktion för rena volymer. |
| D25 | Historiska mediansluttider, fart, klassutveckling | UV U7 | H + explicit whole-course comparison group | Avbruten linje/versionsband vid ändrad bana; ett år i egen grupp är ensamt. |
| D26 | Årets fingeravtryck/rekord | UV U7 + ÖST komprimering | H; prestationsindex kräver ≥2 andra jämförbara år | Prestationsreferens per jämförbart år; deltagande kan visas över hela familjen. |
| D27 | Historisk kvinna/man-andel | ÖST | H+D, täckning | Redovisa täckning och skilj saknat från 0; ÖST:s 80%-regel för könstrend kan återanvändas. |

**Diagramprinciper:** konsekvent färgsemantik och formattering; en korrekt tabell-/textrepresentation av nyckeltal; inte fler än en visuell bärare av samma mått per sida; explicita filtrerade populationer; aktiva könsserier får styras individuellt; diagram får inte tyst ladda hela historikdatabasen.

## 5. Tabell-för-tabell och textvyer

| # | Tabell / vy | Referens | Sätila-kolumner / acceptans |
|---|---|---|---|
| T01 | Resultatdatabas | Gotaleden + ÖST | Plac, namn, startnr, klass, kön vid källstöd, klubb/ort, status, officiell sluttid, år/distans; sort/filter/pagination och profil med tangentbord. |
| T02 | Officiella passager (profil) | UV RunnerAnalysis/Journey | Kontrollens källnamn, kumulativ tid, split sedan föregående verifierade kontroll, officiell/observerad placering där källan ger den, evidensstatus; saknat förblir saknat. |
| T03 | Löparens segment och relativ prestation | ÖST profil + UV U5 | Segment, distans från timingkontrakt, segmenttid, min/km om tillåtet, fältmedian samma segment/kohort, differens och n. |
| T04 | Segmentlabbet | Gotaleden | Från/till, distans, n, median, Q25–Q75, retention, placeringsrörelse, DNF observationer och proveniens. |
| T05 | Direktjämförelse | Gotaleden head-to-head | Två resultat, respektive passagetid, tidslucka, delsträckstid, fart om möjligt, officiell placering, diagram över lucka. Ingen falsk cross-course jämförelse. |
| T06 | Loppplan | UV U6 | Start/kontroll/mål, historisk andel eller explicit distansfallback, segmentmåltid, ack. måltid, målfart, evidens och komplett/ofullständig. |
| T07 | Banversioner och källa | Sätila/ÖST | Family, edition, marknadsdistans, GPX-displaydistans, CourseVersion-ID, whole-course-grupp, källtyp, fil/checksum, verifieringsgrad, tillåten publicering och olösta konflikter. |
| T08 | Historiska år | UV U7 | År, datum, marknadsdistans, deltagare/status, finishmedian om giltig, jämförbarhetsgrupp, route-status. |
| T09 | Klasser/ålder/klubb | Gotaleden/ÖST | KPI per grupp; väljbar graf först, fullt dataset i utfällbar/paginerad tabell. |
| T10 | Käll- och täckningsinventering | ÖST reports | Edition, antal resultat/fullföljare, antal verkliga splitpassager, timingkontroller, status/kön/ålderstäckning, geometri, replay och kommentarer. Exportera även som JSON för CI. |

## 6. Karta-för-karta, banversioner och replay

**K01 – Översiktskarta (Gotaleden + ÖST):** lokal godkänd route asset för vald CourseVersion, OpenStreetMap via vendrad Leaflet 1.9.4; start/mål och endast explicit förankrade checkpoints. Visa GPS-källa/status i närhet av kartan. Höjdprofil i samma route-distance. Ruttens observerade polyline-längd får inte användas som ersättning för officiell tävlingsdistans.

**K02 – Historisk banjämförelse (UV map/historik + Sätila-geometri):** val av max två år inom samma family; två rutter med egen färg och legend; representera gemensam/avvikande korridor och start/mål. Om någon edition saknar godkänd route asset visas orsaken i stället för närliggande års rutt. Här är 43 km 2021–2022 kontra 2023–2025 den första naturliga jämförelsen; märk rutterna som kandidater tills de verifierats officiellt.

**K03 – Synkad segmentkarta / Course Intelligence (UV U6):** klick i karta, höjdprofil, fartfördelning eller segmenttabell ändrar ett och samma `selectedSegment`. Vyn visar valt intervall, riktiga positionsankare, terrängmått och pacing utan att ändra källpassager.

**K04 – Löparens Replay (Ultravasan U5, med ÖST:s bättre modal/fallback):** karta direkt i profilen när `observed_elapsed_split_passages + local_route_asset + >=2 semantic checkpoints`; interpolera position enbart **mellan riktiga timingankare**. Visa tydligt `beräknad position mellan kontroller`; DNF stannar vid sista verkliga passage; ingen Replay för finish-only. Uppspelning 30/60/120/180 s, 120 s standard; pausa, starta om, slider, höjdskrubber, följ löpare, visa hela bana. Referensmarkörer för fält/klass/kön endast med källstödd kohort. Ljud/musik är frivilligt och avstängt som standard i första Sätila-utkastet; inte ett blockerat releasevillkor.

**K05 – Kartduell (Gotaleden):** 2–5 källstödda resultat inom edition med godkänd lokal rutt och minst två faktiska ankare; gemensam tävlingsklocka, leaderboard, höjdsynk, speed, start/stop/reset, kameralägen. Ingen duell över två olika course versions förrän explicit geometri-/checkpointkontrakt tillåter exakt mening. Direktjämförelse med **två** resultat fungerar textuellt även utan rutt om officiella sluttider finns; segmentduell kräver gemensamma observerade analysgränser.

**K06 – Neutralt kartfallback:** om Leaflet/tiles inte laddar visas egen lokal rutt som SVG och all resultatdata fortsätter fungera. Om route asset verkligen saknas: ingen vilseledande linje, utan saklig tomstatus.

**Checkpointpolicy:** `source_label`, `semantic_key`, `sequence_no`, `analysis_boundary`, `replay_anchor`, `nominal_cumulative_km`, `race_distance_km`, `route_distance_km`, `exact_observation` är skilda fält. Sortera explicit kronologiskt, aldrig efter felaktig API-ordning eller alfanumerisk nyckel. Använd monotona route-ankare för projektion. Särskilda extra tracker-/speakertider upphöjs inte automatiskt till analytiska segment.

## 7. Mät-/analysregler (bindande)

- `FINISHED` kräver källa och positiv sluttid. Håll `DNF`, `DNS`, `DSQ`, `UNKNOWN` isär. En DNF med motsägelsefull måltid blir inte automatiskt finisher; råfält bevaras.
- Start=0 i timingmodellen. En giltig segmentobservation kräver två exakta gränspassager och positiv differens. För fart krävs explicit kontrakterad segmentdistans. Ingen interpolerad Replay-punkt återförs till analysdatabasen som split.
- Medianer för små grupper: n≥5; Q25–Q75 n≥10; Q10–Q90 n≥20. Visa n bredvid måttet. Detta är överförd konservativ ÖST/Gotaleden-policy.
- Pacing index för löpare: `100 * (hel_lopp_sek / kontrakts_km) / (segment_sek / kontrakts_segment_km)`. Över 100 = snabbare på segmentet än eget snitt; under 100 = långsammare. Gruppmedian av individindex eller explicit vald metod; blanda inte mått semantiskt.
- Placering ±: `plats_vid_startkontroll - plats_vid_slutkontroll` endast på officiella/källstödda positionspar. DNF-frekvens per segment endast från sista säkra passage och definierad entrékohort.
- Fältmedian, jämförelsemarkörer och banpacing ska ha dokumenterad population; använd gärna samma kompletta FINISHED-kohort på alla relevanta segment för konsistenta relativa kurvor, annars markera varierande n.
- Måltid `T` fördelas med observerade medianandelar `segmenttid/sluttid` endast inom tillåten identisk CourseVersion; när minst fem observationer saknas får **explicit kontrakterad segmentdistans** användas som märkt fallback. Inget resttidsgissande vid saknad både observation och distans. Måltidssimulator baserad på aktuella fullföljartider är deskriptiv, inte prognos.
- Kvinna/man bara från källstödd kod, aldrig namn; ålderskategori är inte exakt ålder; klubb/ort är källtext med normaliseringspolicy.
- Flerårig helbaneprestation/rekord/mediansluttid kräver explicit `whole_course_comparison_group`; volymer/status kan beskrivas även över banbyten. Ingen "mest förbättrad"/"flest lopp" utan verifierad åröverskridande personidentitet.
- Historik-fingeravtryck: minst två andra uttryckligen jämförbara loppår för prestationsindex, median av årsaggregerade värden (inte storleksviktat sammanlagt startfält); visa källår.
- Ingen syntetisk difficulty-summa. Redovisa separata verkliga mått: D+/km, pacing loss, IQR, placeringsrörelse och DNF-exit med respektive egen datatäckning.
- GPS-höjd glättas försiktigt med reproducerbart förfarande. Avbrott i höjddata får inte skapa fabricerad höjdskillnad. Skilj klockbarometer/GPX, extern DEM och ofullständig höjdprofil.

## 8. Kapabilitetsmatris per race edition (genereras vid build)

Varje `race_key` ska få `config/analysis-feature-policy.json`-liknande maskinläsbar readiness. Inget hårdkodat `if (family==='trail22') disable replay`; det är faktiska källor som styr. Första preflight-rapporten visar för varje family/år:

| Capability | Minsta källa | Om saknas |
|---|---|---|
| Results/overview/individual profile | Resultatrader, korrekta statusar | Visa `planned/unavailable` i katalogen, inte tom nollstatistik. |
| Finish distribution, percentile, placement | FINISHED och numeriska fält | Visa tydligt otillräckligt n. |
| Split/flow/pacing | Verkliga publicerade passager vid semantiska gränser | Visa översikt/resultat utan segmentkort. |
| Sex/age/class/club | Källstödd metadata med coverage | Dölj motsvarande tolkning eller ange täckning. |
| Elevation/course map | Godkänd lokal route/elevation med checksum | Källa/proveniens går fortfarande att läsa; ingen fallback till annan edition. |
| Replay/map duel | Faktiska tidsankare + lokal route + ≥2 kontroller | Direktjämförelse utan rutt om sluttid finns; ingen falsk replay. |
| Goal pace | Verifierad CourseVersion + observerade andelar eller kontraktsdistanser | Visa partiell plan och saknad segmentallokering, inte uppfunna tider. |
| Whole-course history | Explicit comparison group | Endast separata år och deltagandetrend. |
| Person history | Dokumenterad confidence-bearing cross-year-identitet | Visa lopp endast för vald appearance. |

## 9. Frontend, prestanda och visuellt kontrakt

- Basera renderingsmönster på ÖST:s moderna `app.js` + `views.js` (hellre uppdelade viewmoduler under Sätila än en 120 KB fil), Gotaledens diagram- och analysfunktioner och UV:s geometri/replay-komponenter. En gemensam `DataAdapter`, `HistoryEngine`, `MapEngine`, `Playback`, `ResultStatus`, `AppState`, `Analytics`, `Help`. Ingen lokal kopia av median/quantile eller personidentitet i enskilda vyer.
- Exportera statiskt under `docs/` med relativa URL:er och kompatibelt GitHub Pages basepath. Ladda `bootstrap.json` (katalog, race metadata, provenance), sedan endast vald `races/<race-key>.json`. Liten `history-aggregate.json` on demand. Rutt/höjd/Leaflet/replay lazy.
- Inledande prestationsbudget (från ÖST, tills mätt mot Sätila): bootstrap ≤10 KiB gzip, vald edition ≤75 KiB gzip och ≤600 KiB raw, tillsammans ≤100 KiB gzip; JS ≤256 KiB gzip, CSS ≤75 KiB gzip, HTML ≤32 KiB gzip, kritisk initial kod/data ≤512 KiB gzip. Om verklig Sätila-edition överskrider budget: analysera och dokumentera/justera med mätning, inte skär bort resultat.
- Egen layout: mörk skogsgrön/petroleum, neutrala ljusa ytor, varm höstaccent, högkontrast, kompakt hero med korrekt skarp Sätila-bild; egen markering för 85/43/22. Behåll ÖST:s balanserade tvåkolumnskort, lokalt scrollande breda tabeller och konsekvent rubrikhierarki. Ingen bild får förstöra LCP eller ge missvisande banfoto.
- Tester vid 1536×1024, 1366×768, 900×900, 390×844: ingen document overflow, fullt brukbara modaler, table-local scroll, knappar inom viewport. Skip-link, fokusåterställning, Enter/Escape/Arrow-tangentstöd, `prefers-reduced-motion`, läsbar legend utan färgberoende.
- Metod per kort: `Vad visas?`, `Källa/urval`, `Beräkning`, `Minsta n`, `Jämförbarhet/felkälla`. Fullständiga metodblad sist.
- De tre systerverktygen ska inte ändras i detta bygge. Ingen obehörig media-/musikåteranvändning.

## 10. Sprintplan – autonom, avslutningsbar och återstartbar

Varje sprint ska vara separat commit/checkpoint, med `reports/BUILD_STATE.json` som uppdateras efter test: `sprint`, `status`, `base_sha`, `head_sha`, `inputs`, `outputs`, `checks`, `known_limits`, `next_action`. Kör aldrig otestad storskalig ombyggnad av alla vyer i ett commit. Status `DONE` kräver angivna tester, inte bara kod närvarande.

| Sprint | Syfte och obligatorisk leverans | Acceptanskriterium / återgångspunkt |
|---|---|---|
| **S0 – Källfrysning och merge-strategi** | Kontrollera nya refs; säkra EQ-artifact 36818159977 före expiration; inventera lokala GPX-bytes mot PR #1; förena `setup/foundation`-filerna med nuvarande `main` selektivt (inte blind merge om konflikt); lås referens-SHA. | `reports/S0_SOURCE_LOCK.md`, käll-/hashmanifest, korrekt 2016–2025 EQ-register, GPX-status `available/missing` utan falska löften; clean Git checkout och uppdaterad BUILD_STATE. |
| **S1 – EQ-data och datakvalitet** | Läs råarkivet; normalisera events/races/classes/results/contestants/checkpoints/splits/status med EQ-adapter; bevara raw JSON; deduplicera deltagare mellan stationer och pagineringssidor. | SQLite kan byggas reproducerbart; per-år/per-distans reconciliation av antal unika result, stationobservationer, finishers, DNF/DNS; kontrollerad ordning och datakontroller utan orphan/dublett; `reports/S1_EQ_COVERAGE.{json,md}`. |
| **S2 – Kurskatalog/geometri** | Registrera varje edition och CourseVersion med evidens. Skapa sanerade 43 km-versioner från PR #1, importera faktiskt åtkomliga 85 km-assets och 22 km när tillåtet; jämför geometri och projektera endast explicita timingankare. | `course-versions.json`, `source-registry.json`, `route-evidence.json`; geometrivalidering/checksum/monotoni/versionsgräns; saknad 22-rutt loggas utan stopp. |
| **S3 – Engine 1.0 och webbleverans** | Exportera kuraterad SQLite → kanonisk Engine 1.0 → bootstrap + edition-bundles + historikaggregat. Compute readiness per edition. | Contract/roundtrip/paritytester, inga resultat-/splitförluster, familj+år byter rätt dataset, statisk `docs/index.html` kan visa samtliga tillgängliga race editions. |
| **S4 – Design och resultatverktyg** | Sätila-hero, distanskort, årsväljare, sticky nav, globala filter, sök, fullständig T01/resultatdatabas, startsidans tom-/loading-/errorstates och delbara länkar. | 85/43/22 kan väljas; namn/startnummer/autocomplete, reset, sort/pagination, Back/Forward, mobil och tangentbord fungerar; inga fake resultatrader. |
| **S5 – Översikt/statistik** | D01–D08, D12–D13, n-kontroller och kön/klass/klubbinteraktioner. | Diagram/testvärden från riktiga race bundles, filter isolerar rätt data, inga null→0, start/finish/status denominator rätt; diagramvisuell QA 4 viewport. |
| **S6 – Dynamik och delsträckor** | D06, D09–D11, D14–D21 och T04 utifrån faktisk split coverage. | Officiella passager och analytiska gränser verifieras; fasordning rätt; n≥5/10/20; result-only editions renderar snyggt utan tomt segment-/DNF-kort; DNF sista observation korrekt. |
| **S7 – Individ, favoriter och Direktjämförelse** | UV U5 + ÖST profilmodal, T02/T03/T05, kompakt Journey, relatif pacing, favoriter, H2H två resultat. | FINISHED/DNF/DNS/partial splits/utan kön/utan route får semantiskt korrekta profiler. Direktjämförelse öppnas från profilen och sök. Namndubblett skapar aldrig falsk personhistorik. |
| **S8 – Kartor, Course Intelligence och Replay** | K01/K03/K04/K05/K06 med Gotaleden/UV-kärnor; D22/D23 och T07; karta/höjd lazy och fallback. | Minst ett tillgängligt lokalt ruttscenario testas om GPX-bytes finns; replay stoppar vid sista exakta ankare; tiles-offline fallback; segment-klick synkar alla vyer; utan route visas inte en annan editions bana. |
| **S9 – Måltempo och flerårshistorik** | T06/T08, D24–D27, måltempo och årstabell/fingeravtryck/versionsband. Valfri K02 historisk kartoverlay när två publicerbara rutter finns. | Målplan summerar T när fullständig och märker distansfallback; tidslinjer bryts vid jämförbarhetsgräns, 2016–2019 ursprunglig distans kvar, 2020 ej nollår, ingen ogrundad person-Hall-of-Fame. |
| **S10 – Metod, polering och end-to-end-regression** | T09/T10, alla lokala (i), full Metod, responsive/a11y/empty/loading/errors, caching/versioner och prestanda. | Python, JS, full Chromium/Playwright per distans och minst ett result-only-scenario grönt. 0 oväntade console/page/networkfel, reduced-motion, fokus, fallback, deep links, 4 viewport. |
| **S11 – Granskningsbar releasekandidat** | `reports/S11_REVIEW_PACK.md`: build-SHA, källtäckning, route-/editionmatris, testresultat, kända begränsningar, skärmbilder för desktop/mobil och länkar till testbar GitHub Pages-preview; README med start/återskapande. | Publicerad **förhandsgranskning** om Pages är tillgängligt och godkänt; annars lokal statisk build + artifact och PR-länk. Produkt `READY FOR HUMAN REVIEW` först när alla tre distanser och varje relevant edition har kontrollerats. Ingen automatiskt utlovad publicering på loppanalys.se. |

### Sprintarnas beroendegraf
`S0 → S1 → S3 → S4 → S5 → S6 → S7 → S8 → S9 → S10 → S11`; `S0 → S2 → S3`. Där geometri saknas får S3–S7 ändå fortsätta med resultatbaserade editions; S8 levererar route feature endast för source-capable editions.

### Reparerbarhet när en körning bryts
1. Läs `reports/BUILD_STATE.json`, README och senaste commit/PR; kontrollera att `head_sha` finns och att working tree matchar eller dokumentera avvikelse.
2. Kör föregående sprints smoke- och datagrind först, inte en ny rådatacrawl.
3. Återuppta första sprint med `status !== DONE`; ta bara om ett tidigare moment om dess test fallerar.
4. Committa per mindre vertikal slice inom sprint (t.ex. en komponent + tests), inte ett oöverskådligt 10-fils-paket.
5. Vid icke-kritiska blockeringar: lägg till `known_limits`, disable via readiness/capability och gå vidare. Vid korrupt timing eller motsägande källdata: karantänsätt observationerna och rapportera utanför publishable data, fortsätt övriga upplagor.
6. Håll `main` stabil och bygg på separat `build/saetila-first-draft` efter källreconciliation. PR innehåller sprintchecklistor/testutfall. Merge först efter S11:s QA-grind.

### Testkatalog (skapa i samma sprint som komponenten)
- Data: års-/familjstotaler, EQ pagination, station/deltagare dedup, split sort, status, race bindings, source fingerprint, checksum.
- Geometri: GPS felväg rå vs sanerad, 43 km kursbyte 2022→2023, nominell distans ≠ polylinelängd, monotona ankare, 85 km årlig geometri separerad, saknad 22 GPX.
- Analys: n-thresholds, null, gender coverage, edition-isolation, DNF last passage, auxiliary vs boundary, cohort consistency, fartsformel.
- Historik: olika whole-course-grupper ger bruten sluttidsserie, deltagande bevaras, 2020 inte syntetiskt noll, identity match utan evidens avvisas.
- Browser: 85/43/22, 2021/2025 där data finns och historiskt 2016 om importen visar edition; deep link och back/forward; alla UI-kontroller; profiler FINISHED/DNF/DNS/partial; jämförelse med/utan split; karttile failure; reduced motion; tablet/mobil overflow; screenshotbaserad granskning.
- Release: länkar, assets, inga onödiga publika original-GPX/personmetadata, korta laddningar, inga oväntade nätverksfel.

## 11. Granskarens acceptansprotokoll för första utkastet

Den som granskar ska utan utvecklarverktyg kunna:
1. Öppna Sätila Splits och välja 85, 43 och 22 km; se senaste genomförda år och växla till historiska år där resultat finns.
2. Hitta en faktisk löpare via namn/startnummer; öppna profil med korrekta passager eller tydlig saknad-data-text.
3. Förstå startfält, måltider, status, klasser och ålders-/könstäckning i varje edition.
4. Se segment- och fältanalys bara när officiella timingobservationer räcker till.
5. Se 43 km:s två preliminära banfamiljer samt 85 km:s evidens per år när de sanerade route-assets finns – aldrig ett falskt lånat 22 km-spår.
6. Öppna en faktisk Replay/Kartduell där både godkänd route och timingankare är tillgängliga; annars förstå exakt varför funktionen saknas.
7. Skilja verkliga tider från interpolerad kartposition; jämföra två löpare och läsa historiken utan falsk banjämförelse.
8. Använda alla kontroller på mobil/tangentbord och öppna metodinformation för varje mått.
9. Läsa `S11_REVIEW_PACK.md` och se full importtäckning, testpass, begränsningar samt vilka delar som är uppskjutna av evidensskäl.

### Avsiktligt senare än första utkastet
Arrangörens kompletterande officiella GPX, eventuella extra 22 km-rutter, verifierad full personidentitet över år, sammanvägd difficulty-poäng (inte planerad utan ny metodprövning), musikproduktion, separat standalone legacy-kartsida och produktionsintegration på loppanalys.se. Ingen av dessa får blockera ett granskningsbart datakorrekt Sätila-utkast.

---
**Byggdirektiv för nästa uppdrag:** Läs hela denna rapport, kontrollera respektive repo-/branch-SHA och nuvarande Sätila-main, börja omedelbart på S0 och fortsätt genom S11 utan mellanliggande designavstämningar. Redovisa endast faktiska utförda commits, tester, previews och kvarvarande begränsningar.