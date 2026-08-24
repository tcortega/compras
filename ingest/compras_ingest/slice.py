from __future__ import annotations

from compras_normalize.text import fold

# Covered municipal-executive IBGE set. Same as web/lib/copy.ts SLICE_MUNICIPIOS.
# Add from official COMPRA+ITEM volume. Do not invent codes.
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
    "1200104": "AC",
    "1200344": "AC",
    "1200401": "AC",
    "1200609": "AC",
    "2701704": "AL",
    "2702504": "AL",
    "2707701": "AL",
    "2709301": "AL",
    "1300201": "AM",
    "1301308": "AM",
    "1304005": "AM",
    "1600303": "AP",
    "2908101": "BA",
    "2912707": "BA",
    "2927309": "BA",
    "2929602": "BA",
    "2301000": "CE",
    "2304400": "CE",
    "2304954": "CE",
    "2305233": "CE",
    "3203106": "ES",
    "3203700": "ES",
    "3204302": "ES",
    "3204955": "ES",
    "5205497": "GO",
    "5208509": "GO",
    "5210406": "GO",
    "5219753": "GO",
    "2104552": "MA",
    "2110039": "MA",
    "2110658": "MA",
    "2111300": "MA",
    "3106200": "MG",
    "3111200": "MG",
    "3120201": "MG",
    "3131901": "MG",
    "5001904": "MS",
    "5005400": "MS",
    "5102504": "MT",
    "5107743": "MT",
    "1501451": "PA",
    "1506203": "PA",
    "1507201": "PA",
    "1507979": "PA",
    "2500601": "PB",
    "2503704": "PB",
    "2509701": "PB",
    "2513901": "PB",
    "2601706": "PE",
    "2601904": "PE",
    "2612802": "PE",
    "2615201": "PE",
    "2202075": "PI",
    "2204204": "PI",
    "2210623": "PI",
    "2211209": "PI",
    "4103701": "PR",
    "4107207": "PR",
    "4108403": "PR",
    "4115309": "PR",
    "4118501": "PR",
    "4120606": "PR",
    "4121406": "PR",
    "4122800": "PR",
    "4127106": "PR",
    "4127965": "PR",
    "4128559": "PR",
    "3300100": "RJ",
    "3302254": "RJ",
    "3304557": "RJ",
    "3305208": "RJ",
    "2402303": "RN",
    "2403103": "RN",
    "2408102": "RN",
    "1100452": "RO",
    "1100114": "RO",
    "1100205": "RO",
    "1400100": "RR",
    "1400175": "RR",
    "1400209": "RR",
    "1400605": "RR",
    "4303103": "RS",
    "4305900": "RS",
    "4318903": "RS",
    "4319802": "RS",
    "4208005": "SC",
    "4214201": "SC",
    "4217402": "SC",
    "4219507": "SC",
    "3507506": "SP",
    "3508108": "SP",
    "3509502": "SP",
    "3518800": "SP",
    "3530805": "SP",
    "3536703": "SP",
    "3543402": "SP",
    "3547601": "SP",
    "3549508": "SP",
    "3556206": "SP",
    "1705508": "TO",
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
