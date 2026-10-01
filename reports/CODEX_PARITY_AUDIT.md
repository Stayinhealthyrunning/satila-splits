# Sätila Splits – komponentgranskning 2026-10-01

> **HISTORISK FÖRSTA DRAFT-SNAPSHOT, EJ AKTUELL GAPLISTA.** För verifierad frontend 217439a4 och uppdaterad D07/K03/T01/T04/T06/T07/K04/K05, läs [VERIFIED_PRE_CODEX_CHECKPOINT_2026-10-01.md](VERIFIED_PRE_CODEX_CHECKPOINT_2026-10-01.md) innan ny Codex-körning.

Bas: `origin/build/full-first-draft-2026-10-01@c739b10`. Arbetsgren: `codex/saetila-complete-first-draft`. Jämförelsen gäller blueprintens faktiska funktioner, inte enbart närvaro av rubriker. `Gated` betyder att källdata för den begärda presentationen inte finns som godkänd lokal tillgång.

## Diagram D01–D27

| ID | Grad | Kod/DOM | Kvarvarande acceptansgap |
| --- | --- | --- | --- |
| D01 | Delvis | `renderKpis`, `#kpis` | Visa separata DNF/DNS/DSQ/UNKNOWN och explicit startnämnare i KPI-raden. |
| D02 | Delvis | `renderFinishChart`, `#finish-chart` | Gör All/F/M-val tydligt; okänt kön och filtrerat n behöver tydligare serieetiketter. |
| D03 | Implementerad | `renderOverview`, `renderCumulativeFinish`, `#percentile-chart` | P10–P90 och kumulativ målgång på gemensam tidsaxel, med separata könsnämnare där n≥5. |
| D04 | Implementerad | `renderSexCompletion`, `#sex-completion` | Kontrollera könstäckning för varje upplaga vid visuell QA. |
| D05 | Implementerad | `renderOverview`, `renderClassDetails`, `#group-bars` | Toppklasser och utfällbar fullständig klasslista med filterval. |
| D06 | Implementerad | `renderDynamics`, `#status-chart`, `#flow-chart` | Fältflödet anger registrerade passager, inte bortfall. |
| D07 | Delvis | `renderDynamics`, `#placement-chart` | Zoom/reset och klass i punktens tooltip saknas. |
| D08 | Implementerad | `renderGoal`, `#goal-placement` | Deskriptiv måltid mot vald editions observerade målgångar. |
| D09 | Implementerad | `renderDynamics`, `#dnf-chart` | Okänd sista passage redovisas separat. |
| D10 | Implementerad | `renderPlacementGain`, `#placement-gain` | Källstött positionspar används. |
| D11 | Delvis | `renderFinishProgress`, `#finish-progression` | Sista verifierade segmentets styrka och kohortn behöver visas tydligare. |
| D12 | Implementerad | `renderAge`, `#age-chart` | Exakt ålder och klass hålls isär. |
| D13 | Implementerad | `renderClub`, `#club-chart` | Upp till fyra källgrupper kan väljas; full tabell med deltagande och mediansluttid kan öppnas. |
| D14 | Implementerad | `renderSegmentGraph`, `#segment-chart` | Median n≥5 och kvartil n≥10. |
| D15 | Implementerad | `renderQ1090`, `#segment-q1090` | Q10–Q90 kräver n≥20. |
| D16 | Implementerad | `renderPacingIndex`, `#segment-pacing` | Eget pacingindex hålls skilt från den äldre grafen för observerad passageretention. |
| D17 | Implementerad | `renderSexSeries`, `#segment-sex-extra` | Gemensam tidsaxel, separata toggles och avbrott vid otillräckligt n. |
| D18 | Implementerad | `renderClassSeries`, `#segment-groups` | Val av upp till fem källklasser, medianpacingindex per segment och n≥5. |
| D19 | Implementerad | `renderHeatmap`, `#segment-heatmap` | Gruppens relativa segmenttid samt n i varje cell. |
| D20 | Implementerad | `renderCumulativeFinish`, `#percentile-chart` | Observerad kumulativ målgång med explicit fullföljarnämnare. |
| D21 | Delvis | `renderCheckpointSpread`, `#checkpoint-spread` | Tydliggör varierande kohort mellan kontroller i kortet. |
| D22 | Delvis | `renderCourseIntel`, `#course-intelligence` | Pacing loss, segmentvis spridning/placeringsrörelse och DNF-exit saknas. Rå GPX D+ är inte officiell. |
| D23 | Delvis | `renderCourseMap`, `#course-elevation` | Verifierade checkpoint-ankare och explicit höjdavbrott saknas. |
| D24 | Implementerad | `renderHistory`, `#history-chart`, `#history-table` | Resultat, kända startande, fullföljare och DNF/status per källår; 2020 är en lucka. |
| D25 | Gated | `renderHistoryPerformance`, `#history-performance` | Separata årsmedianer visas; ingen godkänd flerårig whole-course-grupp är dokumenterad för en prestationslinje. |
| D26 | Delvis | `renderFingerprint`, `#history-fingerprint` | Årsöversikt finns; jämförbart rekord/prestationsindex saknar källstöd. |
| D27 | Implementerad | `renderSexHistory`, `#history-sex` | Separat kvinna/man/okänt och 80 % källtäckningsgrind per upplaga. |

