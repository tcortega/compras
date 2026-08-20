# Metodologia

Versão 0.1.

Este documento é a metodologia pública carimbada na linha de fonte do explorador.

A cobertura é incompleta.
Nenhum agregado afirma cobertura nacional.
O recorte publicado agora é Volta Redonda e Niterói (RJ), Bauru (SP), Caxias do Sul (RS), Joinville (SC), Uberlândia (MG), Londrina (PR), Feira de Santana (BA), Caruaru (PE), Anápolis (GO), Vila Velha (ES), Campina Grande (PB), Caucaia (CE), Imperatriz (MA), Arapiraca (AL), Dourados (MS), Marabá (PA), Várzea Grande (MT), Ji-Paraná (RO), Parnamirim (RN), Cruzeiro do Sul (AC), Santana (AP), Rorainópolis (RR), Maringá (PR), Taubaté (SP), Cascavel (PR), Juiz de Fora (MG), Foz do Iguaçu (PR), Santa Maria (RS), Montes Claros (MG), Governador Valadares (MG), Canoas (RS), Lages (SC), Santarém (PA), Rio Verde (GO), Paulo Afonso (BA), São Lourenço da Mata (PE), Crato (CE), Ariquemes (RO), Colatina (ES), Castanhal (PA), Divinópolis (MG) e Petrópolis (RJ), códigos IBGE 3306305, 3303302, 3506003, 4305108, 4209102, 3170206, 4113700, 2910800, 2604106, 5201108, 3205200, 2504009, 2303709, 2105302, 2700300, 5003702, 1504208, 5108402, 1100122, 2403251, 1200203, 1600600, 1400472, 4115200, 3554102, 4104808, 3136702, 4108304, 4316907, 3143302, 3127701, 4304606, 4209300, 1506807, 5218805, 2924009, 2613701, 2304202, 1100023, 3201506, 1502400, 3122306 e 3303906, ano 2024, extraído dos arquivos em lote do Compras.gov.br.
Esses municípios aparecem no COMPRA municipal de 2024.
O conjunto não é um censo nacional.
Quando o agregado mistura UF, o campo uf fica vazio.
A API de consulta do PNCP é gravada em parquet imutável para entidades que não estão nesse lote.
O explorador publicado neste recorte ainda lê o lote Compras.gov.br.
Todo agregado mostra n, UF e trimestre.
Municípios com menos de 20 mil habitantes estão dispensados de publicar no PNCP até 31 de março de 2027.
O TCU, no Acórdão 53/2025, registrou inconsistência em 86,4% dos registros do PNCP.
Esse percentual é um fato de qualidade dos dados, não uma acusação.

O explorador da Fase 2 permite só busca, listagem e ficha.
Não há alertas públicos, ranking nem pontuação.
Os valores de proposta de participantes do TCE-SP ficam só no landing interno.
Os valores de proposta de participantes do TCE-RS LicitaCon ficam só no landing interno.
O explorador não lê essas fontes.

A precisão do método ingênuo de desvio de preço da Fase 0, neste recorte, é 9/100.
Esse número é o portão do Tier 3 público.
É uma medição, não um veredito sobre qualquer órgão.

O CPF é mascarado.
Não há ranking de partido nem de político.

O warehouse é o contrato.
O Python nunca chama o C#.
O C# nunca executa um detector.

`unidadeMedida` é texto livre.
Cada item recebe `unidadeCanonica` a partir da tabela em `normalize/compras_normalize/data/unidade_medida.csv`.
Unidade sem correspondência permanece `unknown`.
`valorPorUnidadeCanonica` é o preço por unidade canônica (`valorUnitario / to_base_factor`).
Unidade desconhecida não inventa preço comparável.
