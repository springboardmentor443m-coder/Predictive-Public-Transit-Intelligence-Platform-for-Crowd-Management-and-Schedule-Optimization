# Changelog

All notable changes to MetroFlow. Commits are grouped by work stream; the branch
`KOKKIRIGADDA-MANOJ-BABU` is the active deliverable per `guidelines.md`.

## Engineering Hardening & Feature Work (post Milestone 4)

### Frontend — full TypeScript conversion
- Converted every page, component, and library file from `.js/.jsx` to typed `.ts/.tsx`.
- Pinned type packages (`@types/node`, `@types/react`, `@types/react-dom`, `typescript`).
- Added `*.tsbuildinfo` to `.gitignore`; extended `tailwind.config.js` content globs to
  `ts/tsx` so Tailwind styling covers the converted files.
- `tsc --noEmit` and `npm run build` are green.

### Backend reliability fixes
- **Public health endpoint**: added `GET /api/v1/health` (unauthenticated) and switched the
  login page health check to it. Previously the login page probed the auth-protected
  `/analytics/overview`, which returned `401` and produced a false **"Backend Offline"** even
  when the backend was healthy.
- **Chart resilience**: analytics and crowd-history charts now have explicit loading/empty
  ("No data for this window") states so a silent 401/dry window never renders a blank graph.
- **Traffic curve fix**: `seed_db.py` previously created exactly one schedule row per train per
  hour, yielding a flat "Network Traffic Trend" line. Schedule generation now spaces arrivals by
  real headways (4-min peak ≈ 15 tph, 8-min off-peak ≈ 7 tph), producing a recognizable
  morning/evening rush-hour curve with correct volume baselines (~69.3k baseline, ~148.5k peaks).

### Advanced ML model — quantile confidence intervals
- Added `scripts/train_quantile_crowd.py` (3 × GradientBoostingRegressor, quantile loss α =
  0.05/0.50/0.95); artifact `models_store/hangzhou_crowd_quantile_model.joblib` (MAE 0.028, R² 0.98).
- `CrowdModel` now prefers the quantile artifact and returns **native lower/upper intervals** per
  forecast point; legacy artifacts fall back to a symmetric `residual_std` band. API shape unchanged.
- See `docs/ML_MODELS.md`.

### Real-world dataset importers
- New `scripts/importers/` package (`mta`, `seoul`, `tfl` + shared `base` + `cli`).
- Each importer parses the genuine agency format (MTA cumulative turnstile counters, Seoul
  Korean/English card-swipe CSVs — hourly or daily, TfL annual entry/exit), re-anchors to now,
  and writes the seed-ready `ridership_hourly.csv` + `stations.csv`.
- `seed_db.py` gained a fleet fallback so imported station lines without a matching `TR-*` train
  still populate the timetable and live train map.
- Verified end-to-end: MTA sample → `seed_db.py --refresh` → 20,736 schedules + 284 ridership rows.
- See `docs/IMPORTERS.md`.

### Python hygiene
- New `app/core/time.py`; all 40 `datetime.utcnow()` call sites (app, scripts, tests) replaced with
  the timezone-safe `utcnow()` helper (`datetime.now(timezone.utc).replace(tzinfo=None)`, identical
  value — zero behavioral change).
- Modernized type hints in `schemas/analytics.py` (`Optional[...]` → `X | None`), dropped unused
  `typing` imports, and removed a legacy `__import__("datetime")` workaround.
- The `# noqa` intel on testing: full suite still passes 59/59.

## Documentation & Data Guide
- `README.md` overhauled (importers, ML intervals, health check, TypeScript, layouts).
- `docs/IMPORTERS.md` — real-world ingestion guide (formats, aliases, end-to-end verification).
- `docs/ML_MODELS.md` — model store, quantile ensemble, intervals, fallbacks, retraining.
- `Datasets.md` — added importer-to-format mapping section.
- `docs/PROJECT_PLAN.md` / `docs/PERFORMANCE_METRICS.md` / `docs/MILESTONE_4.md` — updated for the
  new surface area and metrics.

## Earlier (pre-branch) work snapshot
Real-time train monitoring, date-aware forecasting & per-train predictions, Ctrl+K palette &
historical date tracking, station health radar reacting to selected date/window, Kaggle training
notebooks (Seoul/Hangzhou/NJ/NYC/TfL/Beijing/Railway), Docker/K8s/CI hardening, graceful
degradation, and the baseline Milestone 1–4 roadmap (see `git log`).