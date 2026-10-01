# Sätila Splits – pre-Codex integrationsöverlämning (2026-10-01)

Denna fil är **aktuellt tillägg** till historiska `CODEX_PARITY_AUDIT.md` (vars K04/K05- och T09-rader beskriver en äldre Codex-checkpoint). Använd **inte** `main`, `build/full-first-draft-2026-10-01` eller gamla Codex-grenen som bas för nästa pass.

## Baslinje och källkontrakt

- Senast helt grön efter D11/D18/D19/D22/T07: `e3420bb5da7763e251e3e61c62f5b2765f411e4d`, [fyra gröna jobb #36868424098](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36868424098). Små efterföljande D07/D21-/metadata-only-korrigeringar kräver nytt **samma-SHA**-CI före slutlig checkpoint.
- Nya funktionsförbättringar ligger efter denna commit i `integration/codex-independent-qa-2026-10-01`; kontrollera **senaste workflow-körning mot samma HEAD** innan en ny grön baslinje anges.
- [Draft PR #7](https://github.com/Stayinhealthyrunning/satila-splits/pull/7) mot bevarad Codex-originalgren `a71a5ef`; `main` och Loppanalys.se är inte publicerade.
- 27 editioner, 3 272 resultat, 2 649 FINISHED, 128 DNF, 494 DNS, 1 UNKNOWN, 16 525 verkliga TIME-passager, fem checksummeverifierade arrangörs-GPX. Inga historiska råa deltagarspår ligger i publik `docs/`.
- Publicerad 2025/43 har Tostared som metadata-only (0 TIME): korrekt sammanslagen Grind→Torrås n=130, sju effektiva segment. 2023/43 har två n=8-segment utan kvartiler; 2016/85 har två kvinnliga FINISHED. Pace för Torrås→Almered 2023/24 är time-only tills timingdistansen verifieras. Ingen historisk route-borrowing eller syntetisk DNF-kontroll.

## Nya implementationer inför återstart (utöver gamla rapporter)

| ID | Ändring i aktuell `docs/assets/app.js` | Evidensgräns |
|---|---|---|
| DNF / T04 | Kolumnen `DNF sist här` visar `Okänt` när urvalets DNF helt saknar källkopplad offentlig TIME; inte en falsk numerisk nolla. | Samtliga 128 nuvarande DNF saknar sådan publicerad observation; DNF:s faktiska avbrottsplats är okänd. |
| D06/passagetäckning | Metadata-only Tostared ligger kvar i stations-/fältflödet, men markeras `endast metadata (0 TIME)` och exkluderas från själva passagetäckningskurvan, så ingen falsk noll-dipp/återhämtning ritas. | Endast editionsbrett verifierade TIME-stationer får ingå i kurvan; grafen visar observerad täckning, aldrig DNF/överlevnad. |
| D07/D21 | Scatter-punkters tooltip visar källklass; kontrollspridningen märker att varje kontroll har eget verkligt observerat n och kan omfatta olika fullföljare. | Klass härleds inte från ålder och saknade TIME imputeras inte. |
| D22 / K03 | Course Intelligence följer `selectedSegment` och visar n, TIME-median, Q25–Q75 när n≥10, pace när distans stöds, placeringsrörelse samt DNF-täckning. | Ingen påhittad segment-D+, exit-position eller officiell GPX-checkpointprojektion. |
| D11 | Separat ranking av sista **verifierade positiva** TIME-segmentet mot just det segmentets fältmedian, n≥5; sista tredjedelens placeringsprogression behålls som separat mått. | Kvoten är tidsbaserad, fungerar även för time-only-distans. Sista verifierade segment behöver inte nå målet. |
| D18/D19 | Heatmap visar samma valda klasser som klasspacingdiagrammet (max fem) och uppdateras vid kryssrutebyte; klassurval återställs vid editionsbyte. | Tom cell = n<5/saknad observation, inte nolltempo. |
| T07 | Provenienstabellen får separata kolumner för publik sanerad displayrutt och faktisk verifieringsreservation ur `coverage.json`. | 2025/26-återanvändning är uttryckligt projektantagande, inte godkänd flerårig whole-course-prestationsgrupp. |

De nya browserkraven är inlagda i `tests/browser_evidence_acceptance.py`: metadata-only Tostared som falskt retentionstapp, DNF-unknown, D07/D21, D22-selectedSegment, D11, D18↔D19 och T07. Den ursprungliga Tostared/n=8/2016-podium-testningen finns kvar. Senast rättat i testet: använd `text_content()` för lång horisontellt scrollad T07-tabell, eftersom `inner_text()` kan begränsas av viewport-klippning. Source-jobbet har även automatisk `node --check`.

## Vad som redan fungerar och inte ska byggas om

- Fulla 27 editionsresultat, källdatainventering och `coverage.json`, statusnämnare, klass/ålders/klubbdiagram, D16 verkligt pacingindex, kvinnors/mäns segmentserier, podium, fördjupad profil och individuell plan.
- K04 personlig tidsstyrd Replay och K05 2–5-löpares kartduell med gemensam klocka/leaderboard finns i integrationen. Både översikt och H2H använder klick i **karta och höjdprofil** mot gemensam displaydistans. Ändra inte dessa från grunden.
- Hero-kopia, Back/Forward, mobilmeny/Escape/fokus, synligt laddfel, felaktig historisk fysisk pace, rådataprivatliv och source-replay-gates är redan åtgärdade och CI-skyddade.

## Återstående, prioriterade begränsningar

1. **Visuell slutgranskning:** riktig topp-/full-page-webbläsargranskning vid 1440/900/768/390, särskilt alla långa segment- och provenienstabeller på mobil, Hero och nytt D11/D22-block. Justera endast identifierade fel; jämför mot `docs/assets/design-reference.webp`.
2. **D07:** scatter-/resultat-zoom/reset och tydlig källklass i punktens tooltip. Fullständigt tangentbordsprov av tabell T01.
3. **D21/K03:** variera-n-upplysning på checkpoint-spridningen; bekräfta att alla synkbara segmentvyer byter `selectedSegment` (inte bara tabell, Course Intelligence, pacingdiagram och karta).
4. **K01/D23:** förbättra kartans utsnitt, tillgängliga checkpointankare och gap i höjdprofil *endast* där godkänd fysisk position/elevation faktiskt finns. Godkänd lokal SVG-fallback fungerar; eventuell Leaflet/OSM får inte bli ett driftberoende för analysen.
5. **T06 / P0.4:** segment-D+/D− ska förbli `ej verifierat` tills godkända ban-/kontrollankare medger faktisk segmenthöjd. Planens historiska tidsandelar och n-grind är redan källkorrekta.
6. **Gated by evidence – ingen frontendfuskfix:** K02 historisk tvåbanoverlay, D25 sammanhängande helbanetidstrend, D26 jämförbar rekordprestation och DNF-avbrottsgeografi. Ingen modern 85-km-GPX får lånas till 2025.

Separat ägaråtgärd: privat långtidsbackup av fryst EQ Timing-raw-artifact (issue #6, utgår 2026-10-31). Den offentliga `docs/`-katalogen får aldrig innehålla det råarkivet.

## Säker Codex-återstart efter kvot 16:13

Behåll `C:\Git\satila-splits` och `reports/qa-local/` helt intakta. Kontrollera befintliga grenar/worktrees innan nytt kommando:

```powershell
cd C:\Git\satila-splits
git status --short
git fetch origin --prune
git worktree list
git branch --list codex/saetila-post-integration
git log -1 --oneline origin/integration/codex-independent-qa-2026-10-01
# Bara om ny branch/worktree inte redan finns:
git worktree add -b codex/saetila-post-integration C:\Git\satila-integration origin/integration/codex-independent-qa-2026-10-01
cd C:\Git\satila-integration
git status --short
```

Kör `python tools/run_release_candidate_checks.py --all`, eller den samlade integrationsworkflowen på **den nya kandidatsamtliga slutliga commits**. Review-ZIP från samma godkända SHA och projektägarens visuella sign-off krävs före merge/publicering. Gör aldrig `reset --hard`, `clean -fd` eller `force-push` mot ägarens bevarade original.
