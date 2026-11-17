# Additional data for the Part 3 model (hard + soft = ?)

These files were added next to the existing `boundaries/`, `census/` and `restaurants/` folders. They are the inputs and intermediate tables behind the segment-level model of where restaurants are and what they serve. Files that were already in the repository (CD 403 boundary, NTAs, block-group census, DOHMH records for community board 403, walk times, walkable streets, walksheds, schools) were **not** copied again.

Everything here is public data. Downloaded 3 November 2026 unless noted (queries below).

## Raw inputs

| File | Source | Query / filter | Used for |
|---|---|---|---|
| `street_network/cscl_street_centerline_box.geojson.gz` | NYC Street Centerline (CSCL), NYC Open Data `inkn-q76z` | `within_box(the_geom, 40.800, -73.920, 40.730, -73.825)` | street graph, betweenness centrality, street width, walking distance to the subway. Gzipped; read with `gzip.open` or `gdal /vsigzip/` |
| `transit/subway_entrances_mta_raw.json` | MTA Subway Entrances and Exits, data.ny.gov `i9wp-a4ja` | whole dataset | the 56 entrances used for walking minutes (`entry_allowed = YES`, within 1,200 m of CD 403) |
| `restaurants/dohmh_queens_raw_2026-11-03.json.gz` | DOHMH NYC Restaurant Inspection Results, NYC Open Data `43nn-pn8j` | `boro = 'Queens'`; 74,053 rows (one per violation); latest record date 30 Oct 2026. Gzipped | the exact snapshot behind the 502 restaurants. Latest row per CAMIS, then `community_board = 403` (510), then drop 8 re-registered permits at the same coordinate (502). The existing `part3_synthesis/data/restaurants/` files come from a later download (17 Nov), so counts can differ slightly |
| `land_use/pluto_cd403_model_input.json` | NYC PLUTO (DCP), NYC Open Data | tax lots of CD 403 (14,686), fields `bbl, retailarea, comarea, officearea, bldgarea, lotarea, landuse, zonedist1, numfloors, yearbuilt, latitude, longitude` (+ `overlay1` where present) | land-use group: retail + commercial floor area and commercial-zoned lots within 40 m of each street segment. Overlaps the Part 2 PLUTO extract by lot, but has different fields |
| `land_use/pluto_cd403_housing50.json` | PLUTO `64uk-42ks` | `cd = '403' and unitsres >= 50` | map of housing with 50+ units |
| `public_space/parks_box.geojson` | NYC Parks Properties `enfh-gkve` | `within_box` around CD 403 | public space map |
| `public_space/plazas_box.geojson` | NYC DOT Pedestrian Plazas `k5k6-6jex` | `within_box` | public space map |
| `public_space/open_streets_box.geojson` | NYC DOT Open Streets `uiay-nctu` | `within_box` | public space map |
| `facilities/facdb_cd403.json` | NYC Facilities Database (DCP) `ji82-xba5` | `cd = '403'` | schools and facilities context |
| `census/acs_tract_race_ethnicity_B03002.json` | ACS 5-year estimates, table B03002 (Hispanic or Latino origin by race), census tracts of CD 403; fetched through the Esri Living Atlas ACS layer (the Census API needs a key) | 154 tract rows: total, White, Black, Asian, Hispanic | residents group: % Hispanic, % Asian, diversity index (5-group Shannon entropy / ln 5). Tract values are inherited by the block groups inside each tract |
| `census/acs_explored_not_used/` | ACS B05002 (foreign born) and B19049 (median household income), same tracts | tried as extra resident variables; they changed nothing, so they are **not** in the final model | for reference only |

## Derived tables

| File | What it is |
|---|---|
| `derived/segments_v2.csv`, `segments_v2.geojson` | the model table: 1,549 street segments of CD 403. `len` metres, `n` restaurants snapped to the nearest segment, and the five predictor groups. **Predictors are z-scores** (mean 0, sd 1): subway `walk_min`; streets `betw_l` (log1p betweenness), `width`; land use `log_retail`, `zoned_share`; residents `log_popden`, `pct_hisp`, `pct_asian`, `diversity`; food cluster `log_cluster` (restaurants within 200 m on other segments). `GEOID` is the block group of the segment midpoint (used as the cross-validation group) |
| `derived/emergence_units.csv`, `.geojson`, `emergence_units_v2check.csv`, `emergence_partition.csv` | first trial with block groups as units (103 block groups, adjusted R² partition). Superseded by the segment model, kept for comparison |
| `derived/parks_plazas_cd403.geojson`, `open_street_34ave.geojson`, `housing_50plus_units.geojson` | clipped and cleaned layers for the Part 2 context maps |

## How the model uses them

- Unit: street segment. Target: restaurants per segment, Poisson model with segment length as exposure.
- Five predictor groups: hard = subway, streets, land use; soft = residents, food cluster. Out-of-sample deviance explained (5-fold cross-validation, folds = whole block groups, 10 repeats), split over the groups with Shapley values.
- Result for "where and how many": hard 55%, soft 10%, other 36%. For "what is served" (cuisine group of each restaurant): hard about 0%, soft 19%, other 82%. These percentages describe explained variation, not causes.
- Segment `n` counts restaurants on the nearest segment, so neighbouring segments can trade restaurants.
