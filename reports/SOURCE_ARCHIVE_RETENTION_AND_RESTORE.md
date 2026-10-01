# Källarkiv – bevarande och återställning utan publik rådata

**Upprättad:** 2026-10-01  
**Gäller:** Sätila Splits, fryst EQ Timing-import och arrangörens officiella GPX.  
**Karaktär:** Operativ skyddsrutin, inte automatisk förlängning av GitHub Actions lagring.

## Varför detta behövs

Den kuraterade databunten i `docs/data/` och dess kontroller i Git-repot ger en granskningsbar, fungerande webbplats. Den ursprungliga sidindelade EQ Timing-importen finns däremot som en tidsbegränsad artifact från:

- Workflow: `Import EQ Timing results`
- Run-ID: **36818159977**
- Artifact: `satila-eqtiming-raw-36818159977`
- Känd storleksordning: cirka **6,6 MB komprimerat**.
- Workflowens `retention-days`: **30**.
- Importen utfördes 2026-10-01. **Verifierad artifact-metadata:** `expires_at = 2026-10-31T05:09:48Z`, `expired = false` vid kontroll 2026-10-01. Ladda ned och verifiera en privat långtidskopia **senast 2026-10-25** så att det finns marginal inför sista utgångstid. ZIP-artifactens av GitHub angivna digest: `sha256:b7b0b6ad97b504900d8dc06e749d7e9818312d88f37edb9424030c3847457b89`. Observera att en **ny** ZIP skapad med `Compress-Archive` får en annan SHA-256 än GitHub-artifactens ZIP även om de extraherade filerna är identiska.

**Risk:** Det räcker inte att bara spara genererad `bootstrap.json`, 27 race-bundlar och källfingeravtryck för att exakt kunna återköra `tools/build_satila.py` senare. De fullständiga råa paginerade svaren, metadata och käll-GPX behövs.

## Omedelbar åtgärd innan artifacten går ut

En användare med åtkomst till repositoryt kör lokalt i en säker katalog, **inte** under `docs/` och **inte** i ett publikt Git-commit:

```powershell
$repo = "Stayinhealthyrunning/satila-splits"
$dest = "C:\Git\satila-source-archive-2026-10-01"

New-Item -ItemType Directory -Force -Path $dest | Out-Null
gh auth status
gh run download 36818159977 --repo $repo --name satila-eqtiming-raw-36818159977 --dir $dest

# Kontrollera att katalogen eqtiming-full finns och innehåller
# event.json, contestants.json, manifest.json och results/-träd för varje år.
Get-ChildItem "$dest\eqtiming-full" -Directory | Select-Object Name

# Spara en fristående hash för själva arkivpaketet om du gör ett ZIP:
Compress-Archive -Path "$dest\eqtiming-full" -DestinationPath "$dest\satila-eqtiming-full-2026-10-01.zip" -Force
Get-FileHash "$dest\satila-eqtiming-full-2026-10-01.zip" -Algorithm SHA256
```

Om artifacten från workflowen i stället packas ut direkt i destinationsroten, använd `Get-ChildItem $dest` och justera sökvägen; förutsätt inte ZIP-innehållets mapplayout utan kontroll.

Förvara arkivet i en **privat, åtkomstbegränsad och säkerhetskopierad** lagringsplats. Det får inte committas i den publika Sätila-koden, läggas som öppet GitHub Release-asset eller inkluderas i den publicerade Pages-mappen. Råa `contestants.json` och kompletterande källfält kan innehålla andra personuppgifter än de avsiktligt sanerade publika resultatuppgifterna.

## Hur integriteten kan verifieras vid återställning

Nuvarande frysta källmanifest:

`docs/data/source-fingerprints.json`

Manifestet innehåller SHA-256 för **event.json per tävlingsår** och verifierade EQ event-ID från `config/eqtiming-events.json`. Fem officiella arrangörs-GPX-hashar finns i `docs/data/route-inventory.json` och `tests/test_route_geometry_integrity.py`.

Kör:

```bash
python -m unittest discover -s tests -p test_source_chain_of_custody.py -v
python tests/test_published_data_integrity.py
python tests/test_route_geometry_integrity.py
```

När en komplett säker kopia finns kan byggaren köras i en **separat temporär katalog**:

```bash
python tools/build_satila.py --source /path/to/eqtiming-full --gpix /path/to/gpx --events config/eqtiming-events.json --out /tmp/satila-independent-rebuild
```

Jämför SHA-256 för alla genererade `*.json` mot nuvarande `docs/data/**/*.json` och dokumentera eventuella avvikelser. **Kör aldrig återbyggnad över `docs/data/` i en parallell Codex-utvecklingsgren**; en rekonstruktion får inte tyst skriva över UI- eller datamodelländringar.

## Begränsningar som är viktiga att dokumentera

1. Fingerprint-manifestet innehåller eventfilernas SHA-256, **inte en fullständig per-fil-manifestering av alla contestants- och pagineringsfiler**. Ett bevarat komplett råarkiv är därför fortfarande nödvändigt.
2. `source_archive` i bootstrap namnger en GitHub-run och utgör inte en permanent backup.
3. En framtida ny hämtning från EQ Timings öppna API kan skilja sig från den ursprungligen frysta datan, även om tävlingsåret är detsamma. Ny källa är då en **ny importerad revision**, inte en byte-identisk återställning av 2026-10-01.
4. Källarkivets roll är reproducerbarhet och verifierbarhet; publicerad frontend ska även fortsättningsvis enbart använda sanerade, avsiktligt kuraterade bundlar.
5. De av arrangören tillhandahållna GPX:erna ska bevaras med sina ursprungliga byte och checksummevärden. Ändra inte internt namn `2025` i en 2026-fil som en del av normalisering; lägg årstolkningen i metadata.

**Status 2026-10-01:** Arkivet finns tillgängligt på GitHub och exakt utgångsdatum samt GitHubs ZIP-digest är verifierade. Den här texten innebär **inte** att ett nytt, separat långtidsarkiv redan har skapats.
