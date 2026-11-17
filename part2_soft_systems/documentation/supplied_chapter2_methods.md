# How far is the table from the train? Method notes for Queens Community District 3 (BoroCD 403)

Re-run on 3 November 2026 (duplicate-permit cleaning added the same evening) for the whole community district (Jackson Heights, East Elmhurst, North Corona).
Everything below was produced by `scripts/01_download.py` (data) and `scripts/02_walktime.py` (analysis); outputs are in `out/`.

## The question

For every restaurant in CD 3, how far is it, on foot along the street network, to the nearest subway entrance?

## The five steps

1. **Restaurant points.** NYC DOHMH Restaurant Inspection Results (dataset 43nn-pn8j), Queens rows, downloaded 3 Nov 2026 (latest record date 30 Oct 2026). The dataset has one row per violation, so each restaurant (CAMIS id) appears many times; we keep the latest inspection row per CAMIS. The point is DOHMH's own latitude/longitude. District membership uses DOHMH's `community_board = 403` field. Cross-check: all 430 points inside the DCP district polygon carry 403, and the only 403 points outside it are 80 Roosevelt Avenue addresses geocoded less than 1 m south of the boundary line, because the polygon follows the avenue's centerline. That gives 510 records. Eight of them are the same storefront registered twice under a new permit (a new owner or company name gets a new CAMIS id; all eight extra rows are not-yet-inspected placeholders dated 1900-01-01): CIELO / CIELO NYC, COCO FRESH TEA & JUICE / COCO TEA, KABABISH / KABABISH OF NY INC, PREMIUM SWEETS, WONDER, MANCOA, PARADISE SPORTS BAR, GREAT WALL. Records at the same coordinate whose names share the same first meaningful word are treated as one business and the latest row is kept (`out/removed_duplicate_permits.csv`). Result: **502 restaurants**. Different businesses in one building (for example Chipotle, Denny's and Dunkin at 87-10 Northern Boulevard) are kept as separate records; 26 addresses hold two or three.
2. **Sub-areas.** 2020 Neighborhood Tabulation Areas (dataset 9nt8-h7nd): QN0301 Jackson Heights, QN0302 East Elmhurst, QN0303 North Corona. Points on the NTA boundary line (16, all on Roosevelt Avenue) take the nearest NTA.
3. **Origins.** MTA Subway Entrances and Exits (data.ny.gov i9wp-a4ja), entrances with `entry_allowed = YES`, within 1.2 km of the district so that stations just outside (e.g. 111 St, Mets-Willets Point, 65 St) still count. **56 entrances, 14 stations.**
4. **Walking network.** NYC Street Centerline (dataset inkn-q76z) inside a box around the district. Kept: streets, bridges, tunnels, boardwalks, paths, step streets and alleys (`rw_type` 1, 3, 4, 5, 6, 7, 10) that are not vehicle-only (`nonped` != V) and are built (`status` = 2). Dropped: highways, ramps, driveways, ferry routes. Segments are joined into a graph where their endpoints share the same coordinates and the same level code, so a street passing under a bridge is not joined to the bridge. 7,910 walkable segments, 6,330 nodes.
5. **Distance and bins.** Each entrance and each restaurant is attached to its nearest walkable segment by a straight connector (median 0.9 m for restaurants). Shortest path from the restaurant to the nearest entrance is computed with Dijkstra's algorithm (networkx, multi-source from all entrances). Walking speed 80 m/min, so 5 minutes = 400 m and 10 minutes = 800 m. Bins: within 5 min (<= 400 m), 5-10 min (400-800 m), beyond 10 min (> 800 m). The walkshed shading on the map is a 35 m band around every piece of street reachable within 400 m or 800 m, trimmed at the exact point where the budget runs out.

