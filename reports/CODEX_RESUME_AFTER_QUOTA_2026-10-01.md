# Sätila Splits – säker återstart för Codex efter kvotpausen

**Datum:** 2026-10-01. **Verifierad integrations-HEAD:** `3b3755af6b880c1d1ce43a05c6263e0baf39f151`.
**Gransknings-PR:** https://github.com/Stayinhealthyrunning/satila-splits/pull/7
**Faktiskt grön CI på exakt samma SHA:** https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36862369057

## Läget som INTE ska förloras

- Den ursprungliga lokala Codex-grenen `codex/saetila-complete-first-draft` är säkrad på GitHub med `a71a5ef161abab7ec0a6a1f53e9b7621c8391fe3`. Användarens senaste `git status --short` visade endast den ospårade mappen `reports/qa-local/`, som ska bevaras lokalt som visuellt bevismaterial.
- En **fristående integrationsgren** `integration/codex-independent-qa-2026-10-01` bygger på Codex commit `a71a5ef`, för in hela den separata auditgrenen som andra merge-parent, och innehåller därefter releasekorrigeringar. Den är öppnad som **Draft PR #7 mot Codex-grenen**.
- Ingen merge till `main`, ingen publicering på Loppanalys.se, ingen ändring av privata raw source-arkiv.

## Grönt releasebevis som redan finns

Workflow `Codex + independent QA integration`, run **36862369057** på `3b3755af...`: ALLA fyra jobb **success**:

| Jobb | Resultat |
|---|---|
| source-and-method | PASS |
| browser-core | PASS |
| release-gates | PASS |
| review-package | PASS |

Det verifierar alla 27 historiska editioner, statistiska spärrar och källproveniens, map/elevation/H2H-synk i Chromium, återställningsbar URL-historik, tangentbords-/mobilinteraktioner, korrekt hantering av tveksamma segmentkilometer, och statisk ZIP-paketering utan rådata. Grön maskinell regression är fortfarande inte liktydig med slutligt visuellt godkännande av ägaren.

## Redan åtgärdat i PR #7 – gör INTE om

1. Missvisande Hero/footer `Samma stigar` borttaget; Hero nu `Tre distanser. Nio resultatår. Djupare insikter.`.
2. Gotaleden-referensläcka i H2H-rubriken borttagen.
3. Timingaxel och GPX-displaydistans åtskiljs explicit i metodtext.
4. Val av år/familj får navigerbar webbläsarhistorik: pushState vid användarval, restaurering på Back/Forward och hashchange utan extra historikloop.
5. Mobilmeny: Escape stänger och `aria-expanded` återställs; sökförslag och dialoger håller tangentbordsfokus.
6. Saknad race-JSON ger synligt felstate i stället för enbart konsolfel.
7. 2023/2024 43 km Torrås→Almered: verkliga TIME och n behålls, men fysisk min/km döljs som `Distans ej verifierad` eftersom timing-km-anomali saknar fysisk validering; samma skydd gäller personprofil.
8. Release-webbläsartester, dataintegritetstester och ZIP-allowlist är integrerade och gröna.

## Säkert sätt för Codex att återuppta arbetet

**Viktigt:** Checkouta inte integrationsgrenen direkt ovanpå en arbetskatalog med ospårade `reports/qa-local/` eller ocommittade framtida ändringar. Behåll `C:\Git\satila-splits` intakt. Använd hellre en separat worktree för integrationen:

```powershell
cd C:\Git\satila-splits
git status --short
git fetch origin
git worktree add -b codex/saetila-post-integration C:\Git\satila-integration origin/integration/codex-independent-qa-2026-10-01
cd C:\Git\satila-integration
git status --short
git log -1 --oneline
```

Om `codex/saetila-post-integration` redan finns, kontrollera `git branch --list` och `git worktree list` innan annat görs; skapa inte om/force-reset en befintlig branch. Efter verifieringen fortsätt etappvis på denna nya worktree. Lämna `integration/codex-independent-qa-2026-10-01` som fryst baslinje tills nya ändringar är testade.

**Nästa uppgifter till Codex:** gå igenom `reports/CODEX_PARITY_AUDIT.md` och `reports/COMPONENT_READINESS_MATRIX.json`, slutför återstående *verkliga* blueprintluckor, gör manuell visuell jämförelse på 1440/900/768/390 px mot godkänd designreferens och Hero, granska tabellernas mobilpresentation samt skapa nytt granskningspaket. Den oberoende regressionssviten ligger nu på samma kodbas; använd `python tools/run_release_candidate_checks.py --all` efter varje avgränsad komponentgrupp, alternativt GitHub Actions `Codex + independent QA integration` på relevanta commits.

**Publicera eller mergea inte automatiskt.** Projektägaren ska först granska sidan och godkänna slutresultatet. Banversioner med bristande källevidens får fortfarande inte fabriceras (särskilt historiska GPX).
