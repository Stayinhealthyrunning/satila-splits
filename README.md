# Sätila Splits

Analysverktyg för Sätila Trail Run med historiska resultat, mellantider och banversioner för 22 km, 43 km och 85 km.

## Mål

Sätila Splits ska bygga vidare på principerna från Ultravasan, Gotaleden och Österlen Spring Trail:

- officiella resultat ska bevaras som rådata före normalisering
- banor ska versionshanteras per år och distans
- samma geografiska kontrollpunkt ska kunna jämföras mellan år även när banans kilometertal ändras
- GPX-källor ska ha tydlig proveniens och confidence
- officiella GPX, homologerade ITRA/Trace de Trail-spår och verifierade deltagarspår ska hållas isär
- inga mellantider, bansträckningar eller statusar får fabriceras

## Primärt scope

- 85 km / historiskt 80–82 km ultra
- 43 km / historiskt cirka 42 km
- 22 km / historiskt cirka 21 km
- första arbetsfönster: 2021–2026
- historisk utvidgning: tillbaka mot premiäråret 2016 där källorna medger det

## Datakällor

Primära och kompletterande källor inventeras i `research/SOURCE_INVENTORY.md`.

Arbetshypotesen är:

1. EQ Timing för officiella resultat och eventuella officiella splits.
2. Sätila Trails egna tävlings-PM och GPX-filer för banversioner och kontrollpunkter.
3. ITRA / Trace de Trail för homologerade 43/85-km-banor.
4. Tulospalvelu / GPS-seuranta för faktiska tävlingsspår på ultran när sådana finns.
5. Verifierade deltagar-GPX från Suunto, Strava, Garmin, Jogg m.fl. som kompletterande geometri.

## Repository structure

```text
config/      maskinläsbara event-, course- och source-konfigurationer
data/        rådata och dokumentation för härledda dataset
docs/        datamodell, metodik och tekniska beslut
research/    källinventering och verifieringsanteckningar
tests/       validering
tools/       import-, kontroll- och byggverktyg
```

Frontend och Engine-integration läggs till först när datagrunden är verifierad.
