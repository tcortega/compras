from __future__ import annotations

from decimal import Decimal

import polars as pl

from compras_normalize.catalog import Catalog
from compras_normalize.text import fold, parse_date, parse_decimal, parse_datetime, quarter_of
from compras_normalize.units import UnitTable

_ESFERA = {
    "f": "federal",
    "federal": "federal",
    "1": "federal",
    "e": "estadual",
    "estadual": "estadual",
    "2": "estadual",
    "m": "municipal",
    "municipal": "municipal",
    "3": "municipal",
}


def normalize_frame(
    raw: pl.DataFrame,
    catalog: Catalog,
    units: UnitTable,
    cnpj: pl.DataFrame | None,
    snapshot_id: str,
    methodology_version: str,
) -> pl.DataFrame:
    cnpj_by = _cnpj_index(cnpj)
    rows: list[dict] = []
    for row in raw.iter_rows(named=True):
        rows.append(
            _normalize_row(row, catalog, units, cnpj_by, snapshot_id, methodology_version)
        )
    return pl.DataFrame(rows, infer_schema_length=0)


def _normalize_row(
    row: dict,
    catalog: Catalog,
    units: UnitTable,
    cnpj_by: dict[str, dict],
    snapshot_id: str,
    methodology_version: str,
) -> dict:
    descricao = _first(row, "descricaodetalhada", "descricao_detalhada", "descricaoresumida", "descricao")
    codigo = _first(row, "coditemcatalogo", "codigoitemcatalogo", "coditem")
    tipo = _first(row, "materialouservico")
    hit = catalog.match(descricao, codigo, tipo)
    unit_raw = _first(row, "unidademedida", "nomeunidademedida", "siglaunidademedida") or ""
    unit = units.match(unit_raw)
    qty = parse_decimal(_first(row, "quantidaderesultado", "quantidade")) or Decimal("0")
    unit_price = parse_decimal(
        _first(row, "valorunitarioresultado", "valorunitariohomologado", "valorunitario", "valorunitarioestimado")
    )
    total = parse_decimal(_first(row, "valortotalresultado", "valortotal"))
    if unit_price is not None and unit.to_base_factor != 0:
        price_base = (unit_price / unit.to_base_factor).quantize(Decimal("0.000001"))
    else:
        price_base = None
    publicado = parse_datetime(_first(row, "datapublicacaopncp", "datainclusaopncp"))
    fornecedor_cnpj = _digits(_first(row, "codfornecedor", "nifornecedor", "fornecedor_cnpj"))
    opened_on = None
    cnae = None
    razao_forn = _first(row, "nomefornecedor", "fornecedor_razao")
    if len(fornecedor_cnpj) == 14 and fornecedor_cnpj in cnpj_by:
        info = cnpj_by[fornecedor_cnpj]
        opened_on = info.get("opened_on")
        cnae = info.get("cnae")
        razao_forn = razao_forn or info.get("razao_social")
    esfera = _ESFERA.get(fold(_first(row, "orgaoentidadeesferaid", "esfera")), "municipal")
    return {
        "orgao_cnpj": _digits(_first(row, "orgaoentidadecnpj", "orgao_cnpj")),
        "orgao_razao": _first(row, "orgaoentidaderazaosocial", "orgao_razao") or "",
        "esfera": esfera,
        "poder": fold(_first(row, "orgaoentidadepoderid", "poder")) or "executivo",
        "uf": (_first(row, "unidadeorgaoufsigla", "uf") or "").upper(),
        "municipio_ibge": _first(row, "unidadeorgaocodigoibge", "municipio_ibge") or "",
        "municipio_nome": _first(row, "unidadeorgaomunicipionome", "municipio_nome") or "",
        "fornecedor_cnpj": fornecedor_cnpj if len(fornecedor_cnpj) == 14 else "",
        "fornecedor_razao": razao_forn or "",
        "opened_on": opened_on.isoformat() if opened_on else "",
        "cnae": cnae or "",
        "pncp_id": _first(row, "numerocontrolepncp", "idcontratacaopncp", "pncp_id") or "",
        "modalidade": _first(row, "modalidadenome", "modalidade") or "",
        "modalidade_codigo": _first(row, "codigomodalidade", "modalidade_codigo") or "",
        "objeto": _first(row, "objetocompra", "objeto") or "",
        "ano": _first(row, "anocomprapncp", "ano") or (str(publicado.year) if publicado else ""),
        "valor_homologado": _dec_str(parse_decimal(_first(row, "valortotalhomologado"))),
        "publicado_em": publicado.isoformat() if publicado else "",
        "descricao": descricao or "",
        "catmat": hit.catmat or "",
        "catser": hit.catser or "",
        "catmat_match_quality": hit.quality,
        "quantidade": _dec_str(qty),
        "unidade_medida": unit_raw,
        "unidade_canonica": unit.canonical,
        "unit_parse_confidence": unit.confidence,
        "valor_unitario": _dec_str(unit_price),
        "valor_total": _dec_str(total),
        "valor_unitario_base": _dec_str(price_base),
        "base_unit": unit.base_unit,
        "uf_item": (_first(row, "unidadeorgaoufsigla", "uf") or "").upper(),
        "quarter": quarter_of(publicado) or "",
        "snapshot_id": snapshot_id,
        "methodology_version": methodology_version,
        "source": _first(row, "source") or "compras_gov",
        "record_id": _first(row, "record_id") or "",
        "record_hash": _first(row, "record_hash") or "",
        "material_ou_servico": tipo or "",
        "id_compra": _first(row, "idcompra") or "",
        "id_compra_item": _first(row, "idcompraitem") or "",
    }


def _cnpj_index(cnpj: pl.DataFrame | None) -> dict[str, dict]:
    if cnpj is None or cnpj.is_empty():
        return {}
    out: dict[str, dict] = {}
    for row in cnpj.iter_rows(named=True):
        folded = {fold(k).replace(" ", "_"): v for k, v in row.items()}
        basico = str(folded.get("cnpj_basico") or "")
        ordem = str(folded.get("cnpj_ordem") or "0001").zfill(4)
        dv = str(folded.get("cnpj_dv") or "").zfill(2)
        full = folded.get("cnpj") or (basico + ordem + dv)
        full = _digits(str(full))
        if len(full) != 14:
            continue
        opened = parse_date(folded.get("data_inicio_atividade") or folded.get("opened_on"))
        out[full] = {
            "opened_on": opened,
            "cnae": str(folded.get("cnae_fiscal_principal") or folded.get("cnae") or ""),
            "razao_social": str(folded.get("razao_social") or folded.get("nome_fantasia") or ""),
        }
    return out


def _first(row: dict, *names: str) -> str | None:
    folded = {fold(k).replace(" ", "").replace("_", ""): v for k, v in row.items()}
    for name in names:
        key = fold(name).replace(" ", "").replace("_", "")
        if key in folded and folded[key] not in (None, ""):
            return str(folded[key])
    return None


def _digits(value: str | None) -> str:
    if not value:
        return ""
    return "".join(c for c in value if c.isdigit())


def _dec_str(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value, "f")
