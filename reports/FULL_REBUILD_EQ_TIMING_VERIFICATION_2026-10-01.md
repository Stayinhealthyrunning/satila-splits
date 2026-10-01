# Fullständig reproducerbarhetsverifiering – publicerade Sätila-bundlar

**Verifierad:** 2026-10-01  
**Isolerad revisionsgren:** `audit/satila-data-method-2026-10-01`  
**GitHub-träd som jämfördes:** commit `c69c5c42956b22dc928072d55915a322ac6f30e9`  
**Källdata:** Privat fryst EQ Timing ZIP `Satila_EQTiming_PRIVATE_source_2026-10-01.zip`, fem oförändrade arrangörs-GPX från projektägaren, fryst `config/eqtiming-events.json`.  
**Kontrolltyp:** SHA-1 av **exakta Git-blobbyte** och byte-för-byte-rekonstruktion, inte bara antal eller schemalikhet.

## Slutligt utfall

| Test | Resultat |
|---|---:|
| Publicerade JSON-filer på den kontrollerade GitHub-commiten | 36 |
| Filer från självständig ren återbyggnad | 36 |
| Exakt identiska Git-blob-SHA, parvis | **36/36** |
| Saknade filer | **0** |
| Extra filer | **0** |
| Avvikande filer | **0** |
| Tävlingsupplagor | 27 |
| Resultatrader i ren återbyggnad | 3 272 |
| Fullföljare i ren återbyggnad | 2 649 |
| Verkliga publicerade TIME-passager i ren återbyggnad | 16 525 |
| Officiella GPX-referensfiler | 5 |

Den rena exporten rapporterade `EQ full observations 20533` som antal granskade käll-ITEMS före publicerad status- och TIME-filtrering. Det är **inte** antalet publicerade tidsobservationer. Efter den dokumenterade normaliseringen publiceras 16 525 TIME-rader.

**Referens-SHA för tre övergripande filer:**

| Fil | Git blob-SHA |
|---|---|
| `docs/data/bootstrap.json` | `9da891525282fe3310c419ec0720605801ea4c6e` |
| `docs/data/route-inventory.json` | `c2426e645708f830f461af02191cc4739c5f946b` |
| `docs/data/source-fingerprints.json` | `feed33b1426fe2b5c57f40ed87eab99115a32f30` |

## Utfört reproduktionsförfarande

1. Kontrollerade den privata källbackupens SHA-256: `9360bf36cd7b042d13d536e8551c3d4c65da2911894d718475dd79090a439fd8` (6 692 068 byte).
2. Kontrollerade dess frysta EQ-käll-ZIP mot `b7b0b6ad97b504900d8dc06e749d7e9818312d88f37edb9424030c3847457b89` (6 626 914 byte).
3. Använde extraherade `eqtiming-full/` och exakt den frysta års-/eventkatalogen med `tools/build_satila.py`.
4. Använde de **fem checksummeverifierade råa GPX-bytefilerna**. Vid ren export gavs deras arbetskopior kanoniska UTF-8-filnamn `Sätila Trail {5|10|21|43|85} - 2026.gpx`. Själva XML-innehållet/ursprunglig källfil ändrades inte.
5. Exporterade till en temporär katalog, aldrig till GitHub-grenens `docs/data/`.
6. Jämförde rekonstruktionens samtliga `*.json` mot de 36 publicerade blob-SHA som hämtades ur GitHubs faktiska träd för commit `c69c5c4`.
7. Resultat: **36 matchade, 0 saknade, 0 extra, 0 olika**.

### Varför GPX-filnamnen behöver skiljas från GPX-innehållet

Den privat mottagna GPX-uppladdningen har ett ursprungligt märkligt filnamn med bokstavsföljden `Sa╠êtila`. Om exportverktyget läser filerna direkt därifrån blir 35/36 JSON-filer identiska, men `source_filename` i just `route-inventory.json` får detta uppladdningsnamn och skiljer sig från GitHubs kanoniska publiceringsnamn `Sätila`.

Det är en **ren manifest-/filnamnsskillnad**, inte en skillnad i GPS-punkter, GPX-hash, registrerade tider eller resultat. Byte-för-byte-testet ovan använde kanoniska namn på temporära **arbetskopior** och gav 36/36 matchning. Den privata backupen ska fortsatt innehålla de råa, orörda filerna med samma SHA-256 som registrerats i `route-inventory.json`.

## Exakt återbyggnadskommando (separat arbetskatalog)

```bash
python tools/build_satila.py \
  --source /path/to/unpacked/eqtiming-full \
  --gpix /path/to/checksum-verified-canonical-gpx-copy \
  --events config/eqtiming-events.json \
  --out /path/to/temporary/rebuild-output
```

**Publiceringsbeslut:** De sex rekonstruerade filgrupperna är reproducerbara utifrån fryst källarkiv. Detta verifierar datapipeline och exporterad analysinput, **inte** hela framtida Codex-designen, alla användarflöden eller publiceringsgodkännande. Vid nästa ändring i importer, källrevision eller data måste exporten och 36-filsjämförelsen köras igen med tydlig referens-HEAD.

**Informationsskydd:** Ingen rå deltagarfil, källa-JSON eller temporär `satila.sqlite` har lagts till i den offentliga webbplatsen eller denna GitHub-revision.

## Återanvändbart verifieringsverktyg

`tools/audit_rebuild_against_published.py` är nu checkat in för nästa källdata- eller Codex-integration. Det tar källorna som **lokala privata kataloger**, kontrollerar SHA-256 för fem GPX, skriver oförändrade GPX-byte till en temporär katalog under kanoniska filnamn, kör `tools/build_satila.py` i en fristående temporär output och jämför alla JSON-filer via exakt Git-blob-SHA mot vald `--published`-katalog. Rådata kopieras aldrig till `docs/`.

Exempel efter att arkivet packats upp lokalt:

```bash
python tools/audit_rebuild_against_published.py \
  --source /private/eqtiming-full \
  --original-gpx /private/raw-organizer-gpx \
  --events config/eqtiming-events.json \
  --published docs/data \
  --report /tmp/satila-independent-rebuild-metadata.json
```

**Verifieringsbevis på fryst första utkast:** kommandots motsvarande fristående återskapning utfördes lokalt och alla 36 JSON-blobbar matchade GitHub-trädet. Det nyincheckade CLI-skriptet automatiserar samma arbetsordning; råarkivet är privat och scriptet körs därför inte som vanlig publik PR-CI utan att åtkomstbehöriga källfiler uttryckligen tillförs körmiljön.
