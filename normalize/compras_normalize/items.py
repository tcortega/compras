from __future__ import annotations

from decimal import Decimal

import polars as pl

from compras_normalize.catalog import Catalog
from compras_normalize.specs import extract_specs
from compras_normalize.text import fold, parse_date, parse_decimal, parse_datetime, quarter_of
from compras_normalize.units import UnitMatch, UnitTable

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
    return pl.DataFrame(rows)


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
    spec = extract_specs(descricao)
    unit_raw = _first(row, "unidademedida", "nomeunidademedida", "siglaunidademedida") or ""
    unit = units.match(unit_raw)
    qty = parse_decimal(_first(row, "quantidaderesultado", "quantidade")) or Decimal("0")
    resultado_unit = parse_decimal(_first(row, "valorunitarioresultado", "valorunitariohomologado"))
    estimado_unit = parse_decimal(_first(row, "valorunitarioestimado"))
    unit_price = resultado_unit
    if unit_price is None:
        unit_price = parse_decimal(_first(row, "valorunitario", "valorunitarioestimado"))
    total = parse_decimal(_first(row, "valortotalresultado", "valortotal"))
    price_base = _price_per_canonical(unit, unit_price, qty, total)
    publicado = parse_datetime(_first(row, "datapublicacaopncp", "datainclusaopncp"))
    resultado = parse_date(_first(row, "dataresultado", "data_resultado"))
    item_pub = parse_date(_first(row, "datainclusaopncp"))
    award = parse_date(_first(row, "award_date")) or resultado or item_pub
    fornecedor_cnpj = _digits(_first(row, "codfornecedor", "nifornecedor", "fornecedor_cnpj"))
    opened_on = None
    cnae = None
    cnae_sec = None
    razao_forn = _first(row, "nomefornecedor", "fornecedor_razao")
    if len(fornecedor_cnpj) == 14 and fornecedor_cnpj in cnpj_by:
        info = cnpj_by[fornecedor_cnpj]
        opened_on = info.get("opened_on")
        cnae = info.get("cnae")
        cnae_sec = info.get("cnae_secundaria")
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
        "cnae_secundaria": cnae_sec or "",
        "pncp_id": _first(row, "numerocontrolepncp", "idcontratacaopncp", "pncp_id") or "",
        "modalidade": _first(row, "modalidadenome", "modalidade") or "",
        "modalidade_codigo": _first(row, "codigomodalidade", "modalidade_codigo") or "",
        "objeto": _first(row, "objetocompra", "objeto") or "",
        "ano": _first(row, "anocomprapncp", "ano") or (str(publicado.year) if publicado else ""),
        "valor_homologado": _dec_str(parse_decimal(_first(row, "valortotalhomologado"))),
        "publicado_em": publicado.isoformat() if publicado else "",
        "data_resultado": resultado.isoformat() if resultado else "",
        "award_date": award.isoformat() if award else "",
        "descricao": descricao or "",
        "catmat": hit.catmat or "",
        "catser": hit.catser or "",
        "catmat_match_quality": hit.quality,
        "spec_concentracao": spec.concentracao or "",
        "spec_dosagem": spec.dosagem or "",
        "spec_tamanho": spec.tamanho or "",
        "quantidade": _dec_str(qty),
        "unidade_medida": unit_raw,
        "unidade_canonica": unit.canonical,
        "unit_parse_confidence": unit.confidence,
        "valor_unitario": _dec_str(unit_price),
        "valor_unitario_resultado": _dec_str(resultado_unit),
        "valor_unitario_estimado": _dec_str(estimado_unit),
        "situacao": _first(
            row,
            "situacaocompraitemnome",
            "situacaocompranome",
            "situacaocompraitem",
            "situacao",
        )
        or "",
        "resultado_http": _first(row, "resultado_http", "resultados_http", "resultado_status") or "",
        "valor_total": _dec_str(total),
        "valor_referencia": _dec_str(
            parse_decimal(_first(row, "valor_referencia", "preco_referencia", "valor_referencia_catalogo"))
        ),
        "preco_referencia": _dec_str(parse_decimal(_first(row, "preco_referencia"))),
        "valor_por_unidade_canonica": _dec_str(price_base),
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
            "cnae_secundaria": str(
                folded.get("cnae_fiscal_secundaria") or folded.get("cnae_secundaria") or ""
            ),
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


def _price_per_canonical(
    unit: UnitMatch, unit_price: Decimal | None, qty: Decimal, total: Decimal | None
) -> Decimal | None:
    if unit.canonical == "unknown" or unit.confidence == "unknown":
        return None
    factor = unit.to_base_factor
    if factor == 0:
        return None
    price = unit_price
    if price is None and total is not None and qty != 0:
        price = total / qty
    if price is None:
        return None
    return (price / factor).quantize(Decimal("0.000001"))


def _dec_str(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value, "f")
