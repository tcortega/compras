from __future__ import annotations

# After land: refetch 03:00, incremental daily 04:00, PNCP gaps 04:30, monthly 05:00 on the 1st.
SCHEDULE_TZ = "America/Sao_Paulo"
SCHEDULE_NAME = "nightly_detector_daily"
JOB_NAME = "nightly_detector_run"
SCHEDULE_CRON = "0 6 * * *"

# Existing detect assets only. Do not invent a detector here.
ASSET_KEYS = (
    "tier1_flags",
    "cobid_graph",
    "fornecedor_adjacency",
)
