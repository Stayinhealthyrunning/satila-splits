# Sätila Splits – verifierad slutcheckpoint inför nästa Codex-pass

**Låst funktionell kandidat (2026-10-01):** 217439a489b210a8cb485a19ff689581d527cc6a på integration/codex-independent-qa-2026-10-01.

**Full 4/4 PASS på exakt denna commit:** [Actions #36875529003](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36875529003). Samtliga source-and-method, browser-core, release-gates och review-package är godkända. [Draft PR #7](https://github.com/Stayinhealthyrunning/satila-splits/pull/7) kvarstår; main och den ursprungliga Codex-grenen är orörda.

## Exakt granskningsmaterial

- Statisk kandidat: GitHub artifact satila-codex-integrated-review, ID **11168981431**, upphör **2026-10-31**. Inre ZIP: **832 401 byte**, SHA-256 **040288de9795b5fb1fae7ba45895baf6cc24254c3a9c13c82b22202ccb8da3ab**.
- Dubbel ZIP-integritet PASS; **45 arkivposter** (44 sajtfiler plus gransknings-README). Inga originala privata EQ Timing-rawfiler ingår.
- Browserbilder/loggar: integration-browser-evidence, ID **11169510950**, upphör **2026-10-15**. Full-page vid 1440, 900, 768, 390 px och duell vid 1440/900/390.
- 390-skärmbilden granskades även visuellt: Heatmap har nu svepanvisning och aktiv segmentmarkering, kartan anger illustrativ proportionell position, och loppplanen har svepanvisning och explicit evidensreservation. Grön maskinell QA är fortfarande inte slutligt ägargodkännande av designen.

## Redan färdigt – bygg inte om

- 27 editions (2016–2019 och 2021–2025), 3 272 resultat, 2 649 FINISHED, 128 DNF, 494 DNS, 1 UNKNOWN, 16 525 offentliga TIME och fem källlåsta arrangörs-GPX. Inga påhittade historiska banor.
- D06: 2025 trail43 Tostared metadata-only (0 TIME) visas i stationsflödet men inte som falsk nedgång i observerad passagetäckning. Grind→Torrås är verkligt segment n=130; sju effektiva segment.
- T01: elva källstödda sorteringsval, native tangentbord och deterministisk sidindelning. D07: två nivåer för scatter-zoom plus reset och source-class-tooltip.
- K03: val från D14, D15, D16, D17, D18, D19 och segmenttabell uppdaterar podium, Course Intelligence, diagram och på tillåtna editions karta/höjdprofil. Mus och SVG Enter/Space testas automatiskt.
- K03/D23: timing-km projiceras proportionellt på officiell GPX för en **illustrativ segmentmitt**, aldrig som uppmätt kontrollpunkt. Kartmarkör, höjdmarkör och state har samma displaydistans.
- D11 sista verkliga segmentstyrka, D18/D19 gemensamt klassval, D21 varierande n, D22 segmentkoppling, T04 DNF Okänt och T07 displayruttens publicering/evidens implementerade. K04 Replay och K05 kartduell 2–5 finns redan.
- T06 visar historisk segmentandel och TIME-par-n, samt nya kolumner **D+/D−: Ej verifierat** och **Underlag: EQ Timing TIME-par**. Mobilanvisning finns för resultat-, segment-, plan- och heatmapöversikt.

## Avgränsade återstående punkter

1. Projektägarens visuella slutgodkännande mot docs/assets/design-reference.webp och faktiskt innehåll vid 1440/900/768/390. Codex bör enbart rätta konstaterade layout- eller interaktionsavvikelser.
2. K01/D23 fysiskt förankrade checkpointmarkörer och numerisk segment-D+/D− är källevidensspärrade. En proportionellt markerad position får inte ersätta uppmätta ankare.
3. K02 historisk dubbelbana, D25 sammanhängande flerårig prestationsserie, D26 jämförbara helbanerekord och DNF-avbrottsgeografi är också källevidensspärrade. Låna aldrig arrangörens 2026-ultra till 2025.
4. Ägaren behöver spara den redan producerade privata EQ-källbackupen på egen åtkomstbegränsad långtidslagring före artifact-utgång 2026-10-31, helst före 2026-10-25. Se issue #6. Äldre privata Suunto-deltagarspår bevaras separat.

## Säker återstart för Codex

Ändra inte ägarens ursprungliga lokala C:\Git\satila-splits eller reports\qa-local. Gör inga reset --hard, clean -fd, checkout -f eller force-push.

~~~powershell
cd C:\Git\satila-splits
git status --short
git fetch origin
git worktree list
git branch --list codex/saetila-post-integration
git log -1 --oneline origin/integration/codex-independent-qa-2026-10-01
# Endast om grenen/worktreen inte redan finns:
git worktree add -b codex/saetila-post-integration C:\Git\satila-integration origin/integration/codex-independent-qa-2026-10-01
cd C:\Git\satila-integration
git status --short
~~~

Denna rapport är auktoritativ när äldre rot-BUILD_STATE.json eller historiska CODEX_PARITY_AUDIT.md pekar på äldre kodcheckpoints. Eventuella efterföljande rapport-/AGENTS-commits är dokumentation och ändrar inte den 4/4-verifierade sajtkoden. Efter varje ny Codex-kodcommit: ny full 4/4 CI och exakt-SHA ZIP före merge/publicering.