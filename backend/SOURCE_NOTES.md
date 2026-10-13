# 511NY access and field-mapping notes

**Checked:** October 13, 2026  
**Status:** Unverified; the Day 1 API uses fictional fixtures only.

The official URLs checked were [511NY Developer Resources](https://511ny.org/developer-resources) and [511NY API](https://511ny.org/api). Both rendered as the general 511NY traffic and travel information page; the retrieved page content did not expose developer documentation, an API endpoint, or a response schema. No API credentials were used, and no live request or real incident payload was retrieved.

| Contract field | 511NY field mapping | Status |
|---|---|---|
| `id` | Unknown | Unverified |
| `location` | Unknown | Unverified |
| `type` | Unknown | Unverified |
| `reported_status` | Unknown | Unverified |
| `reported_at` | Unknown | Unverified |
| `source` / `source_url` | Unknown | Unverified |
| Borough association | Unknown | Unverified |

API access requirements, authentication, endpoint, rate limits, licensing, borough mapping, and timestamp semantics also remain unverified. Do not map assumed field names or describe fixture records as live data.

**Next:** locate official machine-readable API documentation or a provider contact; request credentials if required; then save a sanitized sample response and complete this mapping before implementing the live-source adapter.
