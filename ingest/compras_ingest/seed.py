from __future__ import annotations

import sys

from compras_ingest.pipeline import run_compras_slice
from compras_ingest.settings import Settings
from compras_ingest.warehouse import fetch_contratacao_anos, fetch_counts, fetch_one_orgao, fetch_orgaos

SLICES = (
    ("29477000000180", "3306305", "RJ", "Volta Redonda"),
    ("28521748000159", "3303302", "RJ", "Niterói"),
    ("46137410000180", "3506003", "SP", "Bauru"),
    ("88830609000139", "4305108", "RS", "Caxias do Sul"),
    ("83169623000110", "4209102", "SC", "Joinville"),
    ("18431312000115", "3170206", "MG", "Uberlândia"),
    ("75771477000170", "4113700", "PR", "Londrina"),
    ("14043574000151", "2910800", "BA", "Feira de Santana"),
    ("10091536000113", "2604106", "PE", "Caruaru"),
    ("01067479000146", "5201108", "GO", "Anápolis"),
    ("27165554000103", "3205200", "ES", "Vila Velha"),
    ("08993917000146", "2504009", "PB", "Campina Grande"),
    ("07616162000106", "2303709", "CE", "Caucaia"),
    ("06158455000116", "2105302", "MA", "Imperatriz"),
    ("12198693000158", "2700300", "AL", "Arapiraca"),
    ("20267427000168", "5003702", "MS", "Dourados"),
    ("05853163000130", "1504208", "PA", "Marabá"),
    ("03507548000110", "5108402", "MT", "Várzea Grande"),
    ("04092672000125", "1100122", "RO", "Ji-Paraná"),
    ("08170862000174", "2403251", "RN", "Parnamirim"),
    ("04012548000102", "1200203", "AC", "Cruzeiro do Sul"),
    ("23066640000108", "1600600", "AP", "Santana"),
    ("01613031000180", "1400472", "RR", "Rorainópolis"),
    ("76282656000106", "4115200", "PR", "Maringá"),
    ("45176005000108", "3554102", "SP", "Taubaté"),
    ("76208867000107", "4104808", "PR", "Cascavel"),
    ("18338178000102", "3136702", "MG", "Juiz de Fora"),
    ("76206606000140", "4108304", "PR", "Foz do Iguaçu"),
    ("88488366000100", "4316907", "RS", "Santa Maria"),
    ("22678874000135", "3143302", "MG", "Montes Claros"),
    ("20622890000180", "3127701", "MG", "Governador Valadares"),
    ("88577416000118", "4304606", "RS", "Canoas"),
    ("82777301000190", "4209300", "SC", "Lages"),
    ("05182233000761", "1506807", "PA", "Santarém"),
    ("02056729000105", "5218805", "GO", "Rio Verde"),
    ("14217327000124", "2924009", "BA", "Paulo Afonso"),
    ("11251832000105", "2613701", "PE", "São Lourenço da Mata"),
    ("07587975000107", "2304202", "CE", "Crato"),
    ("04104816000116", "1100023", "RO", "Ariquemes"),
    ("27165729000174", "3201506", "ES", "Colatina"),
    ("05121991000184", "1502400", "PA", "Castanhal"),
    ("18291351000164", "3122306", "MG", "Divinópolis"),
    ("29138344000143", "3303906", "RJ", "Petrópolis"),
    ("19876424000142", "3131307", "MG", "Ipatinga"),
    ("29115474000160", "3302403", "RJ", "Macaé"),
    ("18715409000150", "3157807", "MG", "Santa Luzia"),
    ("28606630000123", "3303401", "RJ", "Nova Friburgo"),
    ("44477909000100", "3529005", "SP", "Marília"),
    ("83102285000107", "4202008", "SC", "Balneário Camboriú"),
    ("46316600000164", "3523107", "SP", "Itaquaquecetuba"),
    ("46177531000155", "3541000", "SP", "Praia Grande"),
    ("76105543000135", "4125506", "PR", "São José dos Pinhais"),
    ("46523056000121", "3552502", "SP", "Suzano"),
    ("44959021000104", "3518701", "SP", "Guarujá"),
    ("46523049000120", "3513009", "SP", "Cotia"),
    ("22980999000115", "1505536", "PA", "Parauapebas"),
    ("46694139000183", "3524402", "SP", "Jacareí"),
    ("28741080000155", "3301900", "RJ", "Itaboraí"),
    ("29131075000193", "3302700", "RJ", "Maricá"),
    ("04508933000145", "1200104", "AC", "Brasiléia"),
    ("04051207000146", "1200344", "AC", "Manoel Urbano"),
    ("04034583000122", "1200401", "AC", "Rio Branco"),
    ("01674973000179", "1200609", "AC", "Tarauacá"),
    ("12333753000106", "2701704", "AL", "Capela"),
    ("12250908000132", "2702504", "AL", "Dois Riachos"),
    ("12200168000120", "2707701", "AL", "Rio Largo"),
    ("12332946000134", "2709301", "AL", "União dos Palmares"),
    ("04530713000118", "1300201", "AM", "Atalaia do Norte"),
    ("04263331000175", "1301308", "AM", "Codajás"),
    ("04477634000190", "1304005", "AM", "Silves"),
    ("05995766000177", "1600303", "AP", "Macapá"),
    ("14222012000175", "2908101", "BA", "Cocos"),
    ("13846753000164", "2912707", "BA", "Ibirapitanga"),
    ("13743281000114", "2927309", "BA", "Salinas da Margarida"),
    ("13696257000171", "2929602", "BA", "Sapeaçu"),
    ("07911696000157", "2301000", "CE", "Aquiraz"),
    ("07954605000160", "2304400", "CE", "Fortaleza"),
    ("12359535000132", "2304954", "CE", "Guaiúba"),
    ("23555196000186", "2305233", "CE", "Horizonte"),
    ("27165653000187", "3203106", "ES", "Jerônimo Monteiro"),
    ("27165687000171", "3203700", "ES", "Muniz Freire"),
    ("27165703000126", "3204302", "ES", "Presidente Kennedy"),
    ("01612865000171", "3204955", "ES", "São Roque do Canaã"),
    ("36862621000121", "5205497", "GO", "Cidade Ocidental"),
    ("01303221000100", "5208509", "GO", "Goiandira"),
    ("02451938000153", "5210406", "GO", "Itaberaí"),
    ("00097857000171", "5219753", "GO", "Santo Antônio do Descoberto"),
    ("01597627000134", "2104552", "MA", "Governador Edison Lobão"),
    ("12511093000106", "2110039", "MA", "Santa Luzia do Paruá"),
    ("01612333000134", "2110658", "MA", "São Domingos do Azeitão"),
    ("06307102000130", "2111300", "MA", "São Luís"),
    ("18715383000140", "3106200", "MG", "Belo Horizonte"),
    ("18659334000137", "3111200", "MG", "Campo Belo"),
    ("17888082000155", "3120201", "MG", "Cristais"),
    ("18307835000154", "3131901", "MG", "Itabirito"),
    ("03576220000156", "5001904", "MS", "Bataguassu"),
    ("03442597000112", "5005400", "MS", "Maracaju"),
    ("03214145000183", "5102504", "MT", "Cáceres"),
    ("04178518000170", "5107743", "MT", "Santa Cruz do Xingu"),
    ("01614112000103", "1501451", "PA", "Belterra"),
    ("05149166000198", "1506203", "PA", "Salinópolis"),
    ("05193115000163", "1507201", "PA", "São Domingos do Capim"),
    ("23060866000193", "1507979", "PA", "Terra Santa"),
    ("08778318000100", "2500601", "PB", "Alhandra"),
    ("08923971000115", "2503704", "PB", "Cajazeiras"),
    ("09073628000191", "2509701", "PB", "Monteiro"),
    ("09069709000118", "2513901", "PB", "São Bento"),
    ("10260222000105", "2601706", "PE", "Belo Jardim"),
    ("10091510000175", "2601904", "PE", "Bezerros"),
    ("11358140000152", "2612802", "PE", "Santa Terezinha"),
    ("11361201000130", "2615201", "PE", "Terra Nova"),
    ("01612573000139", "2202075", "PI", "Cajazeiras do Piauí"),
    ("06553713000169", "2204204", "PI", "Francisco Santos"),
    ("01612805000159", "2210623", "PI", "Sebastião Barros"),
    ("06985832000190", "2211209", "PI", "Uruçuí"),
    ("75732057000184", "4103701", "PR", "Cambé"),
    ("76205640000108", "4107207", "PR", "Dois Vizinhos"),
    ("77816510000166", "4108403", "PR", "Francisco Beltrão"),
    ("76995323000124", "4115309", "PR", "Mariópolis"),
    ("76995448000154", "4118501", "PR", "Pato Branco"),
    ("77003424000134", "4120606", "PR", "Prudentópolis"),
    ("76205673000140", "4121406", "PR", "Realeza"),
    ("76205699000198", "4122800", "PR", "Salgado Filho"),
    ("76170240000104", "4127106", "PR", "Telêmaco Borba"),
    ("78279973000107", "4127965", "PR", "Turvo"),
    ("78101821000101", "4128559", "PR", "Vera Cruz do Oeste"),
    ("29172467000109", "3300100", "RJ", "Angra dos Reis"),
    ("31846892000170", "3302254", "RJ", "Itatiaia"),
    ("42498733000148", "3304557", "RJ", "Rio de Janeiro"),
    ("28909604000174", "3305208", "RJ", "São Pedro da Aldeia"),
    ("08349102000129", "2402303", "RN", "Caraúbas"),
    ("08109126000100", "2403103", "RN", "Currais Novos"),
    ("08241747000496", "2408102", "RN", "Natal"),
    ("01266058000144", "1100452", "RO", "Buritis"),
    ("04279238000159", "1100114", "RO", "Jaru"),
    ("05903125000145", "1100205", "RO", "Porto Velho"),
    ("05943030000155", "1400100", "RR", "Boa Vista"),
    ("01612682000156", "1400175", "RR", "Cantá"),
    ("04653408000113", "1400209", "RR", "Caracaraí"),
    ("04056230000123", "1400605", "RR", "São Luiz"),
    ("87990800000185", "4303103", "RS", "Cachoeirinha"),
    ("87613154000137", "4305900", "RS", "Coronel Bicaco"),
    ("87613022000105", "4318903", "RS", "São Luiz Gonzaga"),
    ("87572079000103", "4319802", "RS", "São Vicente do Sul"),
    ("83024240000153", "4208005", "SC", "Itá"),
    ("83021865000161", "4214201", "SC", "Quilombo"),
    ("83102491000109", "4217402", "SC", "Schroeder"),
    ("83009860000113", "4219507", "SC", "Xanxerê"),
    ("46634101000115", "3507506", "SP", "Botucatu"),
    ("44435121000131", "3508108", "SP", "Buritama"),
    ("51885242000140", "3509502", "SP", "Campinas"),
    ("46319000000150", "3518800", "SP", "Guarulhos"),
    ("45332095000189", "3530805", "SP", "Mogi Mirim"),
    ("46189718000179", "3536703", "SP", "Pederneiras"),
    ("56024581000156", "3543402", "SP", "Ribeirão Preto"),
    ("45368545000193", "3547601", "SP", "Santa Rosa de Viterbo"),
    ("59851600000106", "3549508", "SP", "São José da Bela Vista"),
    ("45787678000102", "3556206", "SP", "Valinhos"),
    ("01795483000120", "1705508", "TO", "Colinas do Tocantins"),
)


