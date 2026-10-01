# Data- och metodöverlämning till Codex – Sätila Splits

Datum: 2026-10-01. Detta är **verifierade tillägg efter den ursprungliga Codex-beställningen**, inte önskemål om att börja om.

**Utgångspunkt:** `build/full-first-draft-2026-10-01@c739b10a201ee327f4f1dfea708f8ee927d4107c`.  
**Isolerad granskningsgren:** `audit/satila-data-method-2026-10-01`.  
**Integrations-PR:** #4. Inga filer under `docs/assets`, `docs/index.html` eller `docs/data` ändras av auditgrenen.

## 1. Resultat från oberoende CI

| Kontroll | Resultat |
|---|---|
| Alla 27 upplagor, 2016–2019 och 2021–2025 | PASS |
| Resultatrader, inklusive DNS och DNF | 3 272 |
| Fullföljare, FINISHED | 2 649 |
| Rena observerade TIME-passager | 16 525 |
| Kontrollerad statusuppdelning | 2 649 FINISHED + 128 DNF + 494 DNS + 1 UNKNOWN = 3 272 |
| Officiella GPX-checksummor | 5/5 oförändrade |
| Ogrundad modern rutt kopplad till äldre edition | 0 |
| Referens-/mål-/tidsordningsfel | 0 |
| CI för exakt segmentkapacitet | PASS |
| CI för metadata-only station och sammanhängande verklig segmenttid | PASS |

Bevis: [GitHub Actions 36843284247](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36843284247) (source, pair capacity, station coverage) och nyare route-integrity workflow. Full maskinläsbar segmentmatris ligger i CI-artifact `satila-source-integrity` tillsammans med JSON för datavalidering.

## 2. P0-källfynd: 43 km 2025, Tostared saknar alla tidtagningspassager

| Station | Km på officiella timingaxeln | Antal publicerade TIME-passager |
|---|---:|---:|
| Grind | 1,2 | 135 |
| **Tostared** | **10,2** | **0** |
| Torrås | 16,2 | 130 |
| Almered | 24,0 | 134 |
| Skolan | 31,0 | 134 |
| Ramhulta | 37,0 | 135 |
| Smälteryd | 41,5 | 133 |
| PRE (teknisk) | 42,4 | 134 |
| FV (teknisk) | 42,7 | 135 |
| Mål | 43,0 | 135 |

Tostared (station UID **1416266**) finns i källans publika stationsmetadata men saknar TIME-rader. Detta är den **enda helt oobserverade analyserbara stationen i samtliga 27 undersökta upplagor**.

### Nuvarande förstautkast (strikt intilliggande metadata-axel)

- Start → Grind: **n=135**, statistiskt klar.
- Grind → Tostared: **n=0**.
- Tostared → Torrås: **n=0**.
- Torrås → Almered: **n=130**.
- Almered → Skolan: **n=133**.
- Skolan → Ramhulta: **n=134**.
- Ramhulta → Smälteryd: **n=133**.
- Smälteryd → Mål: **n=133**.

Den här definitionen gör två analyssegment onödigt tomma och innebär att en komplett historisk segmentbaserad loppplan faller tillbaka på distansfördelning där verkligt underlag finns.

### Förväntad, källtrogen implementation

Behåll `Tostared` i rå metadata, stationshistorik och proveniens som `metadata_only/no_observed_TIME`. Den får inte få en påhittad registrering, position, split eller median.

Skapa däremot `effective_analysis_boundaries` enbart från observerbara tidtagningsstationer. Då blir det sammanslagna segmentet:

**Grind (1,2 km) → Torrås (16,2 km): 15,0 timing-km, n=130 kompletta verkliga positiva tidpar**.

Det är ett observerat sammanslaget segment: `t(Torrås) - t(Grind)`, inte interpolering vid Tostared. Detta möjliggör sju verkliga sammanhängande segment med medianer för 43 km 2025.

Om användaren vill se en personlig *planerad* passagetid vid Tostared får det göras som en separat, tydligt märkt illustrativ planeringspunkt utifrån det uppmätta längre spannet; märk **ej registrerad historisk tid**. Pacingalgoritmen ska inte presentera den som källa för könspodium eller segmentstatistik.

**Acceptanstest:** `python tools/audit_station_coverage.py` ska passera och bevisa att Grind → Torrås har minst 100 giltiga verkliga par. `python tools/audit_segment_capabilities.py` visar i nuläget två luckor i den gamla metadataaxeln: dessa är inte saknade löparpassager utan en metadata-only station.