Not modelled: crossing delays, station interiors, elevation, sidewalk closures, time of day. One restaurant (a Dunkin' at LaGuardia Terminal C) sits on airport roads that do not connect to the street grid; it is counted as beyond 10 minutes.

## Worked examples (from `out/restaurants_cd403_walktime.csv`)

| Restaurant | Address | Nearest entrance | Street distance | Bin |
|---|---|---|---|---|
| Nepali Bhanchha Ghar | 74-11 Roosevelt Ave | Jackson Hts-Roosevelt Av / 74 St (7 E F M R) | 53 m, 0.7 min | within 5 min |
| Palo Bar | 38-12 104 St | 103 St-Corona Plaza (7) | 221 m, 2.8 min | within 5 min |
| Arepa Lady | 77-17 37 Ave | Jackson Hts-Roosevelt Av / 74 St | 466 m, 5.8 min | 5-10 min |
| Kennedy Fried Chicken | 102-20 37 Ave | 103 St-Corona Plaza (7) | 489 m, 6.1 min | 5-10 min |
| Mojitos | 81-01 Northern Blvd | 82 St-Jackson Hts (7) | 941 m, 11.8 min | beyond 10 min |
| Sabor de Mi Tierra | 101-11 Northern Blvd | 103 St-Corona Plaza (7) | 1,060 m, 13.2 min | beyond 10 min |

Reading Mojitos by hand: from 81st St and Northern Blvd walk south on 82nd St past 34th Ave, 35th Ave, 37th Ave and 37th Rd to the station stairs at Roosevelt Ave; those blocks add up to about 940 m, which is 11.8 minutes at 80 m/min.

## Results

By sub-area (`out/summary_by_subarea.csv`):

| Sub-area | n | within 5 min | 5-10 min | beyond 10 min | median walk |
|---|---|---|---|---|---|
| Jackson Heights (QN0301) | 333 | 169 (51%) | 58 (17%) | 106 (32%) | 4.9 min |
| North Corona (QN0303) | 115 | 66 (57%) | 27 (23%) | 22 (19%) | 4.6 min |
| East Elmhurst (QN0302) | 54 | 0 (0%) | 0 (0%) | 54 (100%) | 20.5 min |
| **All CD 3** | **502** | **235 (47%)** | **85 (17%)** | **182 (36%)** | 5.4 min |

By corridor, whole district, using the street in the recorded address (`out/summary_by_corridor.csv`):

| Corridor | n | within 5 min | 5-10 min | beyond 10 min |
|---|---|---|---|---|
| Roosevelt Avenue | 80 | 80 (100%) | 0 | 0 |
| 37th Avenue | 112 | 67 (60%) | 45 (40%) | 0 |
| Junction Boulevard | 32 | 14 (44%) | 11 (34%) | 7 (22%) |
| Northern Boulevard | 112 | 0 | 4 (4%) | 108 (96%) |
| Astoria Boulevard | 19 | 0 | 0 | 19 (100%) |
| Other streets | 147 | 74 (50%) | 25 (17%) | 48 (33%) |

What changed by widening the study area: the Jackson Heights story (Roosevelt and 37th Avenue inside the walkshed, Northern Boulevard outside it) holds district-wide, and East Elmhurst adds a third case: 54 restaurants, none within ten minutes of any subway entrance, served instead by Astoria Boulevard and Northern Boulevard bus corridors. North Corona is the most transit-adjacent sub-area because the 7 train runs along its southern edge.

## Check against the earlier Jackson Heights-only run

The earlier story reported 329 Jackson Heights records: 163 within 5 min, 58 in 5-10 min, 108 beyond. This run gives 333: 169 / 58 / 106. The 5-10 count is identical and the other two move by a handful: the newer DOHMH snapshot (30 Oct vs 21 Oct), Roosevelt Avenue boundary-line points now assigned to the nearest NTA, and the removal of five duplicate permits inside Jackson Heights. The method reproduces the earlier result.

## Files for the StoryMap (all WGS84 GeoJSON, upload to ArcGIS Online as layers)

- `out/cd403_boundary.geojson` study area (DCP Community Districts, BoroCD 403)
- `out/nta_qn03.geojson` the three sub-areas
- `out/subway_entrances_used.geojson` 56 entry-allowed entrances
- `out/walkshed_5_10min_clipped_cd403.geojson` 5- and 10-minute street reach (35 m band), clipped to the district; `walkshed_5_10min.geojson` unclipped
- `out/restaurants_cd403_walktime.geojson` / `.csv` one row per restaurant with sub-area, corridor, nearest station, metres, minutes, bin
- `out/walkable_streets.geojson` the network actually used

## Sources

- DOHMH New York City Restaurant Inspection Results: https://data.cityofnewyork.us/d/43nn-pn8j
- MTA Subway Entrances and Exits: https://data.ny.gov/d/i9wp-a4ja
- NYC Street Centerline (CSCL): https://data.cityofnewyork.us/d/inkn-q76z
- DCP Community Districts (NYC Planning ArcGIS feature service, NYC_Community_Districts)
- DCP 2020 Neighborhood Tabulation Areas: https://data.cityofnewyork.us/d/9nt8-h7nd
- Raw downloads kept in `G:\oss-work\cd403-data\raw` (3 Nov 2026).
