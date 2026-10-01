# Oberoende release-handoff: Sätila Splits

Datum 2026-10-01. Denna leverans gör **ingen** ändring i Codex aktiva frontend, databyggaren, Hero eller publicerade JSON-bundlar. Den bör integreras efter lämplig synkning med Codex `codex/saetila-complete-first-draft`.

## Slutligt QA-läge på aktuell frusen förstautkast-databas

[Alla fristående kontroller godkända – GitHub Actions 36844103210](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36844103210).

| Fristående kontroll | Kommando | Resultat |
|---|---|---|
| Katalog, nycklar, status, publika målpassager, inga fabricerade tider | `python tests/test_published_data_integrity.py` | PASS |
| Exakta segmentpar och minsta n per edition och grupp | `python tools/audit_segment_capabilities.py` | PASS |
| Metadata-only stationer, verkliga sammanslagna delsträckor | `python tools/audit_station_coverage.py` | PASS |
| Fem officiella GPX: SHA, koordinater, kumulativ längd | `python tests/test_route_geometry_integrity.py` | PASS |
| Könspodium, placeringsresa, personlig profil, rutt-readiness | `python tools/audit_ui_capabilities.py` | PASS |
| Endast kuraterat offentligt innehåll i Pages, inga råspår/profilbildslänkar | `python tests/test_publication_privacy.py` | PASS |

Maskinläsbara `satila-source-integrity.json`, `satila-segment-capabilities.json` och `satila-ui-capabilities.json` finns under Actions-runens artifact **satila-source-integrity**.

**Fast baseline:** 27 RaceEdition, 3 272 publicerade resultatrader, 2 649 FINISHED, 128 DNF, 494 DNS, 1 UNKNOWN; 16 525 publicerade verkliga TIME-observationer; 5 officiella arrangörsrutter. Alla källreferenser till registrerade passager är konsistenta.

## Två obligatoriska slutgranskningsfall

**S1 / 43 km 2025:** Tostared, 10,2 km, UID 1416266 är en publicerad station med **0 TIME**. Den kan inte definiera en historiskt mätt segmentgräns. Grind→Torrås, 1,2→16,2 km, har däremot **130 positiva verkliga tidspar**. Presentera det som ett enda historiskt 15,0-km-segment, behåll Tostared i rå metadata, och märk eventuell interpolerad Tostared-loppplan som planering – inte officiell passage.

**S2 / 43 km 2023:** Almered→Skolan och Skolan→Ramhulta har vardera **n=8 (F=4, M=4)**. Visa totalmedian men inte kvartiler, deciler eller könsspecifika medianer. Top3 av *registrerade* kvinnliga/manliga tider kan visas med n=4 och tydlig datatäckningsförklaring. **85 km 2016** har endast två kvinnliga FINISHED och kan inte ha en tredje/bronsplacerad kvinna i topplistan.

## Kompletterande metodregression (utförd medan Codex bygger frontend)

[Samlat godkänd CI-körning inklusive de nya fallen: 36844654698](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36844654698).

- `tools/audit_statistics_reference.py` är en **separat metodreferens**, inte ny produktionmotor. Den innehåller exakta tidspar, n-gränsade kvantiler, verkliga podiumplaceringar, observerad placeringsutveckling och exakt normaliserad måltidsfördelning med tydligt märkta fallback-segment.
- `tests/test_statistics_contract.py`: 9 fristående syntetiska regressionstester, inklusive Tostared utan passage, saknad observation, n=4/5/9/10/19/20, två kvinnliga podiumplaceringar, nollstart endast vid race-start och pacingplan som summerar exakt till angiven sluttid.
- `tests/test_course_comparability_contract.py`: 8 regressionsfall för explicit banversion, 2025/26 återanvändning, separat 85 km 2026, opromoted deltagarkandidater och skillnaden mellan officiell timing- och GPX-displaydistans.
- Dessa tester körs tillsammans med de sex befintliga käll- och publiceringskontrollerna i `.github/workflows/source-integrity.yml` på PR #4. De ändrar inte publicerade race-data eller Codex-filer.

