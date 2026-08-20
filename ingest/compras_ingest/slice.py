from __future__ import annotations

from compras_normalize.text import fold

# Same 59 IBGE codes as web/lib/copy.ts SLICE_MUNICIPIOS. Do not add. Do not drop.
# ibge -> uf. Same 59 as web/lib/copy.ts. Frozen.
SLICE_IBGE_UF = {
    "3306305": "RJ",
    "3303302": "RJ",
    "3506003": "SP",
    "4305108": "RS",
    "4209102": "SC",
    "3170206": "MG",
    "4113700": "PR",
    "2910800": "BA",
    "2604106": "PE",
    "5201108": "GO",
    "3205200": "ES",
    "2504009": "PB",
    "2303709": "CE",
    "2105302": "MA",
    "2700300": "AL",
    "5003702": "MS",
    "1504208": "PA",
    "5108402": "MT",
    "1100122": "RO",
    "2403251": "RN",
    "1200203": "AC",
    "1600600": "AP",
    "1400472": "RR",
    "4115200": "PR",
    "3554102": "SP",
    "4104808": "PR",
    "3136702": "MG",
    "4108304": "PR",
    "4316907": "RS",
    "3143302": "MG",
    "3127701": "MG",
    "4304606": "RS",
    "4209300": "SC",
    "1506807": "PA",
    "5218805": "GO",
    "2924009": "BA",
    "2613701": "PE",
    "2304202": "CE",
    "1100023": "RO",
    "3201506": "ES",
    "1502400": "PA",
    "3122306": "MG",
    "3303906": "RJ",
    "3131307": "MG",
    "3302403": "RJ",
    "3157807": "MG",
    "3303401": "RJ",
    "3529005": "SP",
    "4202008": "SC",
    "3523107": "SP",
    "3541000": "SP",
    "4125506": "PR",
    "3552502": "SP",
    "3518701": "SP",
    "3513009": "SP",
    "1505536": "PA",
    "3524402": "SP",
    "3301900": "RJ",
    "3302700": "RJ",
}
SLICE_IBGE_CODES = frozenset(SLICE_IBGE_UF)
LEG_PODER = frozenset({"l", "legislativo", "legislative"})
MUNICIPAL_ESFERA = frozenset({"m", "municipal", "3"})
COMPRAS_GOV_YEARS = (2024, 2025, 2026)


def ibge_token(value: object) -> str:
    raw = str(value or "").strip()
    if raw == "" or raw.lower() in {"nan", "none", "null", "-"}:
        return ""
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        return ""
    if "." in raw:
        try:
            parsed = int(float(raw))
            return str(parsed) if parsed > 0 else ""
        except ValueError:
            return digits
    return digits


def is_municipal(esfera: object) -> bool:
    return fold(str(esfera or "")).replace(" ", "") in MUNICIPAL_ESFERA


def is_legislative(poder: object) -> bool:
    return fold(str(poder or "")).replace(" ", "") in LEG_PODER


def keep_municipal_non_legislative(esfera: object, poder: object) -> bool:
    return is_municipal(esfera) and not is_legislative(poder)


def keep_slice_ibge(value: object) -> bool:
    token = ibge_token(value)
    return token in SLICE_IBGE_CODES
