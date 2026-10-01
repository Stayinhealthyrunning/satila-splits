# Verifierad ren återbyggnad av Sätila Splits publicerade datamodell

**Datum:** 2026-10-01  
**Kontrolltyp:** Oberoende återställning ur privat käll- och GPX-paket till separat lokal testkatalog, utan skrivning till GitHub eller någon aktiv Codex-arbetskopia.  
**Verktyg för framtida återkörning:** `tools/audit_rebuild_parity.py`; enhetstester `tests/test_rebuild_parity_contract.py`.

## Inmatningskedja

- Privat källa: `Satila_Splits_PRIVATE_SOURCE_BACKUP_2026-10-01.zip`.
- Full paket-SHA-256: `9360bf36cd7b042d13d536e8551c3d4c65da2911894d718475dd79090a439fd8`.
- Inre frysta EQ Timing-ZIP: **6 626 914 byte**, SHA-256
  `b7b0b6ad97b504900d8dc06e749d7e9818312d88f37edb9424030c3847457b89`.
- ZIP-integritet kontrollerad (`ZipFile.testzip() is None`). Inre arkivet innehåller **560 ZIP-medlemmar**, inklusive `eqtiming/` och `eqtiming-full/`, nio år: 2016–2019, 2021–2025.
- De fem ursprungliga arrangörs-GPX-byten återställdes ur privata paketet och SHA-256-kontrollerades mot `SOURCE_MANIFEST_PRIVATE.json`.
- Originalbytes bevarades. Endast inmatningsfilernas lokala **filnamn** normaliserades vid export så att de motsvarar GitHub-repots publicerade `source_filename`-metadata (`Sätila Trail <distans> - 2026.gpx`).

## Oberoende återbyggnad

Återställd `eqtiming-full` och originalbyte-GPX användes i befintlig fryst Python-exporter `build_satila.py`, med samma händelsekatalog. Exporten skrevs under en **egen temporär katalog**.

Exporterloggen:

| Mått | Återbyggt |
|---|---:|
| Råa EQ sidobservationer lästa före kuratering | 20 533 |
| RaceEdition | 27 |
| Publicerade unika resultatrader | 3 272 |
| FINISHED | 2 649 |
| Verkliga TIME-observationer i publicerade bundles | 16 525 |
| Publicerade JSON-filer inklusive 27 races, fem rutter och metadata | **36** |

Officiella GPX-längder i återskapad inventory: 5,533 / 10,876 / 23,043 / 42,254 / 87,866 km för 5/10/21/43/85-km-filerna (displaypolyline, inte officiell timingdistans).

## Hashjämförelse och det enda upptäckta metadatafallet

En första återbyggnad med ASCII-filnamnen `Satila Trail …` gav **35 av 36 byte-identiska JSON-filer** jämfört med den frysta lokala publicerade referenskopian. Den enda avvikelsen var `route-inventory.json`, och där skiljde sig endast de fem fälten `source_filename`; samtliga övriga fält, inklusive alla fem original-GPX-hashar och editionsreferenser, var lika.

En andra ren återbyggnad återställde källfilernas kanoniska svenska filnamn innan export, med exakt oförändrade GPX-bytes. Även denna gav samma **35/35 byte-identiska övriga JSON-filer**. Den återskapade `route-inventory.json` gav då GitHub-blob-SHA:

`c2426e645708f830f461af02191cc4739c5f946b`

Detta är **exakt blob-SHA för `docs/data/route-inventory.json` på audit-PR #4**, kontrollerat via GitHub-connectorn. Andra stickprov från samma lokalreferens, däribland `bootstrap.json`, `source-fingerprints.json` och `races/2025-trail43.json`, hade också samma GitHub-blob-SHA som PR #4.

**Slutsats:** den frysta privata arkivkopian kan återgenerera alla 36 publicerade JSON-filer i deras kanoniska GitHub-format. Inga mätvärden, deltagarposter eller GPX-koordinater behövde korrigeras. Det tidigare filnamnsfallet var en privat arkivkonvention, inte en skillnad i officiellt GPX-innehåll.

## Reproducerbar kodkontroll vid framtida import

```bash
# Återställ privat källarkiv och arrangörs-GPX separat och säkert först.
python tools/build_satila.py \
  --source /private/eqtiming-full \
  --gpix /private/organizer-gpx-original-filenames \
  --events config/eqtiming-events.json \
  --out /tmp/satila-independent-rebuild

python tools/audit_rebuild_parity.py \
  --published docs/data \
  --rebuilt /tmp/satila-independent-rebuild \
  --report /tmp/satila-rebuild-parity.json
```

Vid avvikande normaliserat privat filnamn får jämförelsen **endast** undanta `source_filename` i `route-inventory.json` efter kontroll av övriga fält, framför allt `source_sha256`; varje avvikelse i en race-bundle, ruttgeometri, editionsreferens eller källhash är ett verifieringsfel. Sex separata regressionsfall testar detta i `tests/test_rebuild_parity_contract.py` och ingår i PR #4:s CI.

**Sekretess:** Inga råa EQ-deltagararkiv, ofiltrerad databas eller original-GPX har lagts i repots Git-historik. Den privata återställningen ligger endast i den temporära arbetsmiljön. Projektägaren behöver fortfarande bevara den nedladdningsbara privata backupfilen i säker långtidslagring enligt `reports/SOURCE_ARCHIVE_RETENTION_AND_RESTORE.md` och issue #5.
