# Google Places data for the CD 403 restaurants

Source of ratings, review counts, price ranges, place types and place IDs: **Google Places API** (Text Search, New), fetched 23 November 2026. These values are Google content and are subject to the Google Maps Platform Terms of Service, which limit storing and redistributing it (place IDs may be stored). Use them only for this course project, keep the attribution, and do not reuse or republish them elsewhere. The values change over time; this is one snapshot.

## Files

| file | content |
|---|---|
| `google_places.csv` | one row per DOHMH restaurant (502). `match_ok = True` for 472 rows (465 different Google places) |
| `place_ids.csv` | `camis`, `place_id`, `match_ok`, `match_dist_m` only |
| `three_streets_table.csv` | Roosevelt Avenue, 37th Avenue and Northern Boulevard compared (one row per Google place) |
| `viaduct_bands.csv` | rating, price and Latin American share by distance from Roosevelt Avenue |
| `google_places_by_corridor.csv`, `google_places_by_group.csv`, `google_places_by_corridor_group.csv` | summaries by street and by cuisine group |
| `google_places_tests.csv` | permutation tests, under the elevated 7 train against away from it |

The tables use two samples: the `three_streets` and `viaduct` tables use every matched place; the `google_places_*` summaries and tests use a stricter sample (open places whose Google name agrees with the DOHMH name).

## Columns of `google_places.csv`

| column | meaning |
|---|---|
| `camis` | DOHMH restaurant ID (join key to our restaurant files) |
| `dba` | restaurant name in the DOHMH record |
| `place_id`, `google_name` | Google place ID and name |
| `rating`, `user_rating_count` | average Google rating (out of 5) and number of ratings |
| `price_level`, `price_min`, `price_max` | Google price level and price range in US dollars per person (empty when Google gives none) |
| `primary_type`, `business_status` | Google place type; open, closed temporarily or closed permanently |
| `match_dist_m` | metres between the DOHMH point and the Google point |
| `match_ok` | accepted match: within 80 m and a similar name or the same street number (a second pass allowed 200 m with a similar name). When False, no Google values are kept |

## Scripts

In `../../scripts/`: `09_google_places_fetch.py`, `10_google_places_analysis.py`, `11_three_streets.py`. Each takes one folder as its first argument. Put these files in it: `google_places.csv` (this folder), `restaurants_cd403_walktime.geojson` (`part2_soft_systems/analysis_outputs/`) and `segments_v2.geojson` (`../derived/`). `10` also compares with a hand-made price lookup (`price_sample_results.csv`) that is not in this repository. Running `09` needs your own API key in the environment variable `GOOGLE_PLACES_API_KEY` and is billed to that key. No key is stored here.