## Tabeller T01–T10

| ID | Grad | Kod/DOM | Kvarvarande acceptansgap |
| --- | --- | --- | --- |
| T01 | Delvis | `renderResults`, `#results-table` | År/distans ligger i sidkontext, inte i raden; fulla sortmöjligheter och tangentbords-QA återstår. |
| T02 | Implementerad | `renderProfile`, `#profile-dialog` | Ackumulerad tid, tid sedan föregående verifierade passage, publicerad plats och källstatus. |
| T03 | Implementerad | `renderProfile`, profilens segmenttabell | Segmenttid, timingdistans, tempo, fältmedian, avvikelse och n från denna upplagas fullföljare. |
| T04 | Delvis | `renderSegmentTable`, `#segment-table` | Retention, placeringsrörelse, DNF och proveniens per rad saknas. |
| T05 | Implementerad | `renderCompareContent`, `#compare-dialog` | Ackumulerade tider, segmenttider, publicerad plats, lucka och insikter från gemensamma exakta passager. |
| T06 | Delvis | `renderPlan`, `#plan-table` | Kohort/segmentval finns; D+/D− och särskild evidenskolumn återstår. |
| T07 | Delvis | `renderProvenance`, `#course-provenance` | Källfil, SHA-256, CourseVersion och route-status visas. Särskild publiceringsgrad/konfliktkolumn återstår. |
| T08 | Implementerad | `renderHistory`, `#history-table` | Datum, källdistans, status, median per upplaga, whole-course-grupp, route-status och originallänk. |
| T09 | Delvis | `renderGroupTable`, `#group-table` | Ålder/klubb och paginering saknas. |
| T10 | Implementerad | `renderCoverage`, `#coverage-table`, `docs/data/coverage.json` | Status-, köns-, ålders-, klass- och klubbtäckning med aktuell ruttstatus och reproducerbar JSON-export. |

## Kartlägen K01–K06 och P0

| ID | Grad | Kod/DOM | Kvarvarande acceptansgap |
| --- | --- | --- | --- |
| K01 / P0.1 | Delvis | `renderCourseMap`, `#course-map`, `#course-elevation` | Karta och höjd är synkade med klick/tangentbord. Leaflet-tiles, checkpointmarkörer, hover och full banutsnittshantering återstår. |
| K02 | Gated | `renderMapHistory`, `#map-history` | Endast godkända 2025/26-arrangörsrutter finns lokalt för huvudfamiljerna. Inga två distinkta historiska rutter för samma familj får överlagras. |
| K03 | Delvis | `syncSegmentOverlay`, `#course-map`, `#segment-table` | Segmentvalet styr rutt/tabell men inte samtliga pacing-/spridningskort. |
| K04 | Delvis | `renderProfileReplay`, `#profile-replay` | Interaktiv scrubber finns. Tidsstyrd uppspelning 30/60/120/180 s och följ/visa hela banan saknas. |
| K05 | Saknas | `#compare-dialog` stöder två löpare | Kartduell för 2–5 med tävlingsklocka/leaderboard/kamera saknas. |
| K06 | Implementerad | SVG-rutt i `renderCourseMap` | Lokal interaktiv SVG fungerar utan tiles; källlös edition visar saklig tomstatus. |
| P0.2 | Delvis | `podiumPair`, `#overall-podium`, `#segment-podium`, `#standouts` | Sidvidsida och medaljer finns; n/täckning per kön/segment behöver bli synliga. |
| P0.3 | Delvis | `renderProfile`, `profileInsights`, `renderProfileReplay` | Personinsikter visar nu metod/n där relevant. Tidsstyrd Replay återstår. |
| P0.4 | Delvis | `renderPlan`, `#plan-table` | Hel/kön/klass/nära måltid, n-grind och öppet fallback finns i arbetsgrenen. D+/D− och tydlig planprofil återstår. |
| P0.5 | Delvis | `renderCompareContent`, `drawCompareMap` | Klick/hover, tangentbord, zoom/fit, två markörer och komplett passagetabell fungerar. Gemensam tävlingsklocka för kartduell 2–5 hör till K05. |

## Källgränser och kontroll

- 27 importerade upplagor och 3 272 resultat kontrollerades i `tests/browser_smoke.py`. År 2020 konstrueras inte.
- Route asset finns endast för källstödd 2025 trail22/trail43 i importerade editions. 85 km 2026 är en separat framtida rutt utan resultat. Historisk geometri får inte lånas.
- Det finns redan ersättning med initialavatarer; inga sociala profilbilder behövs.
- `BUILD_STATE.json` i roten är den senaste statusfilen. `reports/BUILD_STATE.json` är en äldre checkpoint och ska inte användas som nästa arbetsinstruktion.
- Komponenternas `Delvis`/`Saknas` är aktiva implementeringspunkter. `Gated` får öppnas först när källkontrakt och lokal godkänd data räcker.
