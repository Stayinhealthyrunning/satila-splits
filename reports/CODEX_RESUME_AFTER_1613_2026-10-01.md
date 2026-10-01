# Sätila Splits – exakt Codex-återstart efter kvotåterställning 2026-10-01

**Observera:** Denna återstart gäller *integrationens* nya releasekandidat, inte en omstart från `main` eller en ny dataimport.

## Grenar och vad som finns sparat

| Git-ref | Syfte |
|---|---|
| `codex/saetila-complete-first-draft@a71a5ef161abab7ec0a6a1f53e9b7621c8391fe3` | Din första fullständiga lokala Codex-checkpoint, 18 commits ovanpå första byggutkastet; **rör ej destruktivt**. |
| `audit/satila-data-method-2026-10-01@8aef5bec258b1f1ff6addc0f78b163f3a225f602` | Fullständig separat käll-/statistik-/metod-/publiceringsaudit. |
| `integration/codex-independent-qa-2026-10-01` | Två-parent-merge ovanpå Codex med auditens 49 separata filer och de senaste riktade releasekorrigeringarna. **Läs senaste HEAD** när arbetet startar igen. |
| [Draft PR #7](https://github.com/Stayinhealthyrunning/satila-splits/pull/7) | Integration mot ursprungliga Codex-grenen; ännu inte mergad. |

Den lokala mappen `C:\Git\satila-splits\reports\qa-local\` är otrackad och innehåller Codex egna QA-bilder. **Behåll den**. Inga råa deltagar-GPX eller privata EQ-källor ska committas i publicerade `docs/`.

## Första Codex-kommandon när kvoten återställs

Kör i befintlig gitklon `C:\Git\satila-splits`, utan reset/clean/omkloning:

```powershell
cd C:\Git\satila-splits
git status --short
git fetch origin --prune
git log -1 --oneline origin/integration/codex-independent-qa-2026-10-01
git switch -c codex/saetila-release-finish origin/integration/codex-independent-qa-2026-10-01
git status --short
```

Om den föreslagna nya lokala grenen redan finns, avbryt `switch -c` och inspektera innan du gör ändringar. Om `git status` visar *andra* osparade kodändringar än `?? reports/qa-local/`, spara dem avgränsat innan grenbyte. Inga `git reset --hard`, `git clean -fd` eller force-push.

Codex får därefter fortsätta den visuella slutfinishen i en **egen** gren, checka in mindre funktionella steg och öppna en Draft PR tillbaka mot integrationsgrenen. Publicera aldrig till `main` eller Loppanalys.se utan projektägarens uttryckliga godkännande.

## Vad ChatGPT-integration redan levererat

- Codex 18 commits + QA-spårets 49 avsiktligt fristående filer sammanförda utan konflikter.
- Fulla publicerade käll-/statistik-/GPX-/privatlivs-/granskningspakettester mot den faktiska nya Codex-koden: **PASS**.
- Hero/footer sakligt korrigerade: inte längre ”Samma stigar”.
- Sätila-native jämförelserubrik och explicit åtskillnad timingaxel/GPX-displaylängd.
- Riktig user-driven `pushState`, `popstate` och navigering med Bakåt/Framåt vid växling av år/distans.
- Tangentbords- och dialogfokus, Escape för mobilmeny, synligt felmeddelande om en editionfil saknas.
- Historiska 43-km-delsträckor med misstänkt timingdistans 2023/2024 Torrås→Almered visar fortfarande riktig TIME och n, men ingen okvalificerad fysisk min/km.
- Vanlig banprofil har nu stabila SVG-händelsemål under skrubbning (samma teknik Codex redan införde i H2H).
- Fyra separata release-gates (saklig text, navigering, tangentbord/UX, tempo-/distansgräns) PASS på integrationscommit `f08335d`.
- Codex nya `docs/data/coverage.json` inkluderas nu uttryckligen som **riktig publicerad fixture** i de tre offline-browserregressionerna, i stället för felaktig 404 från en ofullständig testharness.

## Regler för återstående funktionalitet och design

1. Läs [PR #7](https://github.com/Stayinhealthyrunning/satila-splits/pull/7), `reports/FINAL_INTEGRATION_HANDOFF_2026-10-01.md`, `reports/CODEX_PARITY_AUDIT.md` och aktuell `BUILD_STATE.json`.
2. Kör `python tools/run_release_candidate_checks.py --source`; för browsergruppen `python tools/run_release_candidate_checks.py --browser`, samt `tests/browser_release_navigation_acceptance.py`, `tests/browser_release_ux_acceptance.py` och `tests/browser_release_pace_capability_acceptance.py` på samma HEAD.
3. Prioritera kvarvarande blueprintgap som har **verkligt källstöd**, därefter visuell pixel-/interaktionsgranskning på 1440, 900, 768 och 390 px mot godkänd designreferens och Hero.
4. Kontrollera särskilt sista Codex-fynden: mobilens distanskort får inte överlappa upplagerubriken och Hero-bilden ska synas i QA-skärmbilderna (asset-path i testharness är inte samma sak som att filen saknas i produktions-HTML).
5. Kontrollera individuell profil, D16/D18 och de fem prestationsexemplen mot separata tempo-/distansgränser; bibehåll alla källbaserade tidsvärden och fallbacketiketter.
6. `2025-trail43` Tostared är metadata-only (0 TIME); riktig Grind→Torrås n=130. `2023-trail43` har två segment med n=8/F=4/M=4; `2016-ultra85` har F=2. Ingen syntetisk passagetid, kvinnligt brons eller inlånad modern historisk 85-km-rutt.
7. Både rutt och höjdprofil ska styra en delad GPX-visningsposition. Ingen deltagar-GPS, bara illustrativ markör mellan observerade TIME-ankare. Återanvänd gärna godkända SVG-lösningar från vår redan granskade integration.

**Status vid skrivning:** Fullständig browserregression efter sista fixture-uppdatering är inlagd i `.github/workflows/integration-candidate.yml`. Kontrollera **senaste** körningens utfall innan statusen sätts till redo för publicering. Ett gammalt grönt test motsvarar inte automatiskt ny Codex-kod.

## Plan för slutleveransen

- En grön samlad QA på samma commit med source/metod, tre skärmstorlekar karta/H2H, samtliga 27 editioner på desktop/mobil och alla fyra release-gates.
- Fullständig användargransknings-ZIP från **exakt samma** commit.
- Visuell sign-off utifrån Hero/designboard.
- En tydlig slutrapport med kvarstående `gated_by_evidence` och aktiva funktioner, utan automatiskt merge/publicering.
