# NYC incident data source

**Checked:** October 15, 2026
**Runtime source:** NYC Open Data, **Motor Vehicle Collisions - Crashes**
**Dataset identifier:** `h9gi-nx95`

## Verified access

- Dataset page: <https://data.cityofnewyork.us/d/h9gi-nx95>
- Socrata JSON endpoint: <https://data.cityofnewyork.us/resource/h9gi-nx95.json>
- API access is available without an app token for basic queries. Set
  `NYC_OPEN_DATA_APP_TOKEN` in `.env` to send an optional Socrata app token.
- A live endpoint request returned records with fields including `collision_id`,
  `crash_date`, `crash_time`, `borough`, street names, latitude/longitude,
  injury/fatality counts, contributing factors, and vehicle types.
- The newest non-null-borough record returned during the check was dated
  **June 11, 2026**. The dataset was therefore over four months behind the
  current date at verification time.

This is real, official crash-report data, but it is **not a real-time traffic
incident feed**. It describes collisions reported to NYPD, not all roadway
disruptions or present road conditions. Do not infer that a road is currently
closed, congested, or clear from these records.

## API mapping used by the adapter

| Contract field | NYC Open Data field / transformation |
|---|---|
| `id` | `collision_id` |
| `location` | Available on/cross/off street names; coordinates if no street name is provided; otherwise explicitly “Location not reported” |
| `type` | Constant label “Motor vehicle collision” |
| `reported_status` | `number_of_persons_injured` and `number_of_persons_killed`, preserving missing values as “not reported” |
| `reported_at` | `crash_date` + `crash_time`, interpreted in `America/New_York` |
| `source` | NYC Open Data dataset name |
| `source_url` | JSON resource URL filtered by `collision_id` |
| Borough | Exact `borough` filter, normalized to the dataset's uppercase values |

The adapter requests at most 50 newest records by crash date/time. The dataset's
publication can lag, so `data_freshness` reports the newest event timestamp in
the returned records and explicitly warns that it is not real-time. `no_results`
only means the query returned no rows; it is not a claim that the borough had no
crashes.

Network errors, non-success HTTP responses, invalid JSON, and unusable record
fields produce `data_unavailable`. The runtime never falls back to demo fixtures.

## 511NY

511NY remains unverified and is not used by the application. Its public
developer-resources page did not expose a documented endpoint or schema during
the earlier check. Do not describe this app as using 511NY or current live
traffic conditions.
