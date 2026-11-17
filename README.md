# CDSpec · Queens Community District 3 (CD 403)

Shared data and scripts for our StoryMap **"Streets, Spaces & Shared Tables"**: urban systems and everyday life in Jackson Heights, East Elmhurst and North Corona.

## Folder structure

```
part1_jackson_heights/   Part 1 (hard system, original Jackson Heights scope): code, NYC Open Data extracts, map layers
part2_soft_systems/      Part 2 (soft system, whole CD 403): restaurants, walk times, cuisines, PLUTO, census, charts
  analysis_outputs/      GeoJSON/CSV layers used in the StoryMap
  code/                  scripts 01-07 (see documentation/RUN.md)
  raw_data/              census_2020.xlsx (DCP), PLUTO 26v2 extract
  documentation/         data sources, status, map settings, methods
part3_synthesis/         Part 3 (hard + soft): new CD 403 scope
  data/boundaries/       boroughs, community districts, 2020 NTAs (GeoJSON, EPSG:4326)
  data/census/           2020 Census race/ethnicity (P2) for the 103 block groups in CD 403, plus a 400 m grid
  data/restaurants/      DOHMH records for community board 403 (raw + deduplicated by CAMIS, 17 Nov 2026)
  scripts/               census prep, population-restaurant correlation, locator map
  outputs/               locator map and correlation results
```

Note: Part 1 used the Jackson Heights NTA only. For the final StoryMap the hard system is redone for all of CD 403 (Jackson Heights, East Elmhurst, North Corona).

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
