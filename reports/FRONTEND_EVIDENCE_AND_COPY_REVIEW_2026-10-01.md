# Sätila Splits – evidensbaserad frontend- och textgranskning

**Datum:** 2026-10-01  
**Syfte:** Oberoende acceptans för Codex visuella färdigställning; detta dokument ändrar **inga** frontendfiler på Codex gren.

## Interaktiva kartor – faktisk teststatus

Den separata browserregressionen `tests/browser_synced_scrub_acceptance.py` använder enbart kuraterade verkliga 2025-uppgifter samt deras officiella GPX-displayreferenser. Testet använder **verkliga UI-klick** på banöversikt, höjdprofil, resultatprofiler och H2H-dialog, inte bara interna funktionsanrop.

Testade skärmstorlekar:

- 1440×900 (desktop)
- 900×900 (surfplatta)
- 390×844 (mobil)

Kontrollerad funktionalitet:

1. Val av 43 km 2025 visar en karta och en höjdkurva med samma initiala displaydistans.
2. Klick i höjdprofilen uppdaterar kartans markerade position och tillgänglighetsvärde.
3. Tangentbordsnavigering i kartan uppdaterar höjdkurvan samtidigt.
4. Två olika **verkliga** registrerade fullföljare väljs via sökdialog och personprofil.
5. H2H öppnar karta, profil och ett gemensamt intervallreglage.
6. Klick i H2H-höjdprofilen uppdaterar kartan, reglaget och tidsluckans läsrad.
7. Klick på **den ritade banlinjen i H2H-kartan** uppdaterar i motsatt riktning höjdprofilen och reglaget.
8. UI redovisar att vald distans är GPX-displaydistans, inte uppmätt positions-GPS för de två personerna.
9. Byte från 2025 till 2024 gör den ogrundade 2025-displayrutten otillgänglig.
10. Inga JavaScript-undantag, saknade datafiler eller horisontell overflow.

Verifieringslänkar: [grön första Chromium-körning](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36852479937), samt den kompletterade trestorlekskörningen i Actions-workflow `Sätila independent interaction acceptance`.

**Viktig begränsning:** Detta verifierar första utkastets konkreta UI samt en separat källbaserad Replay-orakel. När Codex levererar en ny frontend måste **samma** test köras mot den nya HTML-/JavaScript-strukturen, och justeras endast när komponentens kontrakt avsiktligt ändras. En grön gammal version är inte bevis för en ny, otestad design.

## Text som riskerar att missleda

### Hero – ändra inför release

Nuvarande text i `docs/index.html`:

> Tre distanser. År av resultat. Samma stigar – djupare insikter.

Problemet är sakligt: 43 km har två olika autentiska deltagarbaserade korridorer 2021–2022 respektive 2023–2025. Dessutom ändras exempelvis Torrås officiella kilometertal från 8,0 km 2024 till 16,2 km 2025. Detta är redan styrkt i `reports/HISTORICAL_TIMING_AXIS_FINDINGS.md`.

**Föreslagen ersättning som bevarar rytm och ton utan att hävda banidentitet:**

> Tre distanser. Nio resultatår. Djupare insikter.

Alternativt en mindre numerisk formulering:

> Tre distanser. Många tävlingsår. Djupare insikter.

Säg inte att alla resultat kommer från ”samma bana” eller att äldre 43-/85-km-rutter är officiellt geometri-verifierade. En återkommande tävlingsidentitet är inte samma sak som en oförändrad tävlingsgeometri.

### Metodetiketter på kartsidan

- **Officiell tidtagningsdistans** (43,0 km i 2025 års maratonedition) är en annan axel än arrangörens **GPX-displaypolyline** (42,254 km för 2025/26-referensen).
- Moderna 21-km-GPX:ens displaylängd är 23,043 km, medan den historiska analysfamiljen i databasen använder etiketten 22 km. De ska inte smälta samman till ett påstått ”korrigerat” officiellt distansvärde.
- `raw_positive_gain_m_not_official` är rå summering av positiva GPX-höjdsteg, **inte** ett sanktionerat officiellt höjdmeterresultat. Undvik en oqualificerad ”D+”-etikett utan fotnot.
- Indikerad Replay-tid mitt emellan två faktiska kontroller är illustrativ interpolation. Visa aldrig en ny osanktionerad officiell passage.
- Historisk måltid→placering bygger på det valda observerade urvalet och ska inte kallas en garanti eller en prognos om framtida placering.

## Kompakt checklista för Codex-revisionen

- [ ] Godkänd Hero-bild kvar, text om ”Samma stigar” sakligt korrigerad.
- [ ] Tre skärmstorlekar och tvåvägsinteraktion karta ↔ höjd på både bana och H2H.
- [ ] H2H använder två separata publicerade resultat **i samma RaceEdition**.
- [ ] Inget ogrundat Replay- eller kartläge för 2024 och tidigare.
- [ ] Tostared 2025 är metadata-only, medan Grind→Torrås är ett enda verkligt uppmätt 15-km-segment med n=130.
- [ ] Profilbilder från sociala medier används inte; initialavatarer är den överenskomna lösningen.
- [ ] Individuella segment utan källpar markeras saknade, aldrig 0 sekunder.
- [ ] Samtliga datakort har rätt nämnare: resultat, startande och fullföljare är olika populationer.
- [ ] Både kvinnor och män visas med enbart faktiskt registrerat antal podiumresultat. 85 km 2016 har endast två kvinnliga FINISHED.

Det här är en kompletterande källgranskning, inte ett krav att Codex ändrar komponenternas formspråk eller börjar om designarbetet.
