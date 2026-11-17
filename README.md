# CDSpec · Queens Community District 3 (CD 403)

Shared data and scripts for our StoryMap **"Streets, Spaces & Shared Tables"**: urban systems and everyday life in Jackson Heights, East Elmhurst and North Corona.

## Folder structure

```
data/
  boundaries/    boroughs, community districts, 2020 NTAs (GeoJSON, EPSG:4326)
  census/        2020 Census race/ethnicity (P2) for the 103 block groups in CD 403, plus a 400 m grid
  restaurants/   DOHMH restaurant inspection records for community board 403 (raw + deduplicated by CAMIS)
softsystem/      data from our earlier Part 1/Part 2 work
scripts/         Python scripts (run in order, from a folder containing the raw downloads)
outputs/         locator map and population-restaurant correlation results
```

## Key fields (census block groups)

| field | meaning |
|---|---|
| `pop` | total population (P2_001) |
| `hisp`, `white`, `black`, `asian` | Hispanic or Latino; White, Black and Asian alone, non-Hispanic |
| `p_*` | the shares of the above |
| `dens` | residents per hectare |
| `n`, `n_per_ha` | restaurants (assigned to nearest block group), per hectare |

## Sources

- U.S. Census Bureau, 2020 Redistricting Data (PL 94-171), New York; TIGER/Line 2020 block groups
- NYC DOHMH Restaurant Inspection Results: https://data.cityofnewyork.us/d/43nn-pn8j (downloaded 17 Nov 2026)
- NYC DCP boundaries via NYC Open Data: community districts (5crt-au7u), 2020 NTAs (9nt8-h7nd), boroughs (gthc-hcne)

## Requirements

`pip install geopandas matplotlib scipy`
