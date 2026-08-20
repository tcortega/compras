from __future__ import annotations

from compras_normalize.text import fold

# Same 59 IBGE codes as web/lib/copy.ts SLICE_MUNICIPIOS. Do not add. Do not drop.
SLICE_IBGE_CODES = frozenset(
    {
        "3306305",
        "3303302",
        "3506003",
        "4305108",
        "4209102",
        "3170206",
        "4113700",
        "2910800",
        "2604106",
        "5201108",
        "3205200",
        "2504009",
        "2303709",
        "2105302",
        "2700300",
        "5003702",
        "1504208",
        "5108402",
        "1100122",
        "2403251",
        "1200203",
        "1600600",
        "1400472",
        "4115200",
        "3554102",
        "4104808",
        "3136702",
        "4108304",
        "4316907",
        "3143302",
        "3127701",
        "4304606",
        "4209300",
        "1506807",
        "5218805",
        "2924009",
        "2613701",
        "2304202",
        "1100023",
        "3201506",
        "1502400",
        "3122306",
        "3303906",
        "3131307",
        "3302403",
        "3157807",
        "3303401",
        "3529005",
        "4202008",
        "3523107",
        "3541000",
        "4125506",
        "3552502",
        "3518701",
        "3513009",
        "1505536",
        "3524402",
        "3301900",
        "3302700",
    }
)
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
