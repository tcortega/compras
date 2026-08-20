#!/usr/bin/env python3
"""Hit served API list/get and web pages. Fail on stub data or public flag fields."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

API = os.environ.get("API_BASE_URL", "http://127.0.0.1:5080").rstrip("/")
WEB = os.environ.get("WEB_BASE_URL", "http://127.0.0.1:3100").rstrip("/")

STUB_MARKERS = (
    "7c2e1f40-3306-4050",
    "8d3f2a51-3306-4050",
    "9e4a3b62-3306-4050",
    "ae5b4c73-3306-4050",
    "Dipirona",
    "Distribuidora de Medicamentos Serra",
    "sha256:dev-slice-vr-2024",
)
BANNED_COPY = re.compile(r"fraude|corrupto|roubo|flag|ranking", re.I)
FLAG_KEY = re.compile(r"flag", re.I)
STAT_HOMOLOGADO = re.compile(r'class="kicker">Homologado')
PUBLISHED = {
    "3306305": ("volta redonda", "RJ"),
    "3303302": ("niteroi", "RJ"),
    "3506003": ("bauru", "SP"),
    "4305108": ("caxias do sul", "RS"),
    "4209102": ("joinville", "SC"),
    "3170206": ("uberlandia", "MG"),
    "4113700": ("londrina", "PR"),
    "2910800": ("feira de santana", "BA"),
    "2604106": ("caruaru", "PE"),
    "5201108": ("anapolis", "GO"),
    "3205200": ("vila velha", "ES"),
    "2504009": ("campina grande", "PB"),
    "2303709": ("caucaia", "CE"),
    "2105302": ("imperatriz", "MA"),
    "2700300": ("arapiraca", "AL"),
    "5003702": ("dourados", "MS"),
    "1504208": ("maraba", "PA"),
    "5108402": ("varzea grande", "MT"),
    "1100122": ("ji-parana", "RO"),
    "2403251": ("parnamirim", "RN"),
    "1200203": ("cruzeiro do sul", "AC"),
    "1600600": ("municipio de santana", "AP"),
    "1400472": ("rorainopolis", "RR"),
    "4115200": ("municipio de maringa", "PR"),
    "3554102": ("municipio de taubate", "SP"),
    "4104808": ("municipio de cascavel", "PR"),
    "3136702": ("municipio de juiz de fora", "MG"),
    "4108304": ("municipio de foz do iguacu", "PR"),
    "4316907": ("municipio de santa maria", "RS"),
    "3143302": ("municipio de montes claros", "MG"),
    "3127701": ("municipio de governador valadares", "MG"),
    "4304606": ("municipio de canoas", "RS"),
    "4209300": ("municipio de lages", "SC"),
    "1506807": ("municipio de santarem", "PA"),
    "5218805": ("municipio de rio verde", "GO"),
    "2924009": ("municipio de paulo afonso", "BA"),
    "2613701": ("municipio de sao lourenco da mata", "PE"),
    "2304202": ("municipio de crato", "CE"),
    "1100023": ("municipio de ariquemes", "RO"),
    "3201506": ("municipio de colatina", "ES"),
    "1502400": ("municipio de castanhal", "PA"),
    "3122306": ("municipio de divinopolis", "MG"),
    "3303906": ("municipio de petropolis", "RJ"),
    "3131307": ("municipio de ipatinga", "MG"),
    "3302403": ("municipio de macae", "RJ"),
    "3157807": ("municipio de santa luzia", "MG"),
    "3303401": ("municipio de nova friburgo", "RJ"),
}


def main() -> int:
    orgaos = get_json(f"{API}/api/orgaos?skip=0&take=100")
    deny_flags(orgaos, f"{API}/api/orgaos")
    deny_stub(json.dumps(orgaos, ensure_ascii=False), "api /api/orgaos")
    items_page = orgaos.get("items") or []
    if len(items_page) < 47:
        raise SystemExit(f"api /api/orgaos returned {len(items_page)} rows, need the published slice")
    by_ibge = {str(row.get("municipioIbge") or ""): row for row in items_page}
    for ibge, (nome, uf) in PUBLISHED.items():
        row = by_ibge.get(ibge)
        if row is None:
            raise SystemExit(f"api /api/orgaos missing IBGE {ibge}")
        razao = str(row.get("razaoSocial") or "")
        if nome not in razao.casefold():
            raise SystemExit(f"api orgao {ibge} razao is not {nome}: {razao}")
        if str(row.get("uf") or "") != uf:
            raise SystemExit(f"api orgao {ibge} UF is not {uf}: {row.get('uf')}")
        if str(row.get("cnpj") or "") == "29138108000113":
            raise SystemExit("api served stub Prefeitura CNPJ")
    orgao_cov = orgaos.get("coverage") or {}
    if orgao_cov.get("uf") not in (None, ""):
        raise SystemExit(f"mixed orgao list invented a UF: {orgao_cov}")
    if not isinstance(orgao_cov.get("n"), int) or orgao_cov["n"] < 47:
        raise SystemExit(f"api orgaos coverage.n missing the extra slice: {orgao_cov}")
    if not orgao_cov.get("methodologyVersion"):
        raise SystemExit(f"api orgaos coverage missing methodologyVersion: {orgao_cov}")

    niteroi = get_json(f"{API}/api/orgaos?municipioIbge=3303302&skip=0&take=50")
    deny_flags(niteroi, f"{API}/api/orgaos?municipioIbge=3303302")
    niteroi_rows = niteroi.get("items") or []
    if len(niteroi_rows) != 1 or str(niteroi_rows[0].get("municipioIbge") or "") != "3303302":
        raise SystemExit(f"api municipio filter 3303302 failed: {niteroi_rows}")
    bauru = get_json(f"{API}/api/orgaos?uf=SP&skip=0&take=50")
    deny_flags(bauru, f"{API}/api/orgaos?uf=SP")
    bauru_rows = bauru.get("items") or []
    if not bauru_rows or any(str(row.get("uf") or "") != "SP" for row in bauru_rows):
        raise SystemExit(f"api UF=SP filter failed: {bauru_rows}")
    if str((bauru.get("coverage") or {}).get("uf") or "") != "SP":
        raise SystemExit(f"api UF=SP coverage lost slice UF: {bauru.get('coverage')}")

    caxias = get_json(f"{API}/api/orgaos?municipioIbge=4305108&skip=0&take=50")
    deny_flags(caxias, f"{API}/api/orgaos?municipioIbge=4305108")
    caxias_rows = caxias.get("items") or []
    if len(caxias_rows) != 1 or str(caxias_rows[0].get("municipioIbge") or "") != "4305108":
        raise SystemExit(f"api municipio filter 4305108 failed: {caxias_rows}")
    joinville = get_json(f"{API}/api/orgaos?uf=SC&skip=0&take=50")
    deny_flags(joinville, f"{API}/api/orgaos?uf=SC")
    joinville_rows = joinville.get("items") or []
    if not joinville_rows or any(str(row.get("uf") or "") != "SC" for row in joinville_rows):
        raise SystemExit(f"api UF=SC filter failed: {joinville_rows}")
    if str((joinville.get("coverage") or {}).get("uf") or "") != "SC":
        raise SystemExit(f"api UF=SC coverage lost slice UF: {joinville.get('coverage')}")

    uberlandia = get_json(f"{API}/api/orgaos?municipioIbge=3170206&skip=0&take=50")
    deny_flags(uberlandia, f"{API}/api/orgaos?municipioIbge=3170206")
    uberlandia_rows = uberlandia.get("items") or []
    if len(uberlandia_rows) != 1 or str(uberlandia_rows[0].get("municipioIbge") or "") != "3170206":
        raise SystemExit(f"api municipio filter 3170206 failed: {uberlandia_rows}")
    londrina = get_json(f"{API}/api/orgaos?uf=PR&skip=0&take=50")
    deny_flags(londrina, f"{API}/api/orgaos?uf=PR")
    londrina_rows = londrina.get("items") or []
    if not londrina_rows or any(str(row.get("uf") or "") != "PR" for row in londrina_rows):
        raise SystemExit(f"api UF=PR filter failed: {londrina_rows}")
    if str((londrina.get("coverage") or {}).get("uf") or "") != "PR":
        raise SystemExit(f"api UF=PR coverage lost slice UF: {londrina.get('coverage')}")

    feira = get_json(f"{API}/api/orgaos?municipioIbge=2910800&skip=0&take=50")
    deny_flags(feira, f"{API}/api/orgaos?municipioIbge=2910800")
    feira_rows = feira.get("items") or []
    if len(feira_rows) != 1 or str(feira_rows[0].get("municipioIbge") or "") != "2910800":
        raise SystemExit(f"api municipio filter 2910800 failed: {feira_rows}")
    caruaru = get_json(f"{API}/api/orgaos?uf=PE&skip=0&take=50")
    deny_flags(caruaru, f"{API}/api/orgaos?uf=PE")
    caruaru_rows = caruaru.get("items") or []
    if not caruaru_rows or any(str(row.get("uf") or "") != "PE" for row in caruaru_rows):
        raise SystemExit(f"api UF=PE filter failed: {caruaru_rows}")
    if str((caruaru.get("coverage") or {}).get("uf") or "") != "PE":
        raise SystemExit(f"api UF=PE coverage lost slice UF: {caruaru.get('coverage')}")

    anapolis = get_json(f"{API}/api/orgaos?municipioIbge=5201108&skip=0&take=50")
    deny_flags(anapolis, f"{API}/api/orgaos?municipioIbge=5201108")
    anapolis_rows = anapolis.get("items") or []
    if len(anapolis_rows) != 1 or str(anapolis_rows[0].get("municipioIbge") or "") != "5201108":
        raise SystemExit(f"api municipio filter 5201108 failed: {anapolis_rows}")
    vila_velha = get_json(f"{API}/api/orgaos?uf=ES&skip=0&take=50")
    deny_flags(vila_velha, f"{API}/api/orgaos?uf=ES")
    vila_velha_rows = vila_velha.get("items") or []
    if not vila_velha_rows or any(str(row.get("uf") or "") != "ES" for row in vila_velha_rows):
        raise SystemExit(f"api UF=ES filter failed: {vila_velha_rows}")
    if str((vila_velha.get("coverage") or {}).get("uf") or "") != "ES":
        raise SystemExit(f"api UF=ES coverage lost slice UF: {vila_velha.get('coverage')}")
    es_ibges = {str(row.get("municipioIbge") or "") for row in vila_velha_rows}
    if "3205200" not in es_ibges or "3201506" not in es_ibges:
        raise SystemExit(f"api UF=ES missing Vila Velha or Colatina: {vila_velha_rows}")

    campina = get_json(f"{API}/api/orgaos?municipioIbge=2504009&skip=0&take=50")
    deny_flags(campina, f"{API}/api/orgaos?municipioIbge=2504009")
    campina_rows = campina.get("items") or []
    if len(campina_rows) != 1 or str(campina_rows[0].get("municipioIbge") or "") != "2504009":
        raise SystemExit(f"api municipio filter 2504009 failed: {campina_rows}")
    caucaia = get_json(f"{API}/api/orgaos?uf=CE&skip=0&take=50")
    deny_flags(caucaia, f"{API}/api/orgaos?uf=CE")
    caucaia_rows = caucaia.get("items") or []
    if not caucaia_rows or any(str(row.get("uf") or "") != "CE" for row in caucaia_rows):
        raise SystemExit(f"api UF=CE filter failed: {caucaia_rows}")
    if str((caucaia.get("coverage") or {}).get("uf") or "") != "CE":
        raise SystemExit(f"api UF=CE coverage lost slice UF: {caucaia.get('coverage')}")
    ce_ibges = {str(row.get("municipioIbge") or "") for row in caucaia_rows}
    if "2303709" not in ce_ibges or "2304202" not in ce_ibges:
        raise SystemExit(f"api UF=CE missing Caucaia or Crato: {caucaia_rows}")

    imperatriz = get_json(f"{API}/api/orgaos?municipioIbge=2105302&skip=0&take=50")
    deny_flags(imperatriz, f"{API}/api/orgaos?municipioIbge=2105302")
    imperatriz_rows = imperatriz.get("items") or []
    if len(imperatriz_rows) != 1 or str(imperatriz_rows[0].get("municipioIbge") or "") != "2105302":
        raise SystemExit(f"api municipio filter 2105302 failed: {imperatriz_rows}")
    arapiraca = get_json(f"{API}/api/orgaos?uf=AL&skip=0&take=50")
    deny_flags(arapiraca, f"{API}/api/orgaos?uf=AL")
    arapiraca_rows = arapiraca.get("items") or []
    if not arapiraca_rows or any(str(row.get("uf") or "") != "AL" for row in arapiraca_rows):
        raise SystemExit(f"api UF=AL filter failed: {arapiraca_rows}")
    if str((arapiraca.get("coverage") or {}).get("uf") or "") != "AL":
        raise SystemExit(f"api UF=AL coverage lost slice UF: {arapiraca.get('coverage')}")

    dourados = get_json(f"{API}/api/orgaos?municipioIbge=5003702&skip=0&take=50")
    deny_flags(dourados, f"{API}/api/orgaos?municipioIbge=5003702")
    dourados_rows = dourados.get("items") or []
    if len(dourados_rows) != 1 or str(dourados_rows[0].get("municipioIbge") or "") != "5003702":
        raise SystemExit(f"api municipio filter 5003702 failed: {dourados_rows}")
    maraba = get_json(f"{API}/api/orgaos?uf=PA&skip=0&take=50")
    deny_flags(maraba, f"{API}/api/orgaos?uf=PA")
    maraba_rows = maraba.get("items") or []
    if not maraba_rows or any(str(row.get("uf") or "") != "PA" for row in maraba_rows):
        raise SystemExit(f"api UF=PA filter failed: {maraba_rows}")
    if str((maraba.get("coverage") or {}).get("uf") or "") != "PA":
        raise SystemExit(f"api UF=PA coverage lost slice UF: {maraba.get('coverage')}")
    pa_ibges = {str(row.get("municipioIbge") or "") for row in maraba_rows}
    if "1504208" not in pa_ibges or "1506807" not in pa_ibges or "1502400" not in pa_ibges:
        raise SystemExit(f"api UF=PA missing Marabá, Santarém or Castanhal: {maraba_rows}")

    varzea = get_json(f"{API}/api/orgaos?municipioIbge=5108402&skip=0&take=50")
    deny_flags(varzea, f"{API}/api/orgaos?municipioIbge=5108402")
    varzea_rows = varzea.get("items") or []
    if len(varzea_rows) != 1 or str(varzea_rows[0].get("municipioIbge") or "") != "5108402":
        raise SystemExit(f"api municipio filter 5108402 failed: {varzea_rows}")
    ji_parana = get_json(f"{API}/api/orgaos?uf=RO&skip=0&take=50")
    deny_flags(ji_parana, f"{API}/api/orgaos?uf=RO")
    ji_parana_rows = ji_parana.get("items") or []
    if not ji_parana_rows or any(str(row.get("uf") or "") != "RO" for row in ji_parana_rows):
        raise SystemExit(f"api UF=RO filter failed: {ji_parana_rows}")
    if str((ji_parana.get("coverage") or {}).get("uf") or "") != "RO":
        raise SystemExit(f"api UF=RO coverage lost slice UF: {ji_parana.get('coverage')}")
    ro_ibges = {str(row.get("municipioIbge") or "") for row in ji_parana_rows}
    if "1100122" not in ro_ibges or "1100023" not in ro_ibges:
        raise SystemExit(f"api UF=RO missing Ji-Paraná or Ariquemes: {ji_parana_rows}")

    parnamirim = get_json(f"{API}/api/orgaos?municipioIbge=2403251&skip=0&take=50")
    deny_flags(parnamirim, f"{API}/api/orgaos?municipioIbge=2403251")
    parnamirim_rows = parnamirim.get("items") or []
    if len(parnamirim_rows) != 1 or str(parnamirim_rows[0].get("municipioIbge") or "") != "2403251":
        raise SystemExit(f"api municipio filter 2403251 failed: {parnamirim_rows}")
    cruzeiro = get_json(f"{API}/api/orgaos?uf=AC&skip=0&take=50")
    deny_flags(cruzeiro, f"{API}/api/orgaos?uf=AC")
    cruzeiro_rows = cruzeiro.get("items") or []
    if not cruzeiro_rows or any(str(row.get("uf") or "") != "AC" for row in cruzeiro_rows):
        raise SystemExit(f"api UF=AC filter failed: {cruzeiro_rows}")
    if str((cruzeiro.get("coverage") or {}).get("uf") or "") != "AC":
        raise SystemExit(f"api UF=AC coverage lost slice UF: {cruzeiro.get('coverage')}")

    santana = get_json(f"{API}/api/orgaos?municipioIbge=1600600&skip=0&take=50")
    deny_flags(santana, f"{API}/api/orgaos?municipioIbge=1600600")
    santana_rows = santana.get("items") or []
    if len(santana_rows) != 1 or str(santana_rows[0].get("municipioIbge") or "") != "1600600":
        raise SystemExit(f"api municipio filter 1600600 failed: {santana_rows}")
    rorainopolis = get_json(f"{API}/api/orgaos?uf=RR&skip=0&take=50")
    deny_flags(rorainopolis, f"{API}/api/orgaos?uf=RR")
    rorainopolis_rows = rorainopolis.get("items") or []
    if not rorainopolis_rows or any(str(row.get("uf") or "") != "RR" for row in rorainopolis_rows):
        raise SystemExit(f"api UF=RR filter failed: {rorainopolis_rows}")
    if str((rorainopolis.get("coverage") or {}).get("uf") or "") != "RR":
        raise SystemExit(f"api UF=RR coverage lost slice UF: {rorainopolis.get('coverage')}")

    maringa = get_json(f"{API}/api/orgaos?municipioIbge=4115200&skip=0&take=50")
    deny_flags(maringa, f"{API}/api/orgaos?municipioIbge=4115200")
    maringa_rows = maringa.get("items") or []
    if len(maringa_rows) != 1 or str(maringa_rows[0].get("municipioIbge") or "") != "4115200":
        raise SystemExit(f"api municipio filter 4115200 failed: {maringa_rows}")
    taubate = get_json(f"{API}/api/orgaos?municipioIbge=3554102&skip=0&take=50")
    deny_flags(taubate, f"{API}/api/orgaos?municipioIbge=3554102")
    taubate_rows = taubate.get("items") or []
    if len(taubate_rows) != 1 or str(taubate_rows[0].get("municipioIbge") or "") != "3554102":
        raise SystemExit(f"api municipio filter 3554102 failed: {taubate_rows}")
    cascavel = get_json(f"{API}/api/orgaos?municipioIbge=4104808&skip=0&take=50")
    deny_flags(cascavel, f"{API}/api/orgaos?municipioIbge=4104808")
    cascavel_rows = cascavel.get("items") or []
    if len(cascavel_rows) != 1 or str(cascavel_rows[0].get("municipioIbge") or "") != "4104808":
        raise SystemExit(f"api municipio filter 4104808 failed: {cascavel_rows}")
    juiz = get_json(f"{API}/api/orgaos?municipioIbge=3136702&skip=0&take=50")
    deny_flags(juiz, f"{API}/api/orgaos?municipioIbge=3136702")
    juiz_rows = juiz.get("items") or []
    if len(juiz_rows) != 1 or str(juiz_rows[0].get("municipioIbge") or "") != "3136702":
        raise SystemExit(f"api municipio filter 3136702 failed: {juiz_rows}")
    foz = get_json(f"{API}/api/orgaos?municipioIbge=4108304&skip=0&take=50")
    deny_flags(foz, f"{API}/api/orgaos?municipioIbge=4108304")
    foz_rows = foz.get("items") or []
    if len(foz_rows) != 1 or str(foz_rows[0].get("municipioIbge") or "") != "4108304":
        raise SystemExit(f"api municipio filter 4108304 failed: {foz_rows}")
    santa = get_json(f"{API}/api/orgaos?municipioIbge=4316907&skip=0&take=50")
    deny_flags(santa, f"{API}/api/orgaos?municipioIbge=4316907")
    santa_rows = santa.get("items") or []
    if len(santa_rows) != 1 or str(santa_rows[0].get("municipioIbge") or "") != "4316907":
        raise SystemExit(f"api municipio filter 4316907 failed: {santa_rows}")
    montes = get_json(f"{API}/api/orgaos?municipioIbge=3143302&skip=0&take=50")
    deny_flags(montes, f"{API}/api/orgaos?municipioIbge=3143302")
    montes_rows = montes.get("items") or []
    if len(montes_rows) != 1 or str(montes_rows[0].get("municipioIbge") or "") != "3143302":
        raise SystemExit(f"api municipio filter 3143302 failed: {montes_rows}")
    valadares = get_json(f"{API}/api/orgaos?municipioIbge=3127701&skip=0&take=50")
    deny_flags(valadares, f"{API}/api/orgaos?municipioIbge=3127701")
    valadares_rows = valadares.get("items") or []
    if len(valadares_rows) != 1 or str(valadares_rows[0].get("municipioIbge") or "") != "3127701":
        raise SystemExit(f"api municipio filter 3127701 failed: {valadares_rows}")
    canoas = get_json(f"{API}/api/orgaos?municipioIbge=4304606&skip=0&take=50")
    deny_flags(canoas, f"{API}/api/orgaos?municipioIbge=4304606")
    canoas_rows = canoas.get("items") or []
    if len(canoas_rows) != 1 or str(canoas_rows[0].get("municipioIbge") or "") != "4304606":
        raise SystemExit(f"api municipio filter 4304606 failed: {canoas_rows}")
    lages = get_json(f"{API}/api/orgaos?municipioIbge=4209300&skip=0&take=50")
    deny_flags(lages, f"{API}/api/orgaos?municipioIbge=4209300")
    lages_rows = lages.get("items") or []
    if len(lages_rows) != 1 or str(lages_rows[0].get("municipioIbge") or "") != "4209300":
        raise SystemExit(f"api municipio filter 4209300 failed: {lages_rows}")
    santarem = get_json(f"{API}/api/orgaos?municipioIbge=1506807&skip=0&take=50")
    deny_flags(santarem, f"{API}/api/orgaos?municipioIbge=1506807")
    santarem_rows = santarem.get("items") or []
    if len(santarem_rows) != 1 or str(santarem_rows[0].get("municipioIbge") or "") != "1506807":
        raise SystemExit(f"api municipio filter 1506807 failed: {santarem_rows}")
    rio_verde = get_json(f"{API}/api/orgaos?municipioIbge=5218805&skip=0&take=50")
    deny_flags(rio_verde, f"{API}/api/orgaos?municipioIbge=5218805")
    rio_verde_rows = rio_verde.get("items") or []
    if len(rio_verde_rows) != 1 or str(rio_verde_rows[0].get("municipioIbge") or "") != "5218805":
        raise SystemExit(f"api municipio filter 5218805 failed: {rio_verde_rows}")
    paulo_afonso = get_json(f"{API}/api/orgaos?municipioIbge=2924009&skip=0&take=50")
    deny_flags(paulo_afonso, f"{API}/api/orgaos?municipioIbge=2924009")
    paulo_afonso_rows = paulo_afonso.get("items") or []
    if len(paulo_afonso_rows) != 1 or str(paulo_afonso_rows[0].get("municipioIbge") or "") != "2924009":
        raise SystemExit(f"api municipio filter 2924009 failed: {paulo_afonso_rows}")
    sao_lourenco = get_json(f"{API}/api/orgaos?municipioIbge=2613701&skip=0&take=50")
    deny_flags(sao_lourenco, f"{API}/api/orgaos?municipioIbge=2613701")
    sao_lourenco_rows = sao_lourenco.get("items") or []
    if len(sao_lourenco_rows) != 1 or str(sao_lourenco_rows[0].get("municipioIbge") or "") != "2613701":
        raise SystemExit(f"api municipio filter 2613701 failed: {sao_lourenco_rows}")
    crato = get_json(f"{API}/api/orgaos?municipioIbge=2304202&skip=0&take=50")
    deny_flags(crato, f"{API}/api/orgaos?municipioIbge=2304202")
    crato_rows = crato.get("items") or []
    if len(crato_rows) != 1 or str(crato_rows[0].get("municipioIbge") or "") != "2304202":
        raise SystemExit(f"api municipio filter 2304202 failed: {crato_rows}")
    ariquemes = get_json(f"{API}/api/orgaos?municipioIbge=1100023&skip=0&take=50")
    deny_flags(ariquemes, f"{API}/api/orgaos?municipioIbge=1100023")
    ariquemes_rows = ariquemes.get("items") or []
    if len(ariquemes_rows) != 1 or str(ariquemes_rows[0].get("municipioIbge") or "") != "1100023":
        raise SystemExit(f"api municipio filter 1100023 failed: {ariquemes_rows}")
    colatina = get_json(f"{API}/api/orgaos?municipioIbge=3201506&skip=0&take=50")
    deny_flags(colatina, f"{API}/api/orgaos?municipioIbge=3201506")
    colatina_rows = colatina.get("items") or []
    if len(colatina_rows) != 1 or str(colatina_rows[0].get("municipioIbge") or "") != "3201506":
        raise SystemExit(f"api municipio filter 3201506 failed: {colatina_rows}")
    castanhal = get_json(f"{API}/api/orgaos?municipioIbge=1502400&skip=0&take=50")
    deny_flags(castanhal, f"{API}/api/orgaos?municipioIbge=1502400")
    castanhal_rows = castanhal.get("items") or []
    if len(castanhal_rows) != 1 or str(castanhal_rows[0].get("municipioIbge") or "") != "1502400":
        raise SystemExit(f"api municipio filter 1502400 failed: {castanhal_rows}")
    divinopolis = get_json(f"{API}/api/orgaos?municipioIbge=3122306&skip=0&take=50")
    deny_flags(divinopolis, f"{API}/api/orgaos?municipioIbge=3122306")
    divinopolis_rows = divinopolis.get("items") or []
    if len(divinopolis_rows) != 1 or str(divinopolis_rows[0].get("municipioIbge") or "") != "3122306":
        raise SystemExit(f"api municipio filter 3122306 failed: {divinopolis_rows}")
    petropolis = get_json(f"{API}/api/orgaos?municipioIbge=3303906&skip=0&take=50")
    deny_flags(petropolis, f"{API}/api/orgaos?municipioIbge=3303906")
    petropolis_rows = petropolis.get("items") or []
    if len(petropolis_rows) != 1 or str(petropolis_rows[0].get("municipioIbge") or "") != "3303906":
        raise SystemExit(f"api municipio filter 3303906 failed: {petropolis_rows}")
    ipatinga = get_json(f"{API}/api/orgaos?municipioIbge=3131307&skip=0&take=50")
    deny_flags(ipatinga, f"{API}/api/orgaos?municipioIbge=3131307")
    ipatinga_rows = ipatinga.get("items") or []
    if len(ipatinga_rows) != 1 or str(ipatinga_rows[0].get("municipioIbge") or "") != "3131307":
        raise SystemExit(f"api municipio filter 3131307 failed: {ipatinga_rows}")
    macae = get_json(f"{API}/api/orgaos?municipioIbge=3302403&skip=0&take=50")
    deny_flags(macae, f"{API}/api/orgaos?municipioIbge=3302403")
    macae_rows = macae.get("items") or []
    if len(macae_rows) != 1 or str(macae_rows[0].get("municipioIbge") or "") != "3302403":
        raise SystemExit(f"api municipio filter 3302403 failed: {macae_rows}")
    santa_luzia = get_json(f"{API}/api/orgaos?municipioIbge=3157807&skip=0&take=50")
    deny_flags(santa_luzia, f"{API}/api/orgaos?municipioIbge=3157807")
    santa_luzia_rows = santa_luzia.get("items") or []
    if len(santa_luzia_rows) != 1 or str(santa_luzia_rows[0].get("municipioIbge") or "") != "3157807":
        raise SystemExit(f"api municipio filter 3157807 failed: {santa_luzia_rows}")
    nova_friburgo = get_json(f"{API}/api/orgaos?municipioIbge=3303401&skip=0&take=50")
    deny_flags(nova_friburgo, f"{API}/api/orgaos?municipioIbge=3303401")
    nova_friburgo_rows = nova_friburgo.get("items") or []
    if len(nova_friburgo_rows) != 1 or str(nova_friburgo_rows[0].get("municipioIbge") or "") != "3303401":
        raise SystemExit(f"api municipio filter 3303401 failed: {nova_friburgo_rows}")

    orgao = by_ibge["3306305"]
    oid = orgao["id"]
    got = get_json(f"{API}/api/orgaos/{oid}")
    deny_flags(got, f"{API}/api/orgaos/{oid}")
    deny_stub(json.dumps(got, ensure_ascii=False), "api get orgao")
    if str(got.get("id") or got.get("orgao", {}).get("id") or "") != str(oid):
        raise SystemExit("api get orgao id mismatch")

    items = get_json(f"{API}/api/items?skip=0&take=50")
    deny_flags(items, f"{API}/api/items")
    deny_stub(json.dumps(items, ensure_ascii=False), "api /api/items")
    coverage = items.get("coverage") or {}
    n = coverage.get("n")
    if not isinstance(n, int) or n < 1:
        raise SystemExit(f"api items coverage.n missing or empty: {coverage}")
    if coverage.get("uf") not in (None, ""):
        raise SystemExit(f"mixed item list invented a UF: {coverage}")
    if not coverage.get("methodologyVersion"):
        raise SystemExit(f"api items coverage missing methodologyVersion: {coverage}")
    rows = items.get("items") or []
    if not rows:
        raise SystemExit("api /api/items returned no rows")
    canons = [row.get("unidadeCanonica") for row in rows]
    if all(v in (None, "") for v in canons):
        raise SystemExit("api items unidadeCanonica always null")
    base_prices = [row.get("valorPorUnidadeCanonica") for row in rows]
    if "valorPorUnidadeCanonica" not in rows[0]:
        raise SystemExit("api items missing valorPorUnidadeCanonica")
    if all(v is None for v in base_prices):
        raise SystemExit("api items valorPorUnidadeCanonica always null")
    mapped = {
        str(row.get("unidadeMedida") or "").upper(): str(row.get("unidadeCanonica") or "")
        for row in rows
    }
    if mapped.get("CX") != "cx" and mapped.get("KG") != "kg":
        raise SystemExit(f"api items missing CX/KG canonical map: {mapped}")
    unknown = [row for row in rows if str(row.get("unidadeMedida") or "").upper() == "FOOBAR"]
    if unknown and str(unknown[0].get("unidadeCanonica") or "") != "unknown":
        raise SystemExit(f"api invented a unit for FOOBAR: {unknown[0].get('unidadeCanonica')}")
    if unknown and unknown[0].get("valorPorUnidadeCanonica") is not None:
        raise SystemExit("api invented a base price for unknown unit")
    ufs = {str(row.get("uf") or "") for row in rows}
    if ufs != {"RJ", "SP", "RS", "SC", "MG", "PR", "BA", "PE", "GO", "ES", "PB", "CE", "MA", "AL", "MS", "PA", "MT", "RO", "RN", "AC", "AP", "RR"}:
        raise SystemExit(f"api items UF set is not RJ+SP+RS+SC+MG+PR+BA+PE+GO+ES+PB+CE+MA+AL+MS+PA+MT+RO+RN+AC+AP+RR: {sorted(ufs)}")
    iid = rows[0]["id"]
    item = get_json(f"{API}/api/items/{iid}")
    deny_flags(item, f"{API}/api/items/{iid}")
    deny_stub(json.dumps(item, ensure_ascii=False), "api get item")

    fornecedores = get_json(f"{API}/api/fornecedores?skip=0&take=50")
    deny_flags(fornecedores, f"{API}/api/fornecedores")
    deny_stub(json.dumps(fornecedores, ensure_ascii=False), "api /api/fornecedores")
    fornecedor_rows = fornecedores.get("items") or []
    if not fornecedor_rows:
        raise SystemExit("api /api/fornecedores returned no rows")
    fid = fornecedor_rows[0]["id"]

    contratacoes = get_json(f"{API}/api/contratacoes?skip=0&take=50")
    deny_flags(contratacoes, f"{API}/api/contratacoes")
    deny_stub(json.dumps(contratacoes, ensure_ascii=False), "api /api/contratacoes")
    contratacao_rows = contratacoes.get("items") or []
    if not contratacao_rows:
        raise SystemExit("api /api/contratacoes returned no rows")
    cid = contratacao_rows[0]["id"]

    by_fornecedor = get_json(f"{API}/api/contratacoes?skip=0&take=50&fornecedorId={fid}")
    deny_flags(by_fornecedor, f"{API}/api/contratacoes?fornecedorId")
    if not (by_fornecedor.get("items") or []):
        raise SystemExit("api /api/contratacoes?fornecedorId returned no rows")

    home = get_text(f"{WEB}/")
    assert_served_page(home, "web /")
    folded = home.casefold()
    if "volta redonda" not in folded:
        raise SystemExit("web / missing Volta Redonda")
    if "niter" not in folded:
        raise SystemExit("web / missing Niterói")
    if "bauru" not in folded:
        raise SystemExit("web / missing Bauru")
    if "caxias do sul" not in folded:
        raise SystemExit("web / missing Caxias do Sul")
    if "joinville" not in folded:
        raise SystemExit("web / missing Joinville")
    if "uberl" not in folded:
        raise SystemExit("web / missing Uberlândia")
    if "londrina" not in folded:
        raise SystemExit("web / missing Londrina")
    if "feira de santana" not in folded:
        raise SystemExit("web / missing Feira de Santana")
    if "caruaru" not in folded:
        raise SystemExit("web / missing Caruaru")
    if "anapolis" not in folded and "anápolis" not in folded:
        raise SystemExit("web / missing Anápolis")
    if "vila velha" not in folded:
        raise SystemExit("web / missing Vila Velha")
    if "campina grande" not in folded:
        raise SystemExit("web / missing Campina Grande")
    if "caucaia" not in folded:
        raise SystemExit("web / missing Caucaia")
    if "imperatriz" not in folded:
        raise SystemExit("web / missing Imperatriz")
    if "arapiraca" not in folded:
        raise SystemExit("web / missing Arapiraca")
    if "dourados" not in folded:
        raise SystemExit("web / missing Dourados")
    if "maraba" not in folded and "marabá" not in folded:
        raise SystemExit("web / missing Marabá")
    if "varzea grande" not in folded and "várzea grande" not in folded:
        raise SystemExit("web / missing Várzea Grande")
    if "ji-parana" not in folded and "ji-paraná" not in folded:
        raise SystemExit("web / missing Ji-Paraná")
    if "parnamirim" not in folded:
        raise SystemExit("web / missing Parnamirim")
    if "cruzeiro do sul" not in folded:
        raise SystemExit("web / missing Cruzeiro do Sul")
    if "santana (ap)" not in folded:
        raise SystemExit("web / missing Santana")
    if "rorainopolis" not in folded and "rorainópolis" not in folded:
        raise SystemExit("web / missing Rorainópolis")
    if "maringa" not in folded and "maringá" not in folded:
        raise SystemExit("web / missing Maringá")
    if "taubate" not in folded and "taubaté" not in folded:
        raise SystemExit("web / missing Taubaté")
    if "cascavel" not in folded:
        raise SystemExit("web / missing Cascavel")
    if "juiz de fora" not in folded:
        raise SystemExit("web / missing Juiz de Fora")
    if "foz do iguacu" not in folded and "foz do iguaçu" not in folded:
        raise SystemExit("web / missing Foz do Iguaçu")
    if "santa maria" not in folded:
        raise SystemExit("web / missing Santa Maria")
    if "montes claros" not in folded:
        raise SystemExit("web / missing Montes Claros")
    if "governador valadares" not in folded:
        raise SystemExit("web / missing Governador Valadares")
    if "canoas" not in folded:
        raise SystemExit("web / missing Canoas")
    if "lages" not in folded:
        raise SystemExit("web / missing Lages")
    if "santarem" not in folded and "santarém" not in folded:
        raise SystemExit("web / missing Santarém")
    if "rio verde" not in folded:
        raise SystemExit("web / missing Rio Verde")
    if "paulo afonso" not in folded:
        raise SystemExit("web / missing Paulo Afonso")
    if "sao lourenco da mata" not in folded and "são lourenço da mata" not in folded:
        raise SystemExit("web / missing São Lourenço da Mata")
    if "crato" not in folded:
        raise SystemExit("web / missing Crato")
    if "ariquemes" not in folded:
        raise SystemExit("web / missing Ariquemes")
    if "colatina" not in folded:
        raise SystemExit("web / missing Colatina")
    if "castanhal" not in folded:
        raise SystemExit("web / missing Castanhal")
    if "divinopolis" not in folded and "divinópolis" not in folded:
        raise SystemExit("web / missing Divinópolis")
    if "petropolis" not in folded and "petrópolis" not in folded:
        raise SystemExit("web / missing Petrópolis")
    if "ipatinga" not in folded:
        raise SystemExit("web / missing Ipatinga")
    if "macae" not in folded and "macaé" not in folded:
        raise SystemExit("web / missing Macaé")
    if "santa luzia" not in folded:
        raise SystemExit("web / missing Santa Luzia")
    if "nova friburgo" not in folded:
        raise SystemExit("web / missing Nova Friburgo")
    if "UF mista" not in home:
        raise SystemExit("web / missing honest mixed UF")
    if "Quarenta e sete municípios" not in home:
        raise SystemExit("web / missing short brand kicker")
    if "UF Brasil" in home or "total nacional" in folded:
        raise SystemExit("web / invented a national total")

    orgaos_html = get_text(f"{WEB}/orgaos?take=100")
    assert_served_page(orgaos_html, "web /orgaos")
    orgaos_fold = orgaos_html.casefold()
    if "volta redonda" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Volta Redonda")
    if "niter" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Niterói")
    if "bauru" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Bauru")
    if "caxias do sul" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Caxias do Sul")
    if "joinville" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Joinville")
    if "uberl" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Uberlândia")
    if "londrina" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Londrina")
    if "feira de santana" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Feira de Santana")
    if "caruaru" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Caruaru")
    if "anapolis" not in orgaos_fold and "anápolis" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Anápolis")
    if "vila velha" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Vila Velha")
    if "campina grande" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Campina Grande")
    if "caucaia" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Caucaia")
    if "imperatriz" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Imperatriz")
    if "arapiraca" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Arapiraca")
    if "dourados" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Dourados")
    if "maraba" not in orgaos_fold and "marabá" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Marabá")
    if "varzea grande" not in orgaos_fold and "várzea grande" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Várzea Grande")
    if "ji-parana" not in orgaos_fold and "ji-paraná" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Ji-Paraná")
    if "parnamirim" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Parnamirim")
    if "cruzeiro do sul" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Cruzeiro do Sul")
    if "municipio de santana" not in orgaos_fold and "município de santana" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Santana")
    if "rorainopolis" not in orgaos_fold and "rorainópolis" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Rorainópolis")
    if "maringa" not in orgaos_fold and "maringá" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Maringá")
    if "taubate" not in orgaos_fold and "taubaté" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Taubaté")
    if "cascavel" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Cascavel")
    if "juiz de fora" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Juiz de Fora")
    if "foz do iguacu" not in orgaos_fold and "foz do iguaçu" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Foz do Iguaçu")
    if "santa maria" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Santa Maria")
    if "montes claros" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Montes Claros")
    if "governador valadares" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Governador Valadares")
    if "canoas" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Canoas")
    if "lages" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Lages")
    if "santarem" not in orgaos_fold and "santarém" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Santarém")
    if "rio verde" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Rio Verde")
    if "paulo afonso" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Paulo Afonso")
    if "sao lourenco da mata" not in orgaos_fold and "são lourenço da mata" not in orgaos_fold:
        raise SystemExit("web /orgaos missing São Lourenço da Mata")
    if "crato" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Crato")
    if "ariquemes" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Ariquemes")
    if "colatina" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Colatina")
    if "castanhal" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Castanhal")
    if "divinopolis" not in orgaos_fold and "divinópolis" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Divinópolis")
    if "petropolis" not in orgaos_fold and "petrópolis" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Petrópolis")
    if "ipatinga" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Ipatinga")
    if "macae" not in orgaos_fold and "macaé" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Macaé")
    if "santa luzia" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Santa Luzia")
    if "nova friburgo" not in orgaos_fold:
        raise SystemExit("web /orgaos missing Nova Friburgo")
    if "UF mista" not in orgaos_html:
        raise SystemExit("web /orgaos missing honest mixed UF")

    niteroi_html = get_text(f"{WEB}/orgaos?municipioIbge=3303302")
    assert_served_page(niteroi_html, "web /orgaos?municipioIbge=3303302")
    niteroi_table = table_html(niteroi_html)
    if "niteroi" not in niteroi_table.casefold() and "niterói" not in niteroi_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3303302 missing Niterói")
    if "prefeitura municipal de bauru" in niteroi_table.casefold():
        raise SystemExit("web municipio filter leaked Bauru")
    if "prefeitura municipal de volta redonda" in niteroi_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", niteroi_html):
        raise SystemExit("web municipio filter missing n=1")
    if "UF RJ" not in niteroi_html:
        raise SystemExit("web municipio filter missing UF RJ")

    sp_html = get_text(f"{WEB}/orgaos?uf=SP")
    assert_served_page(sp_html, "web /orgaos?uf=SP")
    sp_table = table_html(sp_html)
    if "bauru" not in sp_table.casefold():
        raise SystemExit("web /orgaos?uf=SP missing Bauru")
    if "prefeitura municipal de volta redonda" in sp_table.casefold():
        raise SystemExit("web UF=SP filter leaked Volta Redonda")
    if "prefeitura municipal de niter" in sp_table.casefold():
        raise SystemExit("web UF=SP filter leaked Niterói")
    if "UF SP" not in sp_html:
        raise SystemExit("web UF=SP missing coverage UF")

    caxias_html = get_text(f"{WEB}/orgaos?municipioIbge=4305108")
    assert_served_page(caxias_html, "web /orgaos?municipioIbge=4305108")
    caxias_table = table_html(caxias_html)
    if "caxias do sul" not in caxias_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=4305108 missing Caxias do Sul")
    if "municipio de joinville" in caxias_table.casefold():
        raise SystemExit("web municipio filter leaked Joinville")
    if "prefeitura municipal de volta redonda" in caxias_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", caxias_html):
        raise SystemExit("web Caxias filter missing n=1")
    if "UF RS" not in caxias_html:
        raise SystemExit("web Caxias filter missing UF RS")

    sc_html = get_text(f"{WEB}/orgaos?uf=SC")
    assert_served_page(sc_html, "web /orgaos?uf=SC")
    sc_table = table_html(sc_html)
    if "joinville" not in sc_table.casefold():
        raise SystemExit("web /orgaos?uf=SC missing Joinville")
    if "lages" not in sc_table.casefold():
        raise SystemExit("web /orgaos?uf=SC missing Lages")
    if "municipio de caxias do sul" in sc_table.casefold():
        raise SystemExit("web UF=SC filter leaked Caxias do Sul")
    if "prefeitura municipal de volta redonda" in sc_table.casefold():
        raise SystemExit("web UF=SC filter leaked Volta Redonda")
    if "UF SC" not in sc_html:
        raise SystemExit("web UF=SC missing coverage UF")

    uberlandia_html = get_text(f"{WEB}/orgaos?municipioIbge=3170206")
    assert_served_page(uberlandia_html, "web /orgaos?municipioIbge=3170206")
    uberlandia_table = table_html(uberlandia_html)
    if "uberl" not in uberlandia_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3170206 missing Uberlândia")
    if "municipio de londrina" in uberlandia_table.casefold():
        raise SystemExit("web municipio filter leaked Londrina")
    if "prefeitura municipal de volta redonda" in uberlandia_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", uberlandia_html):
        raise SystemExit("web Uberlândia filter missing n=1")
    if "UF MG" not in uberlandia_html:
        raise SystemExit("web Uberlândia filter missing UF MG")

    pr_html = get_text(f"{WEB}/orgaos?uf=PR")
    assert_served_page(pr_html, "web /orgaos?uf=PR")
    pr_table = table_html(pr_html)
    if "londrina" not in pr_table.casefold():
        raise SystemExit("web /orgaos?uf=PR missing Londrina")
    if "municipio de uberlandia" in pr_table.casefold():
        raise SystemExit("web UF=PR filter leaked Uberlândia")
    if "prefeitura municipal de volta redonda" in pr_table.casefold():
        raise SystemExit("web UF=PR filter leaked Volta Redonda")
    if "UF PR" not in pr_html:
        raise SystemExit("web UF=PR missing coverage UF")

    feira_html = get_text(f"{WEB}/orgaos?municipioIbge=2910800")
    assert_served_page(feira_html, "web /orgaos?municipioIbge=2910800")
    feira_table = table_html(feira_html)
    if "feira de santana" not in feira_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=2910800 missing Feira de Santana")
    if "municipio de caruaru" in feira_table.casefold():
        raise SystemExit("web municipio filter leaked Caruaru")
    if "prefeitura municipal de volta redonda" in feira_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", feira_html):
        raise SystemExit("web Feira de Santana filter missing n=1")
    if "UF BA" not in feira_html:
        raise SystemExit("web Feira de Santana filter missing UF BA")

    pe_html = get_text(f"{WEB}/orgaos?uf=PE")
    assert_served_page(pe_html, "web /orgaos?uf=PE")
    pe_table = table_html(pe_html)
    if "caruaru" not in pe_table.casefold():
        raise SystemExit("web /orgaos?uf=PE missing Caruaru")
    if "sao lourenco da mata" not in pe_table.casefold() and "são lourenço da mata" not in pe_table.casefold():
        raise SystemExit("web /orgaos?uf=PE missing São Lourenço da Mata")
    if "municipio de feira de santana" in pe_table.casefold():
        raise SystemExit("web UF=PE filter leaked Feira de Santana")
    if "prefeitura municipal de volta redonda" in pe_table.casefold():
        raise SystemExit("web UF=PE filter leaked Volta Redonda")
    if not re.search(r"n=2", pe_html):
        raise SystemExit("web UF=PE filter missing n=2")
    if "UF PE" not in pe_html:
        raise SystemExit("web UF=PE missing coverage UF")

    anapolis_html = get_text(f"{WEB}/orgaos?municipioIbge=5201108")
    assert_served_page(anapolis_html, "web /orgaos?municipioIbge=5201108")
    anapolis_table = table_html(anapolis_html)
    if "anapolis" not in anapolis_table.casefold() and "anápolis" not in anapolis_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=5201108 missing Anápolis")
    if "municipio de vila velha" in anapolis_table.casefold():
        raise SystemExit("web municipio filter leaked Vila Velha")
    if "prefeitura municipal de volta redonda" in anapolis_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", anapolis_html):
        raise SystemExit("web Anápolis filter missing n=1")
    if "UF GO" not in anapolis_html:
        raise SystemExit("web Anápolis filter missing UF GO")

    es_html = get_text(f"{WEB}/orgaos?uf=ES")
    assert_served_page(es_html, "web /orgaos?uf=ES")
    es_table = table_html(es_html)
    if "vila velha" not in es_table.casefold():
        raise SystemExit("web /orgaos?uf=ES missing Vila Velha")
    if "colatina" not in es_table.casefold():
        raise SystemExit("web /orgaos?uf=ES missing Colatina")
    if "municipio de anapolis" in es_table.casefold() or "município de anápolis" in es_table.casefold():
        raise SystemExit("web UF=ES filter leaked Anápolis")
    if "prefeitura municipal de volta redonda" in es_table.casefold():
        raise SystemExit("web UF=ES filter leaked Volta Redonda")
    if "UF ES" not in es_html:
        raise SystemExit("web UF=ES missing coverage UF")

    campina_html = get_text(f"{WEB}/orgaos?municipioIbge=2504009")
    assert_served_page(campina_html, "web /orgaos?municipioIbge=2504009")
    campina_table = table_html(campina_html)
    if "campina grande" not in campina_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=2504009 missing Campina Grande")
    if "municipio de caucaia" in campina_table.casefold() or "município de caucaia" in campina_table.casefold():
        raise SystemExit("web municipio filter leaked Caucaia")
    if "prefeitura municipal de volta redonda" in campina_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", campina_html):
        raise SystemExit("web Campina Grande filter missing n=1")
    if "UF PB" not in campina_html:
        raise SystemExit("web Campina Grande filter missing UF PB")

    ce_html = get_text(f"{WEB}/orgaos?uf=CE")
    assert_served_page(ce_html, "web /orgaos?uf=CE")
    ce_table = table_html(ce_html)
    if "caucaia" not in ce_table.casefold():
        raise SystemExit("web /orgaos?uf=CE missing Caucaia")
    if "crato" not in ce_table.casefold():
        raise SystemExit("web /orgaos?uf=CE missing Crato")
    if "municipio de campina grande" in ce_table.casefold() or "município de campina grande" in ce_table.casefold():
        raise SystemExit("web UF=CE filter leaked Campina Grande")
    if "prefeitura municipal de volta redonda" in ce_table.casefold():
        raise SystemExit("web UF=CE filter leaked Volta Redonda")
    if "UF CE" not in ce_html:
        raise SystemExit("web UF=CE missing coverage UF")

    imperatriz_html = get_text(f"{WEB}/orgaos?municipioIbge=2105302")
    assert_served_page(imperatriz_html, "web /orgaos?municipioIbge=2105302")
    imperatriz_table = table_html(imperatriz_html)
    if "imperatriz" not in imperatriz_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=2105302 missing Imperatriz")
    if "municipio de arapiraca" in imperatriz_table.casefold() or "município de arapiraca" in imperatriz_table.casefold():
        raise SystemExit("web municipio filter leaked Arapiraca")
    if "prefeitura municipal de volta redonda" in imperatriz_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", imperatriz_html):
        raise SystemExit("web Imperatriz filter missing n=1")
    if "UF MA" not in imperatriz_html:
        raise SystemExit("web Imperatriz filter missing UF MA")

    al_html = get_text(f"{WEB}/orgaos?uf=AL")
    assert_served_page(al_html, "web /orgaos?uf=AL")
    al_table = table_html(al_html)
    if "arapiraca" not in al_table.casefold():
        raise SystemExit("web /orgaos?uf=AL missing Arapiraca")
    if "municipio de imperatriz" in al_table.casefold() or "município de imperatriz" in al_table.casefold():
        raise SystemExit("web UF=AL filter leaked Imperatriz")
    if "prefeitura municipal de volta redonda" in al_table.casefold():
        raise SystemExit("web UF=AL filter leaked Volta Redonda")
    if "UF AL" not in al_html:
        raise SystemExit("web UF=AL missing coverage UF")

    dourados_html = get_text(f"{WEB}/orgaos?municipioIbge=5003702")
    assert_served_page(dourados_html, "web /orgaos?municipioIbge=5003702")
    dourados_table = table_html(dourados_html)
    if "dourados" not in dourados_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=5003702 missing Dourados")
    if "municipio de maraba" in dourados_table.casefold() or "município de marabá" in dourados_table.casefold():
        raise SystemExit("web municipio filter leaked Marabá")
    if "prefeitura municipal de volta redonda" in dourados_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", dourados_html):
        raise SystemExit("web Dourados filter missing n=1")
    if "UF MS" not in dourados_html:
        raise SystemExit("web Dourados filter missing UF MS")

    pa_html = get_text(f"{WEB}/orgaos?uf=PA")
    assert_served_page(pa_html, "web /orgaos?uf=PA")
    pa_table = table_html(pa_html)
    if "maraba" not in pa_table.casefold() and "marabá" not in pa_table.casefold():
        raise SystemExit("web /orgaos?uf=PA missing Marabá")
    if "santarem" not in pa_table.casefold() and "santarém" not in pa_table.casefold():
        raise SystemExit("web /orgaos?uf=PA missing Santarém")
    if "castanhal" not in pa_table.casefold():
        raise SystemExit("web /orgaos?uf=PA missing Castanhal")
    if "fundacao de servicos de saude de dourados" in pa_table.casefold() or "fundação de serviços de saúde de dourados" in pa_table.casefold() or "municipio de dourados" in pa_table.casefold() or "município de dourados" in pa_table.casefold():
        raise SystemExit("web UF=PA filter leaked Dourados")
    if "prefeitura municipal de volta redonda" in pa_table.casefold():
        raise SystemExit("web UF=PA filter leaked Volta Redonda")
    if "UF PA" not in pa_html:
        raise SystemExit("web UF=PA missing coverage UF")

    varzea_html = get_text(f"{WEB}/orgaos?municipioIbge=5108402")
    assert_served_page(varzea_html, "web /orgaos?municipioIbge=5108402")
    varzea_table = table_html(varzea_html)
    if "varzea grande" not in varzea_table.casefold() and "várzea grande" not in varzea_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=5108402 missing Várzea Grande")
    if "municipio de ji-parana" in varzea_table.casefold() or "município de ji-paraná" in varzea_table.casefold():
        raise SystemExit("web municipio filter leaked Ji-Paraná")
    if "prefeitura municipal de volta redonda" in varzea_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", varzea_html):
        raise SystemExit("web Várzea Grande filter missing n=1")
    if "UF MT" not in varzea_html:
        raise SystemExit("web Várzea Grande filter missing UF MT")

    ro_html = get_text(f"{WEB}/orgaos?uf=RO")
    assert_served_page(ro_html, "web /orgaos?uf=RO")
    ro_table = table_html(ro_html)
    if "ji-parana" not in ro_table.casefold() and "ji-paraná" not in ro_table.casefold():
        raise SystemExit("web /orgaos?uf=RO missing Ji-Paraná")
    if "ariquemes" not in ro_table.casefold():
        raise SystemExit("web /orgaos?uf=RO missing Ariquemes")
    if "municipio de varzea grande" in ro_table.casefold() or "município de várzea grande" in ro_table.casefold():
        raise SystemExit("web UF=RO filter leaked Várzea Grande")
    if "prefeitura municipal de volta redonda" in ro_table.casefold():
        raise SystemExit("web UF=RO filter leaked Volta Redonda")
    if "UF RO" not in ro_html:
        raise SystemExit("web UF=RO missing coverage UF")

    parnamirim_html = get_text(f"{WEB}/orgaos?municipioIbge=2403251")
    assert_served_page(parnamirim_html, "web /orgaos?municipioIbge=2403251")
    parnamirim_table = table_html(parnamirim_html)
    if "parnamirim" not in parnamirim_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=2403251 missing Parnamirim")
    if "municipio de cruzeiro do sul" in parnamirim_table.casefold() or "município de cruzeiro do sul" in parnamirim_table.casefold():
        raise SystemExit("web municipio filter leaked Cruzeiro do Sul")
    if "prefeitura municipal de volta redonda" in parnamirim_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", parnamirim_html):
        raise SystemExit("web Parnamirim filter missing n=1")
    if "UF RN" not in parnamirim_html:
        raise SystemExit("web Parnamirim filter missing UF RN")

    ac_html = get_text(f"{WEB}/orgaos?uf=AC")
    assert_served_page(ac_html, "web /orgaos?uf=AC")
    ac_table = table_html(ac_html)
    if "cruzeiro do sul" not in ac_table.casefold():
        raise SystemExit("web /orgaos?uf=AC missing Cruzeiro do Sul")
    if "municipio de parnamirim" in ac_table.casefold() or "município de parnamirim" in ac_table.casefold():
        raise SystemExit("web UF=AC filter leaked Parnamirim")
    if "prefeitura municipal de volta redonda" in ac_table.casefold():
        raise SystemExit("web UF=AC filter leaked Volta Redonda")
    if "UF AC" not in ac_html:
        raise SystemExit("web UF=AC missing coverage UF")

    santana_html = get_text(f"{WEB}/orgaos?municipioIbge=1600600")
    assert_served_page(santana_html, "web /orgaos?municipioIbge=1600600")
    santana_table = table_html(santana_html)
    if "municipio de santana" not in santana_table.casefold() and "município de santana" not in santana_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=1600600 missing Santana")
    if "municipio de rorainopolis" in santana_table.casefold() or "município de rorainópolis" in santana_table.casefold():
        raise SystemExit("web municipio filter leaked Rorainópolis")
    if "prefeitura municipal de volta redonda" in santana_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", santana_html):
        raise SystemExit("web Santana filter missing n=1")
    if "UF AP" not in santana_html:
        raise SystemExit("web Santana filter missing UF AP")

    rr_html = get_text(f"{WEB}/orgaos?uf=RR")
    assert_served_page(rr_html, "web /orgaos?uf=RR")
    rr_table = table_html(rr_html)
    if "rorainopolis" not in rr_table.casefold() and "rorainópolis" not in rr_table.casefold():
        raise SystemExit("web /orgaos?uf=RR missing Rorainópolis")
    if "municipio de santana" in rr_table.casefold() or "município de santana" in rr_table.casefold():
        raise SystemExit("web UF=RR filter leaked Santana")
    if "prefeitura municipal de volta redonda" in rr_table.casefold():
        raise SystemExit("web UF=RR filter leaked Volta Redonda")
    if "UF RR" not in rr_html:
        raise SystemExit("web UF=RR missing coverage UF")

    maringa_html = get_text(f"{WEB}/orgaos?municipioIbge=4115200")
    assert_served_page(maringa_html, "web /orgaos?municipioIbge=4115200")
    maringa_table = table_html(maringa_html)
    if "municipio de maringa" not in maringa_table.casefold() and "município de maringá" not in maringa_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=4115200 missing Maringá")
    if "municipio de taubate" in maringa_table.casefold() or "município de taubaté" in maringa_table.casefold():
        raise SystemExit("web municipio filter leaked Taubaté")
    if "prefeitura municipal de volta redonda" in maringa_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", maringa_html):
        raise SystemExit("web Maringá filter missing n=1")
    if "UF PR" not in maringa_html:
        raise SystemExit("web Maringá filter missing UF PR")

    taubate_html = get_text(f"{WEB}/orgaos?municipioIbge=3554102")
    assert_served_page(taubate_html, "web /orgaos?municipioIbge=3554102")
    taubate_table = table_html(taubate_html)
    if "municipio de taubate" not in taubate_table.casefold() and "município de taubaté" not in taubate_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3554102 missing Taubaté")
    if "municipio de maringa" in taubate_table.casefold() or "município de maringá" in taubate_table.casefold():
        raise SystemExit("web municipio filter leaked Maringá")
    if "prefeitura municipal de volta redonda" in taubate_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", taubate_html):
        raise SystemExit("web Taubaté filter missing n=1")
    if "UF SP" not in taubate_html:
        raise SystemExit("web Taubaté filter missing UF SP")

    cascavel_html = get_text(f"{WEB}/orgaos?municipioIbge=4104808")
    assert_served_page(cascavel_html, "web /orgaos?municipioIbge=4104808")
    cascavel_table = table_html(cascavel_html)
    if "municipio de cascavel" not in cascavel_table.casefold() and "município de cascavel" not in cascavel_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=4104808 missing Cascavel")
    if "municipio de juiz de fora" in cascavel_table.casefold() or "município de juiz de fora" in cascavel_table.casefold():
        raise SystemExit("web municipio filter leaked Juiz de Fora")
    if "prefeitura municipal de volta redonda" in cascavel_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", cascavel_html):
        raise SystemExit("web Cascavel filter missing n=1")
    if "UF PR" not in cascavel_html:
        raise SystemExit("web Cascavel filter missing UF PR")

    juiz_html = get_text(f"{WEB}/orgaos?municipioIbge=3136702")
    assert_served_page(juiz_html, "web /orgaos?municipioIbge=3136702")
    juiz_table = table_html(juiz_html)
    if "municipio de juiz de fora" not in juiz_table.casefold() and "município de juiz de fora" not in juiz_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3136702 missing Juiz de Fora")
    if "municipio de cascavel" in juiz_table.casefold() or "município de cascavel" in juiz_table.casefold():
        raise SystemExit("web municipio filter leaked Cascavel")
    if "prefeitura municipal de volta redonda" in juiz_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", juiz_html):
        raise SystemExit("web Juiz de Fora filter missing n=1")
    if "UF MG" not in juiz_html:
        raise SystemExit("web Juiz de Fora filter missing UF MG")

    foz_html = get_text(f"{WEB}/orgaos?municipioIbge=4108304")
    assert_served_page(foz_html, "web /orgaos?municipioIbge=4108304")
    foz_table = table_html(foz_html)
    if "municipio de foz do iguacu" not in foz_table.casefold() and "município de foz do iguaçu" not in foz_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=4108304 missing Foz do Iguaçu")
    if "municipio de santa maria" in foz_table.casefold() or "município de santa maria" in foz_table.casefold():
        raise SystemExit("web municipio filter leaked Santa Maria")
    if "prefeitura municipal de volta redonda" in foz_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", foz_html):
        raise SystemExit("web Foz do Iguaçu filter missing n=1")
    if "UF PR" not in foz_html:
        raise SystemExit("web Foz do Iguaçu filter missing UF PR")

    santa_html = get_text(f"{WEB}/orgaos?municipioIbge=4316907")
    assert_served_page(santa_html, "web /orgaos?municipioIbge=4316907")
    santa_table = table_html(santa_html)
    if "municipio de santa maria" not in santa_table.casefold() and "município de santa maria" not in santa_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=4316907 missing Santa Maria")
    if "municipio de foz do iguacu" in santa_table.casefold() or "município de foz do iguaçu" in santa_table.casefold():
        raise SystemExit("web municipio filter leaked Foz do Iguaçu")
    if "prefeitura municipal de volta redonda" in santa_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", santa_html):
        raise SystemExit("web Santa Maria filter missing n=1")
    if "UF RS" not in santa_html:
        raise SystemExit("web Santa Maria filter missing UF RS")

    montes_html = get_text(f"{WEB}/orgaos?municipioIbge=3143302")
    assert_served_page(montes_html, "web /orgaos?municipioIbge=3143302")
    montes_table = table_html(montes_html)
    if "municipio de montes claros" not in montes_table.casefold() and "município de montes claros" not in montes_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3143302 missing Montes Claros")
    if "municipio de governador valadares" in montes_table.casefold() or "município de governador valadares" in montes_table.casefold():
        raise SystemExit("web municipio filter leaked Governador Valadares")
    if "prefeitura municipal de volta redonda" in montes_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", montes_html):
        raise SystemExit("web Montes Claros filter missing n=1")
    if "UF MG" not in montes_html:
        raise SystemExit("web Montes Claros filter missing UF MG")

    valadares_html = get_text(f"{WEB}/orgaos?municipioIbge=3127701")
    assert_served_page(valadares_html, "web /orgaos?municipioIbge=3127701")
    valadares_table = table_html(valadares_html)
    if "municipio de governador valadares" not in valadares_table.casefold() and "município de governador valadares" not in valadares_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3127701 missing Governador Valadares")
    if "municipio de montes claros" in valadares_table.casefold() or "município de montes claros" in valadares_table.casefold():
        raise SystemExit("web municipio filter leaked Montes Claros")
    if "prefeitura municipal de volta redonda" in valadares_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", valadares_html):
        raise SystemExit("web Governador Valadares filter missing n=1")
    if "UF MG" not in valadares_html:
        raise SystemExit("web Governador Valadares filter missing UF MG")

    canoas_html = get_text(f"{WEB}/orgaos?municipioIbge=4304606")
    assert_served_page(canoas_html, "web /orgaos?municipioIbge=4304606")
    canoas_table = table_html(canoas_html)
    if "municipio de canoas" not in canoas_table.casefold() and "município de canoas" not in canoas_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=4304606 missing Canoas")
    if "municipio de lages" in canoas_table.casefold() or "município de lages" in canoas_table.casefold():
        raise SystemExit("web municipio filter leaked Lages")
    if "prefeitura municipal de volta redonda" in canoas_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", canoas_html):
        raise SystemExit("web Canoas filter missing n=1")
    if "UF RS" not in canoas_html:
        raise SystemExit("web Canoas filter missing UF RS")

    lages_html = get_text(f"{WEB}/orgaos?municipioIbge=4209300")
    assert_served_page(lages_html, "web /orgaos?municipioIbge=4209300")
    lages_table = table_html(lages_html)
    if "municipio de lages" not in lages_table.casefold() and "município de lages" not in lages_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=4209300 missing Lages")
    if "municipio de canoas" in lages_table.casefold() or "município de canoas" in lages_table.casefold():
        raise SystemExit("web municipio filter leaked Canoas")
    if "prefeitura municipal de volta redonda" in lages_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", lages_html):
        raise SystemExit("web Lages filter missing n=1")
    if "UF SC" not in lages_html:
        raise SystemExit("web Lages filter missing UF SC")

    santarem_html = get_text(f"{WEB}/orgaos?municipioIbge=1506807")
    assert_served_page(santarem_html, "web /orgaos?municipioIbge=1506807")
    santarem_table = table_html(santarem_html)
    if "municipio de santarem" not in santarem_table.casefold() and "município de santarém" not in santarem_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=1506807 missing Santarém")
    if "municipio de rio verde" in santarem_table.casefold() or "município de rio verde" in santarem_table.casefold():
        raise SystemExit("web municipio filter leaked Rio Verde")
    if "prefeitura municipal de volta redonda" in santarem_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", santarem_html):
        raise SystemExit("web Santarém filter missing n=1")
    if "UF PA" not in santarem_html:
        raise SystemExit("web Santarém filter missing UF PA")

    rio_verde_html = get_text(f"{WEB}/orgaos?municipioIbge=5218805")
    assert_served_page(rio_verde_html, "web /orgaos?municipioIbge=5218805")
    rio_verde_table = table_html(rio_verde_html)
    if "municipio de rio verde" not in rio_verde_table.casefold() and "município de rio verde" not in rio_verde_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=5218805 missing Rio Verde")
    if "municipio de santarem" in rio_verde_table.casefold() or "município de santarém" in rio_verde_table.casefold():
        raise SystemExit("web municipio filter leaked Santarém")
    if "prefeitura municipal de volta redonda" in rio_verde_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", rio_verde_html):
        raise SystemExit("web Rio Verde filter missing n=1")
    if "UF GO" not in rio_verde_html:
        raise SystemExit("web Rio Verde filter missing UF GO")

    paulo_afonso_html = get_text(f"{WEB}/orgaos?municipioIbge=2924009")
    assert_served_page(paulo_afonso_html, "web /orgaos?municipioIbge=2924009")
    paulo_afonso_table = table_html(paulo_afonso_html)
    if "municipio de paulo afonso" not in paulo_afonso_table.casefold() and "município de paulo afonso" not in paulo_afonso_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=2924009 missing Paulo Afonso")
    if "municipio de sao lourenco da mata" in paulo_afonso_table.casefold() or "município de são lourenço da mata" in paulo_afonso_table.casefold():
        raise SystemExit("web municipio filter leaked São Lourenço da Mata")
    if "prefeitura municipal de volta redonda" in paulo_afonso_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", paulo_afonso_html):
        raise SystemExit("web Paulo Afonso filter missing n=1")
    if "UF BA" not in paulo_afonso_html:
        raise SystemExit("web Paulo Afonso filter missing UF BA")

    sao_lourenco_html = get_text(f"{WEB}/orgaos?municipioIbge=2613701")
    assert_served_page(sao_lourenco_html, "web /orgaos?municipioIbge=2613701")
    sao_lourenco_table = table_html(sao_lourenco_html)
    if "municipio de sao lourenco da mata" not in sao_lourenco_table.casefold() and "município de são lourenço da mata" not in sao_lourenco_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=2613701 missing São Lourenço da Mata")
    if "municipio de paulo afonso" in sao_lourenco_table.casefold() or "município de paulo afonso" in sao_lourenco_table.casefold():
        raise SystemExit("web municipio filter leaked Paulo Afonso")
    if "prefeitura municipal de volta redonda" in sao_lourenco_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", sao_lourenco_html):
        raise SystemExit("web São Lourenço da Mata filter missing n=1")
    if "UF PE" not in sao_lourenco_html:
        raise SystemExit("web São Lourenço da Mata filter missing UF PE")

    crato_html = get_text(f"{WEB}/orgaos?municipioIbge=2304202")
    assert_served_page(crato_html, "web /orgaos?municipioIbge=2304202")
    crato_table = table_html(crato_html)
    if "municipio de crato" not in crato_table.casefold() and "município de crato" not in crato_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=2304202 missing Crato")
    if "municipio de ariquemes" in crato_table.casefold() or "município de ariquemes" in crato_table.casefold():
        raise SystemExit("web municipio filter leaked Ariquemes")
    if "prefeitura municipal de volta redonda" in crato_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", crato_html):
        raise SystemExit("web Crato filter missing n=1")
    if "UF CE" not in crato_html:
        raise SystemExit("web Crato filter missing UF CE")

    ariquemes_html = get_text(f"{WEB}/orgaos?municipioIbge=1100023")
    assert_served_page(ariquemes_html, "web /orgaos?municipioIbge=1100023")
    ariquemes_table = table_html(ariquemes_html)
    if "municipio de ariquemes" not in ariquemes_table.casefold() and "município de ariquemes" not in ariquemes_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=1100023 missing Ariquemes")
    if "municipio de crato" in ariquemes_table.casefold() or "município de crato" in ariquemes_table.casefold():
        raise SystemExit("web municipio filter leaked Crato")
    if "prefeitura municipal de volta redonda" in ariquemes_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", ariquemes_html):
        raise SystemExit("web Ariquemes filter missing n=1")
    if "UF RO" not in ariquemes_html:
        raise SystemExit("web Ariquemes filter missing UF RO")

    colatina_html = get_text(f"{WEB}/orgaos?municipioIbge=3201506")
    assert_served_page(colatina_html, "web /orgaos?municipioIbge=3201506")
    colatina_table = table_html(colatina_html)
    if "municipio de colatina" not in colatina_table.casefold() and "município de colatina" not in colatina_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3201506 missing Colatina")
    if "municipio de castanhal" in colatina_table.casefold() or "município de castanhal" in colatina_table.casefold():
        raise SystemExit("web municipio filter leaked Castanhal")
    if "prefeitura municipal de volta redonda" in colatina_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", colatina_html):
        raise SystemExit("web Colatina filter missing n=1")
    if "UF ES" not in colatina_html:
        raise SystemExit("web Colatina filter missing UF ES")

    castanhal_html = get_text(f"{WEB}/orgaos?municipioIbge=1502400")
    assert_served_page(castanhal_html, "web /orgaos?municipioIbge=1502400")
    castanhal_table = table_html(castanhal_html)
    if "municipio de castanhal" not in castanhal_table.casefold() and "município de castanhal" not in castanhal_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=1502400 missing Castanhal")
    if "municipio de colatina" in castanhal_table.casefold() or "município de colatina" in castanhal_table.casefold():
        raise SystemExit("web municipio filter leaked Colatina")
    if "prefeitura municipal de volta redonda" in castanhal_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", castanhal_html):
        raise SystemExit("web Castanhal filter missing n=1")
    if "UF PA" not in castanhal_html:
        raise SystemExit("web Castanhal filter missing UF PA")

    divinopolis_html = get_text(f"{WEB}/orgaos?municipioIbge=3122306")
    assert_served_page(divinopolis_html, "web /orgaos?municipioIbge=3122306")
    divinopolis_table = table_html(divinopolis_html)
    if "municipio de divinopolis" not in divinopolis_table.casefold() and "município de divinópolis" not in divinopolis_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3122306 missing Divinópolis")
    if "municipio de petropolis" in divinopolis_table.casefold() or "município de petrópolis" in divinopolis_table.casefold():
        raise SystemExit("web municipio filter leaked Petrópolis")
    if "prefeitura municipal de volta redonda" in divinopolis_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", divinopolis_html):
        raise SystemExit("web Divinópolis filter missing n=1")
    if "UF MG" not in divinopolis_html:
        raise SystemExit("web Divinópolis filter missing UF MG")

    petropolis_html = get_text(f"{WEB}/orgaos?municipioIbge=3303906")
    assert_served_page(petropolis_html, "web /orgaos?municipioIbge=3303906")
    petropolis_table = table_html(petropolis_html)
    if "municipio de petropolis" not in petropolis_table.casefold() and "município de petrópolis" not in petropolis_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3303906 missing Petrópolis")
    if "municipio de divinopolis" in petropolis_table.casefold() or "município de divinópolis" in petropolis_table.casefold():
        raise SystemExit("web municipio filter leaked Divinópolis")
    if "prefeitura municipal de volta redonda" in petropolis_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", petropolis_html):
        raise SystemExit("web Petrópolis filter missing n=1")
    if "UF RJ" not in petropolis_html:
        raise SystemExit("web Petrópolis filter missing UF RJ")

    ipatinga_html = get_text(f"{WEB}/orgaos?municipioIbge=3131307")
    assert_served_page(ipatinga_html, "web /orgaos?municipioIbge=3131307")
    ipatinga_table = table_html(ipatinga_html)
    if "municipio de ipatinga" not in ipatinga_table.casefold() and "município de ipatinga" not in ipatinga_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3131307 missing Ipatinga")
    if "municipio de macae" in ipatinga_table.casefold() or "município de macaé" in ipatinga_table.casefold():
        raise SystemExit("web municipio filter leaked Macaé")
    if "prefeitura municipal de volta redonda" in ipatinga_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", ipatinga_html):
        raise SystemExit("web Ipatinga filter missing n=1")
    if "UF MG" not in ipatinga_html:
        raise SystemExit("web Ipatinga filter missing UF MG")

    macae_html = get_text(f"{WEB}/orgaos?municipioIbge=3302403")
    assert_served_page(macae_html, "web /orgaos?municipioIbge=3302403")
    macae_table = table_html(macae_html)
    if "municipio de macae" not in macae_table.casefold() and "município de macaé" not in macae_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3302403 missing Macaé")
    if "municipio de ipatinga" in macae_table.casefold() or "município de ipatinga" in macae_table.casefold():
        raise SystemExit("web municipio filter leaked Ipatinga")
    if "prefeitura municipal de volta redonda" in macae_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", macae_html):
        raise SystemExit("web Macaé filter missing n=1")
    if "UF RJ" not in macae_html:
        raise SystemExit("web Macaé filter missing UF RJ")

    santa_luzia_html = get_text(f"{WEB}/orgaos?municipioIbge=3157807")
    assert_served_page(santa_luzia_html, "web /orgaos?municipioIbge=3157807")
    santa_luzia_table = table_html(santa_luzia_html)
    if "municipio de santa luzia" not in santa_luzia_table.casefold() and "município de santa luzia" not in santa_luzia_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3157807 missing Santa Luzia")
    if "municipio de nova friburgo" in santa_luzia_table.casefold() or "município de nova friburgo" in santa_luzia_table.casefold():
        raise SystemExit("web municipio filter leaked Nova Friburgo")
    if "prefeitura municipal de volta redonda" in santa_luzia_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", santa_luzia_html):
        raise SystemExit("web Santa Luzia filter missing n=1")
    if "UF MG" not in santa_luzia_html:
        raise SystemExit("web Santa Luzia filter missing UF MG")

    nova_friburgo_html = get_text(f"{WEB}/orgaos?municipioIbge=3303401")
    assert_served_page(nova_friburgo_html, "web /orgaos?municipioIbge=3303401")
    nova_friburgo_table = table_html(nova_friburgo_html)
    if "municipio de nova friburgo" not in nova_friburgo_table.casefold() and "município de nova friburgo" not in nova_friburgo_table.casefold():
        raise SystemExit("web /orgaos?municipioIbge=3303401 missing Nova Friburgo")
    if "municipio de santa luzia" in nova_friburgo_table.casefold() or "município de santa luzia" in nova_friburgo_table.casefold():
        raise SystemExit("web municipio filter leaked Santa Luzia")
    if "prefeitura municipal de volta redonda" in nova_friburgo_table.casefold():
        raise SystemExit("web municipio filter leaked Volta Redonda")
    if not re.search(r"n=1", nova_friburgo_html):
        raise SystemExit("web Nova Friburgo filter missing n=1")
    if "UF RJ" not in nova_friburgo_html:
        raise SystemExit("web Nova Friburgo filter missing UF RJ")

    orgao_html = get_text(f"{WEB}/orgaos/{oid}")
    assert_served_page(orgao_html, "web /orgaos/{id}")
    if STAT_HOMOLOGADO.search(orgao_html):
        raise SystemExit("web /orgaos/{id} used Homologado as a slice total")
    if "volta redonda" not in orgao_html.casefold():
        raise SystemExit("web /orgaos/{id} missing Volta Redonda")

    fornecedor_html = get_text(f"{WEB}/fornecedores/{fid}")
    assert_served_page(fornecedor_html, "web /fornecedores/{id}")
    if STAT_HOMOLOGADO.search(fornecedor_html):
        raise SystemExit("web /fornecedores/{id} used Homologado as a slice total")

    contratacao_html = get_text(f"{WEB}/contratacoes/{cid}")
    assert_served_page(contratacao_html, "web /contratacoes/{id}")
    if not STAT_HOMOLOGADO.search(contratacao_html):
        raise SystemExit("web /contratacoes/{id} missing Homologado on the contratação")
    if not re.search(r"R\$\s*[\d.]+,\d{2}", contratacao_html):
        raise SystemExit("web /contratacoes/{id} missing money")
    if not re.search(r"\d{2}/\d{2}/\d{4}", contratacao_html):
        raise SystemExit("web /contratacoes/{id} missing date")

    item_html = get_text(f"{WEB}/itens/{iid}")
    assert_served_page(item_html, "web /itens/{id}")
    if not re.search(r"R\$\s*[\d.]+,\d{2}", item_html):
        raise SystemExit("web /itens/{id} missing money")
    mapped_row = next((row for row in rows if row.get("valorPorUnidadeCanonica") is not None), None)
    if mapped_row is None:
        raise SystemExit("api items missing a warehouse base price to prove the item page")
    mapped_html = get_text(f"{WEB}/itens/{mapped_row['id']}")
    assert_served_page(mapped_html, "web mapped item")
    if "Valor por" not in mapped_html:
        raise SystemExit("web mapped item hid the warehouse base price")
    canon = str(mapped_row.get("unidadeCanonica") or "")
    if not canon or canon == "unknown" or canon not in mapped_html:
        raise SystemExit(f"web mapped item missing canonical unit {canon}")
    unknown_page = get_json(f"{API}/api/items?q=CONHECIDA&skip=0&take=20")
    unknown_row = next(
        (row for row in (unknown_page.get("items") or []) if str(row.get("unidadeCanonica") or "") == "unknown"),
        None,
    )
    if unknown_row is None:
        raise SystemExit("api missing unknown-unit item (LOTE AVULSO / FOOBAR)")
    unknown_html = get_text(f"{WEB}/itens/{unknown_row['id']}")
    assert_served_page(unknown_html, "web unknown item")
    if "não mapeada" not in unknown_html:
        raise SystemExit("web unknown item missing não mapeada")
    if re.search(r'class="kicker">Valor por', unknown_html):
        raise SystemExit("web unknown item invented a base-price stat")
    if re.search(r"\bunknown\b", unknown_html):
        raise SystemExit("web leaked the warehouse unknown token")

    paged = get_text(f"{WEB}/orgaos?uf=RJ&take=1")
    assert_served_page(paged, "web /orgaos?uf=RJ&take=1")
    next_href = re.search(r'<a href="([^"]+)">Próxima</a>', paged)
    if next_href is None:
        raise SystemExit("web /orgaos?uf=RJ&take=1 missing next page")
    if "uf=RJ" not in next_href.group(1):
        raise SystemExit(f"web pager dropped UF: {next_href.group(1)}")

    empty = get_text(f"{WEB}/orgaos?q=zzzz-sem-registro")
    assert_served_page(empty, "web empty orgaos")
    if "Nenhum registro neste recorte para o filtro atual." not in empty:
        raise SystemExit("web empty orgaos missing empty copy")
    if "n=0" not in empty:
        raise SystemExit("web empty orgaos missing n=0")
    if "filtro sem registros" not in empty:
        raise SystemExit("web empty orgaos invented a UF")

    missing = get_text(f"{WEB}/orgaos/00000000-0000-0000-0000-000000000000", ok=(200, 404))
    assert_served_page(missing, "web 404")
    if "não encontrado" not in missing.casefold():
        raise SystemExit("web 404 missing not-found copy")

    cobertura = get_text(f"{WEB}/cobertura")
    assert_served_page(cobertura, "web /cobertura")
    if "3306305" not in cobertura:
        raise SystemExit("web /cobertura missing VR IBGE")
    if "3303302" not in cobertura:
        raise SystemExit("web /cobertura missing Niterói IBGE")
    if "3506003" not in cobertura:
        raise SystemExit("web /cobertura missing Bauru IBGE")
    if "4305108" not in cobertura:
        raise SystemExit("web /cobertura missing Caxias do Sul IBGE")
    if "4209102" not in cobertura:
        raise SystemExit("web /cobertura missing Joinville IBGE")
    if "3170206" not in cobertura:
        raise SystemExit("web /cobertura missing Uberlândia IBGE")
    if "4113700" not in cobertura:
        raise SystemExit("web /cobertura missing Londrina IBGE")
    if "2910800" not in cobertura:
        raise SystemExit("web /cobertura missing Feira de Santana IBGE")
    if "2604106" not in cobertura:
        raise SystemExit("web /cobertura missing Caruaru IBGE")
    if "5201108" not in cobertura:
        raise SystemExit("web /cobertura missing Anápolis IBGE")
    if "3205200" not in cobertura:
        raise SystemExit("web /cobertura missing Vila Velha IBGE")
    if "2504009" not in cobertura:
        raise SystemExit("web /cobertura missing Campina Grande IBGE")
    if "2303709" not in cobertura:
        raise SystemExit("web /cobertura missing Caucaia IBGE")
    if "2105302" not in cobertura:
        raise SystemExit("web /cobertura missing Imperatriz IBGE")
    if "2700300" not in cobertura:
        raise SystemExit("web /cobertura missing Arapiraca IBGE")
    if "5003702" not in cobertura:
        raise SystemExit("web /cobertura missing Dourados IBGE")
    if "1504208" not in cobertura:
        raise SystemExit("web /cobertura missing Marabá IBGE")
    if "5108402" not in cobertura:
        raise SystemExit("web /cobertura missing Várzea Grande IBGE")
    if "1100122" not in cobertura:
        raise SystemExit("web /cobertura missing Ji-Paraná IBGE")
    if "2403251" not in cobertura:
        raise SystemExit("web /cobertura missing Parnamirim IBGE")
    if "1200203" not in cobertura:
        raise SystemExit("web /cobertura missing Cruzeiro do Sul IBGE")
    if "1600600" not in cobertura:
        raise SystemExit("web /cobertura missing Santana IBGE")
    if "1400472" not in cobertura:
        raise SystemExit("web /cobertura missing Rorainópolis IBGE")
    if "4115200" not in cobertura:
        raise SystemExit("web /cobertura missing Maringá IBGE")
    if "3554102" not in cobertura:
        raise SystemExit("web /cobertura missing Taubaté IBGE")
    if "4104808" not in cobertura:
        raise SystemExit("web /cobertura missing Cascavel IBGE")
    if "3136702" not in cobertura:
        raise SystemExit("web /cobertura missing Juiz de Fora IBGE")
    if "4108304" not in cobertura:
        raise SystemExit("web /cobertura missing Foz do Iguaçu IBGE")
    if "4316907" not in cobertura:
        raise SystemExit("web /cobertura missing Santa Maria IBGE")
    if "3143302" not in cobertura:
        raise SystemExit("web /cobertura missing Montes Claros IBGE")
    if "3127701" not in cobertura:
        raise SystemExit("web /cobertura missing Governador Valadares IBGE")
    if "4304606" not in cobertura:
        raise SystemExit("web /cobertura missing Canoas IBGE")
    if "4209300" not in cobertura:
        raise SystemExit("web /cobertura missing Lages IBGE")
    if "1506807" not in cobertura:
        raise SystemExit("web /cobertura missing Santarém IBGE")
    if "5218805" not in cobertura:
        raise SystemExit("web /cobertura missing Rio Verde IBGE")
    if "2924009" not in cobertura:
        raise SystemExit("web /cobertura missing Paulo Afonso IBGE")
    if "2613701" not in cobertura:
        raise SystemExit("web /cobertura missing São Lourenço da Mata IBGE")
    if "2304202" not in cobertura:
        raise SystemExit("web /cobertura missing Crato IBGE")
    if "1100023" not in cobertura:
        raise SystemExit("web /cobertura missing Ariquemes IBGE")
    if "3201506" not in cobertura:
        raise SystemExit("web /cobertura missing Colatina IBGE")
    if "1502400" not in cobertura:
        raise SystemExit("web /cobertura missing Castanhal IBGE")
    if "3122306" not in cobertura:
        raise SystemExit("web /cobertura missing Divinópolis IBGE")
    if "3303906" not in cobertura:
        raise SystemExit("web /cobertura missing Petrópolis IBGE")
    if "3131307" not in cobertura:
        raise SystemExit("web /cobertura missing Ipatinga IBGE")
    if "3302403" not in cobertura:
        raise SystemExit("web /cobertura missing Macaé IBGE")
    if "3157807" not in cobertura:
        raise SystemExit("web /cobertura missing Santa Luzia IBGE")
    if "3303401" not in cobertura:
        raise SystemExit("web /cobertura missing Nova Friburgo IBGE")
    if "não é um total nacional" not in cobertura:
        raise SystemExit("web /cobertura missing disclaimer")
    if "UF mista" not in cobertura:
        raise SystemExit("web /cobertura must stay mixed-UF")

    metodologia = get_text(f"{WEB}/metodologia")
    assert_served_page(metodologia, "web /metodologia")
    if "0.1" in metodologia and "phase1-0.1.0" not in metodologia:
        raise SystemExit("web /metodologia assumed stub methodology 0.1")

    flags = get_json(f"{API}/api/internal/flags?state=detected&skip=0&take=50")
    flag_coverage = flags.get("coverage") or {}
    flag_n = flag_coverage.get("n")
    if not isinstance(flag_n, int) or flag_n < 1:
        raise SystemExit(f"internal flags coverage.n missing or empty: {flag_coverage}")
    if not str(flag_coverage.get("methodologyVersion") or ""):
        raise SystemExit("internal flags coverage missing methodologyVersion")
    flag_rows = flags.get("items") or []
    if not flag_rows:
        raise SystemExit("internal flags returned no rows")
    kinds = {str(row.get("kind") or "") for row in flag_rows}
    if "qty_unit_price_neq_total" not in kinds:
        raise SystemExit(f"internal flags missing tier1 qty fact: {sorted(kinds)}")
    for row in flag_rows:
        if str(row.get("state") or "") != "detected":
            raise SystemExit(f"internal flag state is not detected: {row.get('state')}")
        if not row.get("itemId"):
            raise SystemExit("internal flag missing itemId")
        if not row.get("delta"):
            raise SystemExit("internal flag missing delta")
        if not row.get("snapshotId"):
            raise SystemExit("internal flag missing snapshotId")
        if not row.get("methodologyVersion"):
            raise SystemExit("internal flag missing methodologyVersion")
    paged = get_json(f"{API}/api/internal/flags?state=detected&take=1")
    if len(paged.get("items") or []) != 1:
        raise SystemExit("internal flags take=1 did not page")
    if (paged.get("coverage") or {}).get("n") != flag_n:
        raise SystemExit("internal flags page coverage.n changed")
    qty = get_json(f"{API}/api/internal/flags?kind=qty_unit_price_neq_total&state=detected")
    if not (qty.get("items") or []):
        raise SystemExit("internal flags kind filter missed qty_unit_price_neq_total")
    deny_flags(orgaos, f"{API}/api/orgaos")
    deny_flags(items, f"{API}/api/items")
    deny_flags(item, f"{API}/api/items/{iid}")

    print("compose prove ok")
    print(f"orgaos={len(items_page)} ibges={sorted(by_ibge)} items={n} flags={flag_n}")
    return 0


def assert_served_page(html: str, where: str) -> None:
    deny_stub(html, where)
    if BANNED_COPY.search(html):
        raise SystemExit(f"{where} leaked banned copy")
    if not re.search(r"n=\d+", html):
        raise SystemExit(f"{where} missing coverage n")
    if not any(token in html for token in ("UF RJ", "UF SP", "UF RS", "UF SC", "UF MG", "UF PR", "UF BA", "UF PE", "UF GO", "UF ES", "UF PB", "UF CE", "UF MA", "UF AL", "UF MS", "UF PA", "UF MT", "UF RO", "UF RN", "UF AC", "UF AP", "UF RR", "UF mista", "filtro sem registros")):
        raise SystemExit(f"{where} missing UF / empty-filter chip")
    if not re.search(r"trimestre|trim\.", html, re.I):
        raise SystemExit(f"{where} missing trimestre")
    if not re.search(r"metodologia", html, re.I):
        raise SystemExit(f"{where} missing metodologia")


def get_json(url: str) -> dict:
    raw = get_text(url)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{url} is not JSON") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{url} JSON is not an object")
    return data


def get_text(url: str, ok: tuple[int, ...] = (200,)) -> str:
    req = urllib.request.Request(url, headers={"accept": "application/json, text/html"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status not in ok:
                raise SystemExit(f"{url} status {resp.status}")
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code in ok:
            return exc.read().decode("utf-8", "replace")
        raise SystemExit(f"{url} status {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"{url} unreachable: {exc.reason}") from exc


def table_html(html: str) -> str:
    match = re.search(r"<table\b[\s\S]*?</table>", html, re.I)
    return match.group(0) if match else ""


def deny_stub(blob: str, where: str) -> None:
    for marker in STUB_MARKERS:
        if marker in blob:
            raise SystemExit(f"{where} used stub data ({marker})")


def deny_flags(payload: object, where: str) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if FLAG_KEY.search(str(key)):
                raise SystemExit(f"{where} leaked public flag field {key}")
            deny_flags(value, where)
        return
    if isinstance(payload, list):
        for item in payload:
            deny_flags(item, where)


if __name__ == "__main__":
    sys.exit(main())
