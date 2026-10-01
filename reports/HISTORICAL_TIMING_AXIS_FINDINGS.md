# Historiska kontrollpunkter och banversioner: varför namnmatchning inte räcker

**Datum:** 2026-10-01  
**Underlag:** 27 kuraterade EQ Timing editioner, `config/course-versions.json`, och arrangörens GPX-referenser.  
**Reproducerbar matris:** `tools/audit_historical_station_alignment.py` (24 par av närliggande tillgängliga år, tre distansfamiljer).  
**CI-artifact:** `satila-history-checkpoint-alignment.json` i source-integrity-workflow.

## Två självständiga problem att särskilja

1. **En station kan ändra kilometertal**, även när den behåller sitt namn.
2. **En bana kan ändras kraftigt medan en station behåller både namn och tidtagningskilometer**. Stationsmetadata är då otillräcklig som geografisk jämförbarhetsbevisning.

Båda är observerbara i Sätilas historiska 43-km-serie.

### Exempel: 43 km, 2021–2025

| Kontroll | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Grind | 1,2 | 1,2 | 1,2 | 1,2 | 1,2 |
| Torrås | 8,0 | 8,0 | 8,0 | 8,0 | **16,2** |
| Almered | 24,0 | 24,0 | 24,0 | 24,0 | 24,0 |
| Skolan | 31,0 | 31,0 | 31,0 | 31,0 | 31,0 |
| Ramhulta | 37,0 | 37,0 | 37,0 | 37,0 | 37,0 |
| Smälteryd | — | 41,5 | 41,5 | 41,5 | 41,5 |
| Mål | 43,0 | 43,0 | 43,0 | 43,0 | 43,0 |

Även om både 2024 och 2025 betecknas som 43 km kan `Grind→Torrås` **inte** behandlas som samma delsträcka: den officiella tidtagningsaxeln ger 6,8 km 2024 och 15,0 km 2025. **Tostared** tillkommer i 2025 års metadata vid 10,2 km men har n=0 verkliga TIME-passager; för 2025 är Grind→Torrås ändå ett legitimt sammanslaget observerat segment (n=130).

### Den mindre uppenbara avvikelsen 2022 → 2023

Torrås ligger fortfarande på 8,0 timing-km och flera andra stationer behåller sina namn och angivna distanser. Men de autentiska deltagarspåren separerar i två olika bangeometrier enligt `research/GPX_43KM_ANALYSIS.md`:

- 2021–2022 är en sammanhängande deltagarbaserad kurskandidat.
- 2023–2025 är en annan, jämnare deltagarbaserad kurskandidat.
- Korridoren mellan 2022 och 2023 har i forskningsrapportens jämförelse endast omkring **74,43 % inom 25 m** (bidirektionell jämförelse). En större divergens uppkommer redan kring 6,5–6,8 km.
- Båda normaliserade rutterna är **kandidater**, inte automatiskt auktoritativa arrangörsbanor. Se `config/course-versions.json`.

Det vore således metodfel att förena årens segment i ett tidsseriediagram bara för att kontrollnamn eller kilometertal sammanfaller.

## Analys- och UI-kontrakt inför Codex

- Redovisa KPI för enskilt år även där historisk banjämförbarhet saknas; använd n och källhänvisning.
- Historiskt antal deltagare/fullföljare kan jämföras per nominell tävlingsfamilj när år och populationsdefinition tydligt anges.
- Historisk tid, medelfart, relativa segmenttider, banprofil och place progression får **inte** agg­regeras över olika år som samma geometri utifrån enbart samma distansnamn eller stationsnamn.
- Håll isär `station_uid`, `station.name`, `station.km`, `RaceEdition` och `course_version`; station UID är inte en konstant mellan åren.
- När en stationsposition ändras ska samma sträcknamn i olika upplagor minst visa årskvalificerat kilometertal. Ingen implicit segmentduell över olika banversioner.
- Presentera arrangörens 2025/26-bana för 21/43 km endast i editioner där explicit återanvändning är godkänd. Separat officiell 85-km-rutt 2026 ska inte kopplas till äldre edition.
- Ett framtida bevis för en gemensam whole-course-version kan upphöja jämförbarhet genom ett **explicit verifierat kontraktsbeslut**. Den här rapporten förbjuder inte sådan framtida uppgradering; den förbjuder omotiverad automatisk uppgradering.

## Regression

```bash
python tools/audit_historical_station_alignment.py \
  --output /tmp/satila-history-checkpoint-alignment.json
python -m unittest discover -s tests -p test_course_comparability_contract.py -v
```

Den första kontrollen jämför **24 närliggande årspar** över 85/43/22-familjer och kräver att 2024→2025 års ändring av Torrås (+8,2 km) och 2022→2023 års separata deltagarbaserade kurskandidater är synliga i matrisen. Den genererade JSON-filen innehåller inte deltagaridentitet eller råspår.

**Arbetsgräns:** Denna QA-rapport ändrar inte frontend, och dess rekommendationer ska gå in i Codex historik- och komponentbearbetning via separat integrationsgranskning.
