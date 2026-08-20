# Metodologia

Versão 0.2.

Este documento é a metodologia pública carimbada na linha de fonte do explorador.

A cobertura é incompleta.
Nenhum agregado afirma cobertura nacional.
O recorte publicado agora é Volta Redonda e Niterói (RJ), Bauru (SP), Caxias do Sul (RS), Joinville (SC), Uberlândia (MG), Londrina (PR), Feira de Santana (BA), Caruaru (PE), Anápolis (GO), Vila Velha (ES), Campina Grande (PB), Caucaia (CE), Imperatriz (MA), Arapiraca (AL), Dourados (MS), Marabá (PA), Várzea Grande (MT), Ji-Paraná (RO), Parnamirim (RN), Cruzeiro do Sul (AC), Santana (AP), Rorainópolis (RR), Maringá (PR), Taubaté (SP), Cascavel (PR), Juiz de Fora (MG), Foz do Iguaçu (PR), Santa Maria (RS), Montes Claros (MG), Governador Valadares (MG), Canoas (RS), Lages (SC), Santarém (PA), Rio Verde (GO), Paulo Afonso (BA), São Lourenço da Mata (PE), Crato (CE), Ariquemes (RO), Colatina (ES), Castanhal (PA), Divinópolis (MG), Petrópolis (RJ), Ipatinga (MG), Macaé (RJ), Santa Luzia (MG), Nova Friburgo (RJ), Marília (SP), Balneário Camboriú (SC), Itaquaquecetuba (SP), Praia Grande (SP), São José dos Pinhais (PR), Suzano (SP), Guarujá (SP), Cotia (SP), Parauapebas (PA), Jacareí (SP), Itaboraí (RJ) e Maricá (RJ), códigos IBGE 3306305, 3303302, 3506003, 4305108, 4209102, 3170206, 4113700, 2910800, 2604106, 5201108, 3205200, 2504009, 2303709, 2105302, 2700300, 5003702, 1504208, 5108402, 1100122, 2403251, 1200203, 1600600, 1400472, 4115200, 3554102, 4104808, 3136702, 4108304, 4316907, 3143302, 3127701, 4304606, 4209300, 1506807, 5218805, 2924009, 2613701, 2304202, 1100023, 3201506, 1502400, 3122306, 3303906, 3131307, 3302403, 3157807, 3303401, 3529005, 4202008, 3523107, 3541000, 4125506, 3552502, 3518701, 3513009, 1505536, 3524402, 3301900 e 3302700, ano 2024, extraído dos arquivos em lote do Compras.gov.br.
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
Os valores de proposta de participantes do TCE-SP e do TCE-RS LicitaCon ficam no warehouse interno.
O explorador não lê essas fontes.

A precisão do método ingênuo de desvio de preço da Fase 0, neste recorte, é 9/100.
Esse número é o portão do Tier 3 público.
É uma medição, não um veredito sobre qualquer órgão.
Exclusões de qualidade de dado (`item_exclusion`) retiram o item do pool de anomalia de preço.
Elas não são alertas públicos.
O item permanece no explorador.

O CPF é mascarado.
Não há ranking de partido nem de político.

O warehouse é o contrato.
O Python nunca chama o C#.
O C# nunca executa um detector.

O classificador CATMAT/CATSER é interno ao normalize.
Ele só preenche item sem código oficial, por hash da descrição, embedding local e kNN com margem alta.
Caso de margem baixa permanece sem código.
Código `knn` atribuído não é alerta público.
A cobertura medida da Fase 0 em Volta Redonda 2024 permanece 81.75%.
Esse número é a linha de base rotulada daquele recorte, não o percentual ao vivo do warehouse.
O percentual público em `/cobertura` é o join inteiro exato de `item.catmat`/`item.catser` ao catálogo ingerido.

`unidadeMedida` é texto livre.
Cada item recebe `unidadeCanonica` a partir da tabela em `normalize/compras_normalize/data/unidade_medida.csv`.
Caixa ou pacote com contagem explícita usa esse fator e a unidade interna.
Caixa ou pacote sem contagem permanece no catálogo (`CX` vira `cx`, fator 1).
Unidade sem correspondência permanece `unknown`.
`valorPorUnidadeCanonica` é o preço por unidade canônica (`valorUnitario / to_base_factor`).
Unidade desconhecida não inventa preço comparável.