def main() -> int:
    settings = Settings.from_env()
    result = run_compras_slice(settings)
    seen_ibge: set[str] = set()
    seen_uf: set[str] = set()
    for cnpj, ibge, uf, nome in SLICES:
        orgao = fetch_one_orgao(settings, cnpj)
        if orgao is None:
            raise SystemExit(f"missing {nome} orgao {cnpj}")
        if str(orgao.get("municipioIbge") or "") != ibge:
            raise SystemExit(f"{nome}: expected IBGE {ibge}, got {orgao.get('municipioIbge')}")
        if str(orgao.get("uf") or "") != uf:
            raise SystemExit(f"{nome}: expected UF {uf}, got {orgao.get('uf')}")
        seen_ibge.add(ibge)
        seen_uf.add(uf)
        print(f"orgao={orgao['cnpj']} ibge={orgao['municipioIbge']} uf={orgao['uf']}")
    required_ibge = {ibge for _, ibge, _, _ in SLICES}
    if not required_ibge.issubset(seen_ibge):
        raise SystemExit(f"warehouse missing published IBGE codes: {sorted(required_ibge - seen_ibge)}")
    required_uf = {uf for _, _, uf, _ in SLICES}
    if not required_uf.issubset(seen_uf):
        raise SystemExit(f"warehouse missing published UFs: {sorted(required_uf - seen_uf)}")
    landed = {(str(o.get("municipioIbge") or ""), str(o.get("uf") or "")) for o in fetch_orgaos(settings)}
    required_landed = {(ibge, uf) for _, ibge, uf, _ in SLICES}
    if not required_landed.issubset(landed):
        raise SystemExit(f"warehouse orgao set is missing the published slice: {sorted(required_landed - landed)}")
    counts = fetch_counts(settings)
    if counts["item"] < 1:
        raise SystemExit("warehouse has no items")
    if counts["orgao"] < len(SLICES):
        raise SystemExit(f"warehouse orgao count {counts['orgao']} < {len(SLICES)}")
    anos = set(fetch_contratacao_anos(settings))
    missing_years = {2024, 2025, 2026} - anos
    if missing_years:
        raise SystemExit(f"warehouse missing years {sorted(missing_years)}: {sorted(anos)}")
    print("seed ok")
    print(f"entities={result.entity_counts} facts={result.fact_rows} flags={result.flag_rows} adjacencies={result.adjacency_rows} participants={result.participant_rows} cobid={result.cobid_edge_rows}/{result.cobid_screen_rows}")
    print(f"counts={counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
