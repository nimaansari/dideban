# OSINT & Journalist Skills

## Core OSINT Principles
- **Verify before publish**: Always cross-reference minimum 2 independent sources
- **Label unverified**: Any single-source claim → mark as "تأییدنشده"  
- **Source hierarchy**: Official statements > verified journalists > OSINT accounts > citizen reports
- **Geolocation**: Cross-reference coordinates with satellite imagery (Google Maps, Wikimapia, Sentinel Hub)
- **Timestamp verification**: Check metadata, sun position, shadows for video/image authenticity

## OSINT Tools & Sources
- **Warstrikes.com** `/api/events` — live global strike tracker with lat/lon
- **MahsaAlert.com** `/api/v1/layers` + geojson — Iran conflict layers
- **Sentinel Hub** — satellite imagery for damage assessment
- **SunCalc** — verify timestamps via sun position in images
- **FlightAware/Flightradar24** — track military aircraft movements
- **MarineTraffic** — track naval vessels
- **Bellingcat techniques** — open source verification methods

## Journalist Best Practices
- **Neutral language**: Avoid politically loaded terms (e.g. "سرزمین‌های اشغالی" → "اسرائیل")
- **Attribution**: Always name the source (who said what)
- **Context**: Provide background — why this matters, historical context
- **Official statements format**:
  🎙️ [Name / Title / Organization]
  ❓ [Reporter question if applicable]
  💬 [Official answer/statement]
- **Breaking news**: Lead with facts, not speculation. Update as confirmed.
- **Casualties**: Only report confirmed numbers, note "preliminary" when applicable

## News Credibility Tiers
1. **Tier 1 (Most reliable)**: Official military/government statements, major wire services (Reuters, AP)
2. **Tier 2**: Established journalists with track record, verified OSINT accounts
3. **Tier 3**: Telegram channels with history of accuracy
4. **Tier 4 (Label as تأییدنشده)**: Anonymous, citizen reports, single-source claims

## Red Flags for Misinformation
- No timestamp or verifiable location
- Recycled footage from different conflict/time
- Emotional language designed to provoke reaction
- Exaggerated casualty numbers without sources
- Anonymous "informed sources" as sole basis

## Data Sources for Dashboard
- Telegram channels: SaberinFa, ManotoTV, overlordechokilo, tehran_timse, defender_iran, etc.
- X List: @Dideban1995/Iran War News (ID: 2028404706926813366)
- Warstrikes API: https://warstrikes.com/api/events (fields: id, title, summary, origin_lat/lng, impact_lat/lng)
- INSS Lion's Roar ArcGIS layers:
  - Iranian attacks 2026: https://services-eu1.arcgis.com/cOhMqNf3ihcdtO7J/arcgis/rest/services/IranianAttack2026/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson
  - IDF/US strikes 2026: https://services-eu1.arcgis.com/cOhMqNf3ihcdtO7J/arcgis/rest/services/IDF_US_Strikes_2026/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson
  - US bases Middle East: https://services-eu1.arcgis.com/cOhMqNf3ihcdtO7J/arcgis/rest/services/US_bases_in_the_Middle_East/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson
  - Fields: Date, TargeteSite, Location, Notes
- MahsaAlert API: https://api.mahsaalert.app/api/v1/layers