## 3. P1-analysgräns: 43 km 2023 – lågt men äkta n i mitten

| Segment | Verkliga positiva par | Kvinnor | Män | Visa statistik |
|---|---:|---:|---:|---|
| Start → Grind | 86 | 15 | 71 | median, Q25–Q75, Q10–Q90, könsmedianer |
| Grind → Torrås | 85 | 15 | 70 | samma |
| Torrås → Almered | 84 | 15 | 69 | samma |
| **Almered → Skolan** | **8** | **4** | **4** | **enbart totalmedian; inga kvantiler eller könsmedianer** |
| **Skolan → Ramhulta** | **8** | **4** | **4** | **enbart totalmedian; inga kvantiler eller könsmedianer** |
| Ramhulta → Smälteryd | 85 | 15 | 70 | alla nivåer |
| Smälteryd → Mål | 85 | 15 | 70 | alla nivåer |

Könsuppdelad Top 3 **kan** visas för de observerade fyra per kön om källidentitet och båda ändpassagerna finns, men märk `n=4 uppmätta tider`; kalla det inte automatiskt hela fältets snabbaste prestation på dessa två delsträckor.

Gränser enligt blueprint: pooled median `n >= 5`, Q25–Q75 `n >= 10`, Q10–Q90 `n >= 20`, separat könsmedian `n >= 5` inom respektive grupp.

## 4. Personlig loppplan: exakt källgräns och normalisering

För fullföljaren `r`, observerat segment `i` och sluttid `F_r`:

`s_(r,i) = t_(r,slutankare) − t_(r,startankare)`, med `t(Start)=0` som enda definierade artificiella nollpunkt. Kräver två publicerade, positiva och monotona observationer för övriga segment.

`w_i = median(s_(r,i) / F_r)` i vald kohort, när minst fem riktiga par finns. En sammanhängande, källtrogen analysaxel måste först användas (se Tostared).

`T_plan,i = T_mål × w_i / Σ_j(w_j)`. Summan över publicerade plansegment ska bli måltiden exakt, med avrundningsrest lagd i slutsegmentet.

Om sammanhängande historisk andel saknas får en fallback användas **endast för planering** och märkas `distance-based planning estimate`, aldrig `historical median` eller `observed checkpoint`. Särredovisa totalt n och n per segment; tillåt inte att ett smalt köns-/klassfilter med n under gränsen återanvänder bredare fältsiffror utan synlig metodetikett.

Säkerställ att 2025 års Grind → Torrås ger historisk andel direkt från 130 positiva verkliga par. Gör inte två falskt separata historiska andelar runt Tostared.

## 5. Övriga implementeringsvillkor

1. Den nominella tidtagningsaxeln för 2025 års 43 km slutar på 43,0 km, men GPX-displaypolyline är 42,254 km. Dessa är **två olika namngivna axlar**; GPS-längd får inte ersätta officiell tidsaxel.
2. 2025/26-arrangörens 21-km-GPX har cirka 23,043 km geometri, samtidigt som historisk EQ-klass ligger i familjen `trail22`; behåll ursprungsnamn och referens separat.
3. Officiell 85 km 2026 har egen `edition_references:[2026]`. Koppla inte utan verifiering samma fil till 85 km 2025 eller äldre år.
4. Samtliga fem ruttgeometrier är utställningsdata utan GPX-tidsstämplar. Visualiserad förflyttning mellan äkta timingankare är aldrig ett uppmätt deltagarspår.
5. En edition med många tidsstationer har inte nödvändigtvis många fullständiga segmentpar. Låt komponenternas readiness vara per delsträcka, per statistisk nivå och per grupp; använd det genererade `satila-segment-capabilities.json` som facit.

## 6. Fristående regressioner att köra före integration

```bash
python tests/test_published_data_integrity.py
python tools/audit_segment_capabilities.py --output /tmp/satila-segment-capabilities.json
python tools/audit_station_coverage.py
python tests/test_route_geometry_integrity.py
```

Ingen av dessa fyra skriver till publicerade `docs/data`; de kan köras mot den senaste Codex-databunten med `--data` där stödet finns. Om importer eller station-urval ändras av Codex måste den ändringen verifieras med en ny reproducerbar bundle innan siffror i gränssnittet uppdateras.

**Överlämning:** Cherry-picka/mergea PR #4 till bygggrenen efter att Codex kodgren är synkad, men ändra inte en aktiv fil under pågående Codex-implementering.
