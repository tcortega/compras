from __future__ import annotations

import polars as pl

from compras_detect.tier1.cnae_mismatch import detect_cnae_mismatch
from compras_detect.tier1.cnpj_age import detect_cnpj_age
from compras_detect.tier1.fracionamento import KIND_CLUSTER as KIND_FRAC_CLUSTER
from compras_detect.tier1.fracionamento import KIND_OVER as KIND_FRAC
from compras_detect.tier1.fracionamento import detect_fracionamento
from compras_detect.tier1.mismatch import detect_qty_price_mismatch
from compras_detect.tier1.retroactive_edit import detect_retroactive_edits
from compras_detect.tier1.sanctioned import detect_sanctioned

KIND_QTY = "qty_unit_price_neq_total"
KIND_AGE = "cnpj_age"
KIND_AGE_INFO = "cnpj_age_info"
KIND_CNAE = "cnae_mismatch"
KIND_SANCTION = "sanctioned_ceis_cnep"
KIND_EDIT = "retroactive_edit"


def run_tier1(
    items: pl.DataFrame,
    *,
    landing_records: pl.DataFrame | None = None,
    sanctions: pl.DataFrame | None = None,
) -> pl.DataFrame:
    frames = [
        detect_qty_price_mismatch(items),
        detect_fracionamento(items),
        detect_cnpj_age(items),
        detect_cnae_mismatch(items),
        detect_sanctioned(items, sanctions),
        detect_retroactive_edits(landing_records),
    ]
    present = [f for f in frames if f is not None and not f.is_empty()]
    if not present:
        return pl.DataFrame(
            schema={
                "record_id": pl.String,
                "pncp_id": pl.String,
                "kind": pl.String,
                "delta": pl.String,
                "source_url": pl.String,
                "snapshot_id": pl.String,
                "methodology_version": pl.String,
            }
        )
    return pl.concat(present, how="vertical")
