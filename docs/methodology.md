# Metodologia

Versão 0.1.

Este documento é a metodologia pública carimbada na linha de fonte do explorador.

A cobertura é incompleta.
Nenhum agregado afirma cobertura nacional.
O recorte publicado agora é Volta Redonda, RJ, código IBGE 3306305, ano 2024, extraído dos arquivos em lote do Compras.gov.br.
A API de consulta do PNCP é gravada em parquet imutável para entidades que não estão nesse lote.
O explorador publicado neste recorte ainda lê o lote Compras.gov.br.
Todo agregado mostra n, UF e trimestre.
Municípios com menos de 20 mil habitantes estão dispensados de publicar no PNCP até 31 de março de 2027.
O TCU, no Acórdão 53/2025, registrou inconsistência em 86,4% dos registros do PNCP.
Esse percentual é um fato de qualidade dos dados, não uma acusação.

O explorador da Fase 2 permite só busca, listagem e ficha.
Não há alertas públicos, ranking nem pontuação.

A precisão do método ingênuo de desvio de preço da Fase 0, neste recorte, é 9/100.
Esse número é o portão do Tier 3 público.
É uma medição, não um veredito sobre qualquer órgão.

O CPF é mascarado.
Não há ranking de partido nem de político.

O warehouse é o contrato.
O Python nunca chama o C#.
O C# nunca executa um detector.
