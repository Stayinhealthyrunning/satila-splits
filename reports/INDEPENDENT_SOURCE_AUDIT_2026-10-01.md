# Sätila Splits – oberoende käll- och dataintegritetsgranskning

**Datum:** 2026-10-01  
**Bas:** `build/full-first-draft-2026-10-01@c739b10a201ee327f4f1dfea708f8ee927d4107c`  
**Separat gren:** `audit/satila-data-method-2026-10-01`  
**Verifiering:** [GitHub Actions 36842571845](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36842571845) (**PASS**)  
**Automatiskt test:** `tests/test_published_data_integrity.py`

## Reviderad täckning – publicerat analysunderlag

| Mått | Antal |
|---|---:|
| Tävlingsupplagor (RaceEdition) | 27 |
| Historiska år med data | 9 |
| Analyserade huvudfamiljer per år | 3 |
| Resultatrader totalt, inklusive DNS och DNF | 3 272 |
| Fullföljare, FINISHED | 2 649 |
| DNF | 128 |
| DNS | 494 |
| Okänd status | 1 |
| Publicerade TIME-observationer (split-rader) | 16 525 |
| Officiella arrangörs-GPX i ruttinventeringen | 5 |
| Strukturella fel i integritetstestet | **0** |
| Varningar i integritetstestet | **0** |

Åren: **2016, 2017, 2018, 2019 och 2021–2025**. År 2020 ingår inte och får inte presenteras som ett uppmätt nollår. År 2026 är framtida tävlingsupplaga vid granskningstillfället och dess arrangörs-GPX är en referensgeometri, inte ett tävlingsresultat.

### Årsvis täckning

| År | Resultatrader | Fullföljare | DNF | DNS | Okänd |
|---|---:|---:|---:|---:|---:|
| 2016 | 343 | 260 | 12 | 71 | 0 |
| 2017 | 346 | 282 | 13 | 51 | 0 |
| 2018 | 297 | 239 | 21 | 37 | 0 |
| 2019 | 342 | 277 | 12 | 53 | 0 |
| 2021 | 394 | 308 | 16 | 69 | 1 |
| 2022 | 354 | 300 | 12 | 42 | 0 |
| 2023 | 351 | 286 | 11 | 54 | 0 |
| 2024 | 393 | 323 | 14 | 56 | 0 |
| 2025 | 452 | 374 | 17 | 61 | 0 |
| **Totalt** | **3 272** | **2 649** | **128** | **494** | **1** |

**Viktig denominatorregel:** `results` är offentliga resultatrader, **inte antalet startande** och inte antalet fullföljare. Startande bör beräknas med separat statuspolicy där DNS inte felaktigt ingår. Fullföljandeandel ska ange vald nämnare och hantera den enda UNKNOWN separat. Inga procentandelar får bilda en skenprecision genom att utelämna dessa statusdefinitioner.

### Faktisk täckning av publika tidtagningsstationer

Antalet tillgängliga stationer varierar mellan år och distans. Detta ska styra vilka interaktiva delsträckor, individuella insikter och historiska loppplaner som kan presenteras:

| År | 85 km | 43 km | 22 km |
|---|---:|---:|---:|
| 2016 | 3 | 5 | 5 |
| 2017 | 4 | 6 | 4 |
| 2018 | 5 | 5 | 4 |
| 2019 | 6 | 6 | 5 |
| 2021 | 5 | 7 | 5 |
| 2022 | 9 | 9 | 7 |
| 2023 | 9 | 9 | 7 |
| 2024 | 9 | 9 | 7 |
| 2025 | 9 | 10 | 7 |

Dessa siffror innefattar även eventuella tekniska stationer (exempelvis `PRE` eller `FV`), som **inte automatiskt är analysgränser**. En edition med nio publika stationer har därför inte nödvändigtvis åtta meningsfulla analyssplitar. Antal giltiga *segmentpar* måste beräknas per löpare och per edition från exakta observerade passager.

## Omsatta QA-kontroller

Testet läser de redan genererade browserbundlarna utan att ändra dem:

1. Katalogens 27 nycklar, tre distansfamiljer per tävlingsår och avsaknad av fabricerat 2020.
2. Unika resultat-ID och unika publika checkpoint-ID inom varje edition.
3. Publika `TIME`-passager har en känd resultat-/stationsreferens och en positiv tid.
4. Inga dubbletter på `(result_id, station_uid)`.
5. Samtliga statusantal och splitantal summerar exakt till edition-katalogen.
6. Varje `FINISHED` har positiv sluttid och en matchande publicerad målpassage. Icke-`FINISHED` tilldelas inte en sluttid.
7. Tidsordningsavvikelser och DNS med passagetid flaggas som källvarningar i stället för att tyst modifieras.
8. Arrangörens fem GPX-källhashar jämförs med de explicit frysta värdena.
9. Återanvänd 2025/2026-rutt är kopplad enbart till **2025 års 21- och 43-km-upplagor** i det nuvarande historiska resultatunderlaget. Ingen äldre edition lånar den.
10. Route asset, metadata och historisk tävlingsupplaga hålls separata.

## Metodgränser för vidare utveckling

- De 16 525 observationerna är faktiska källposter, inte 16 525 komplett jämförbara segmentpar. Segmenttid får räknas först när två relevanta och monotona observationer finns för samma deltagare.
- Den officiella arrangörsrutten för 21 km har en GPX-polyline på cirka 23,043 km. Den officiella tidtagningens distansaxel ska därför **inte** ersättas av GPX-kilometrering. På motsvarande sätt skiljer sig 43-km-GPX-geometrin (cirka 42,254 km) från tävlingsetiketten. Båda värdena får redovisas, tydligt namngivna.
- Endast 2025/2026-återanvändningen för 5/10/21/43 km är uttryckligen accepterad av projektägaren. Att andra år råkar ha samma nominella distans ger inte automatiskt stöd för jämförbar whole-course-historik.
- Varken splitbaserad status eller GPX-interpolering ska användas för att konstruera en officiell saknad passage.
- Inga publika löparporträtt/sociala profilbilder samlas in.

## Integrering utan kollision med Codex

Auditgrenen tillför bara `tests/test_published_data_integrity.py`, `.github/workflows/source-integrity.yml` och denna rapport. Den ändrar varken frontendkod, importer, browserbundlar, Hero eller `BUILD_STATE.json`. Integrera via separat PR mot aktuell buildgren när det passar. Codex arbetar i separat `codex/saetila-complete-first-draft`.
