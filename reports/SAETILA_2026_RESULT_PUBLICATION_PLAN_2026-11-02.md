# Sätila Trail 2026 – resultatpublicering efter 7 november

**Status 2026-11-02: INTE AUTOMATISKT KLAR.** Detta är ett kontrollerat förberedelsedokument, inte ett godkännande att publicera rådata. Den historiska `events`-listan är medvetet fryst. Årets event registreras separat under `pending_events` i `config/eqtiming-events.json`.

## Bekräftad källa och tid

- Tävling: Sätila Trail 2026, lördag **2026-11-07**.
- Officiell tidsleverantör: **EQ Timing**.
- Offentlig källa: **https://live.eqtiming.com/82600** (webbgranskad 2026-11-02).
- Anmälda distanser enligt arrangören: 5 km, 10 km, 22 km, 43 km och 85 km. Webbappens historiska analys omfattar **22 km, 43 km och 85 km**, inte 5/10 km.
- Målet stänger natten mellan lördag 7 och söndag 8 november kl. 00.00. Första rimliga fullständiga avstämning: söndag 8 november under förmiddagen, förutsatt att EQ Timing verkligen har publicerat slutresultaten.

## Aktuella blockerare

1. **Ingen 2026-analysdata:** `docs/data/bootstrap.json` och `docs/data/races/` innehåller endast 2016–2025.
2. **Avstängd råimport:** `.github/workflows/import-eqtiming.yml` har en uttrycklig privacy hold `if: ${{ false }}`; slå inte på den gamla workflowen. Den laddade historiskt upp råa deltagaruppgifter till en offentlig repo-ägd Actions-artifact.
3. **Ingen trygg, verifierad 2026-kedja:** separat, skyddad källa → parsing → opt-out/minor-/sekretessfilter → kvalitetssäkrat publiceringspaket → PR → Pages har inte provkörts för årets data.
4. **Privat råarkiv:** GitHub issue #6 (https://github.com/Stayinhealthyrunning/satila-splits/issues/6) är fortfarande öppen och utgör inget bevis för återställningsbar privat källa.
5. **Ingen automatisk schemaläggning:** det finns ingen Github Actions-schedule som importerar, godkänner och publicerar 2026-resultat den 8 november.

## Söndag 8 november – rekommenderad körordning

1. Öppna https://live.eqtiming.com/82600 och verifiera publicerade **slutresultat** och samtliga officiella TIME-kontroller för 22/43/85 km. Jämför status för FINISHED, DNF, DNS och eventuella DSQ. Återkom efter ändringar i EQ Timing.
2. Hämta källmaterial **till åtkomstkontrollerat privat lagringsutrymme**, aldrig till publikt repo, GitHub Actions-artifact eller publik PR. Kryptera backup och provåterställ.
3. Identifiera faktiskt EQ Timing race-leg-UID, klass/kön och offentliga stationers UID, ordning, distans och om de är verifierade. Exkludera 5/10 km från webbappens historiska familjer och behåll icke-officiella Grind spärrad. Ingen gissning om DNF:s sista kontroll.
4. Kör nyårsspecifik transformer med `tools/build_satila.py` som referens, i en **privat stagingmiljö** med `LOPPANALYS_PRIVACY_REGISTRY_B64` eller motsvarande åtkomstkontrollerat register. Testa att alla personer under 18 år och registrerade opt-out-matchningar är helt borttagna från publika resultatrader och passager. Nya namnkollisioner ska kräva manuell granskning, inte ett automatiskt godkännande.
5. Skapa **endast granskade sanerade** `2026-ultra85.json`, `2026-trail43.json`, `2026-trail22.json`; uppdatera `bootstrap.json`, `coverage.json` och de käll-/ruttfingeravtryck som faktiskt kan styrkas. Behåll oförändrade historiska editioner. 2026-85-km GPX är en separat arrangörsrutt; för 22/43-km får arrangörens återanvändningsantagande anges explicit där det fortfarande gäller.
6. Kontrollera resultatantal, unika IDs, statusnämnare, mellantidernas monotonicitet, källa/siffror/medianer, n-trösklar, barnfilter, opt-out och frontend inklusive individuell analys. Fel i någon kontroll **stoppar publicering**.
7. Publicera granskade metadata + sanerade resultat via skyddad PR/merge till `main`. GitHub Pages-workflowen kan då bygga om och publicera `docs/`. Kontrollera publicerad 2026-upplaga och att de äldre årsresultaten är oförändrade.
8. Kör avstämning igen på kvällen eller måndag 9 november för sena statusändringar och rättningar i EQ Timing, med samma GDPR-/QA-gate.

## Releasevillkor

Publicera **inte** om EQ Timings 2026-data saknas/ofullständig, om någon opt-out eller minderårig inte kan granskas säkert, om källspåren är osäkra eller om checks fallerar. Råa `contestants.json`, importerade API-sidor, skärmade personuppgifter och rå-GPX får inte läggas i publikt Git eller offentliga Actions-artifacts.

Detta dokument ändrar **inte** befintligt gränssnitt eller befintlig data. Årets eventregistrering i `pending_events` är endast källförberedelse. Det är inte ett schema och innebär inte automatisk import.