**Viktig metodregel vid Codex-integration:** Kontrollera att pacing inte byggs som en mekanisk fördelning över stationsmetadata när en publikt angiven station helt saknar tidtagning. Eliminera bara den oobserverade analysgränsen (inte källstationen), bygg verkliga positiva grannankare och markera eventuell interpolerad Tostared-planering som icke observerad. För utvecklaren är statistisk referensimplementation i `tools/audit_statistics_reference.py` tillgänglig att jämföra mot faktisk JS.

## Verkligt-data-regression och Codex-browseracceptans

Tillägg efter `974ede95`:

- `tests/test_real_data_analysis_contract.py`: sju **datadrivna** regressioner över hela uppsättningen av 27 officiella editioner. Till skillnad från de syntetiska fallen provar dessa varje faktisk katalog, observerat segmentpar, per-segment-n/grupp, 81 målplansvarianter (tre måltider per edition), 2025/43 Grind→Torrås med n=130, 2023/43:s två n=8-segment, 2016/85:s två kvinnor och placeringsutveckling ur verkligt registrerade platser.
- Testet hittade och vi rättade ett för strikt antagande i **testet**: vissa gamla upplagor kan ha en officiell registrerad tidtagningsstation som heter Start och också har en källregistrerad placering. Den får användas *endast om den finns på riktig källa*, inte konstrueras för saknade startpassager. Kontrollgränsen är nu källobservation, inte en spärr på textetiketten.
- [Grön verkligt-data-regression för alla 27 upplagor](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36845227231).
- `.github/workflows/source-integrity.yml` har förenklats så att audit körs **en gång** som PR-check i stället för både push och PR vid samma kodändring. Manuell `workflow_dispatch` kvarstår för integrationsprov.
- `tests/browser_evidence_acceptance.py`: separat **Codex-acceptanstest**, ej inkluderat i den gröna käll-CI:n innan fixen finns. Kräver installerad Playwright/Chromium och körs med:
  ```bash
  python tests/browser_evidence_acceptance.py
  ```
  Det laddar endast committade, riktiga race-bundlar, testar desktop **1440×900** och mobil **390×844** och verifierar observerade Grind→Torrås i 2025/43, 7 av 7 historiska plansegment i samma edition, korrekt låg n i 2023/43 och två (inte tre) kvinnor på 2016/85:s podium. **Det första utkastet förväntas misslyckas på Tostared-punkten**; använd det som en faktisk acceptansgrind för Codex rättning, inte som ett tillfälligt krav att tysta eller förbigå.

## Integration i rekommenderad ordning

1. Låt Codex färdigställa sin egen kod-/designgren och köra dess browser QA. Mergea aldrig en pågående arbetsgren.
2. Synka Codex PR mot dåvarande `build/full-first-draft-2026-10-01`.
3. Öppna/uppdatera denna separata audit-PR #4 mot aktuella bygggrenen och kör dess sex kontroller.
4. Kontrollera att Codex behandling av Tostared inte tilldelar någon fiktiv tid. Vårt stationstest är förberett för båda tillåtna sätten att markera stationen: som källa med metadata-only-status eller som source analysis-boundary som filtreras bort vid beräkning.
5. Kör slutligen fristående Chromium-regression, visuell desktop/mobil-granskning och gransknings-ZIP på samma integrerade commit.
6. Publicera först när projektägaren uttryckligen godkänt; varken denna PR eller Codex PR ska auto-mergas till `main`.

## Viktiga källavgränsningar

- Den officiella timingaxeln och GPX-displaydistansen är olika mått: 43 km 2025 ger 43,0 km respektive cirka 42,254 km; 21/22-familjens moderna arrangörs-GPX ger cirka 23,043 km. Ändra inte segmentdistans till GPS-distans utan explicit metodbyte.
- 2025/2026 officiell återanvändning är godkänd för 5/10/21/43 km. Den separata 85-km-rutten från 2026 får inte obemärkt kopplas till 2025 eller äldre upplagor.
- Rå deltagar-GPX, arkivdatabas och sociala profilbilder ska inte ingå i det publika GitHub Pages-paketet.
- Löparhistorik över olika år kräver en separat verifierad identitetsmodell och course comparability; gissa inte individers identitet från liknande namn.