`specConcentracao`, `specDosagem` e `specTamanho` guardam o token extraído da descrição.
Ausência de token permanece nula.
Esses campos não aparecem no explorador público.

## Sinais internos Tier 1

A versão 0.2 descreve os sinais internos já embarcados.
Nenhum destes sinais aparece no explorador público.
O estado permanece `detected`.
O texto de um sinal, se existir, é só um indício que pede verificação.

### Quantidade e exclusões de qualidade de dado

`qty_unit_price_neq_total` marca o item quando quantidade vezes preço unitário diverge do total além de 0,02 ou 0,2%.
O mesmo critério vira exclusão `item_exclusion` e tira o item do pool de anomalia de preço.
Outras exclusões de qualidade são `decimal_shift`, `qty_eq_1_collapse`, `zero_or_negative`, `duplicate_row` e `catalog_magnitude`.
Exclusão não é alerta público.
O item permanece no explorador.

### CEIS e CNEP na janela da homologação

`sanctioned_ceis_cnep` cruza o CNPJ do fornecedor com o CEIS e o CNEP da CGU.
O sinal só nasce quando a data de homologação cai dentro da vigência da sanção.
Fonte e janela ficam no landing interno.
O explorador não lê essa fonte.

### Idade do CNPJ

`cnpj_age` nasce quando a homologação ocorre em menos de 90 dias após a abertura do CNPJ.
`cnpj_age_info` nasce quando essa idade está entre 90 e 365 dias.
Idade maior que 365 dias não gera sinal.
Datas ausentes ou invertidas são ignoradas.

### Fracionamento

`fracionamento` agrega dispensas do mesmo órgão, mesma classe CATMAT e mesmo ano.
O sinal nasce quando cada compra fica abaixo do limiar do decreto daquele ano e a soma ultrapassa o Art. 75.
`fracionamento_cluster` pede ao menos três dispensas na última décima do limiar, com datas em janela de 90 dias.
Os valores do limiar vêm de `detect/compras_detect/data/dispensa_thresholds.csv`.
Em juízo, o fracionamento da contratação exige dolo específico.
Este detector é um indício de agregado anual do mesmo objeto frente aos limiares do decreto, não um veredito.

### Edição retroativa

`retroactive_edit` compara snapshots do mesmo registro no landing.
O sinal nasce quando preço, quantidade ou fornecedor muda depois da publicação ou da homologação.
Mudança só de descrição não gera sinal.
Snapshot anterior à publicação não gera sinal.

### CNAE fora da allow-list da classe

`cnae_mismatch` marca um item de material homologado quando a classe CATMAT tem prefixos CNAE mapeados e nenhum CNAE do vencedor (principal ou secundário) começa com esses prefixos.
A tabela é conservadora e cita o catálogo CATMAT e a CNAE 2.0 da CONCLA.
Classe ausente, CNAE ausente ou não numérico, e classe sem mapeamento não geram sinal, mas continuam no denominador de cobertura.
Linha de serviço ou CATSER fica de fora.
Este sinal tem risco alto de falso positivo.
Ele fica fora do conjunto de novembro até uma amostragem posterior cruzar o limiar.
Não é alerta público.
Nada acusatório é publicado antes de 25 de outubro de 2026.

## Ressalvas legais

Estas frases são ressalvas, não acusações.
Sócios em comum não são, por si sós, ilícitos, conforme os Acórdãos 297/2009, 1.793/2011 e 2.803/2016 do TCU.
Um desvio de preço não é, por si só, um ilícito.
A precisão do método ingênuo da Fase 0 neste recorte é 9%.
Sinais públicos permanecem fechados.

## Carimbo 0.2

Sinais internos novos gravados pelo pipeline recebem methodologyVersion 0.2.
O agregado de cobertura do explorador usa a mesma versão.
Uma linha já persistida em `flag` mantém o carimbo anterior, porque o conflito de escrita atualiza só o delta.
Os fixtures FullCycle da API permanecem em 0.1.
Os arquivos de rótulo da Fase 0 e do A3 permanecem em phase1-0.1.0.
