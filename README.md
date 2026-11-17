# WBA junior grading

Public site: wba-grading.pages.dev (the `index.html` in this folder).

## How it updates

`.github/workflows/update.yml` runs three times a day (10:30pm, midnight and 7am Melbourne time, AEDT) and whenever `build/` changes:

1. `build/playhq_pull.py` reads WBA's fixtures and results from the PlayHQ public API and writes them in the same layout as PlayHQ's fixture export.
2. `build/s2gen.py` turns them into `build/s2.json` (divisions, results, next round).
3. `build/build.py` puts the data into `build/template.html` and writes `index.html`.
4. If anything changed it is committed and, when the Cloudflare secrets are set, deployed to Cloudflare Pages.

Results only show in PlayHQ once a game is finalised, which can take a few hours.

## Secrets (Settings → Secrets and variables → Actions)

| Secret | What |
|---|---|
| `PLAYHQ_API_KEY` | WBA's PlayHQ public API key (x-api-key) |
| `PLAYHQ_ORG_ID` | WBA's PlayHQ organisation ID |
| `PLAYHQ_TENANT` | optional; worked out automatically if left out |
| `PLAYHQ_SEASON_ID` | optional; otherwise every ACTIVE season is used |
| `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | optional; to publish to Cloudflare Pages project `wba-grading` |

## Manual fallback

Drop a PlayHQ fixture export into `build/fx.csv` and run:

```
cd build && python3 s2gen.py fx.csv s2.json s2_overrides.json s2_results_extra.json && python3 build.py
```

Grading decisions, review text and draw changes live in `build/template.html`, `build/s2_overrides.json` and `build/s2_results_extra.json`. No player names or internal floor lists go in this repository (it is public).
