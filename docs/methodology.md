# Metodologia

Versão 0.1.

Este documento é a metodologia pública carimbada na linha de fonte do explorador.

A cobertura é incompleta.
Nenhum agregado afirma cobertura nacional.
O recorte publicado agora é Volta Redonda e Niterói (RJ), Bauru (SP), Caxias do Sul (RS), Joinville (SC), Uberlândia (MG) e Londrina (PR), códigos IBGE 3306305, 3303302, 3506003, 4305108, 4209102, 3170206 e 4113700, ano 2024, extraído dos arquivos em lote do Compras.gov.br.
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
