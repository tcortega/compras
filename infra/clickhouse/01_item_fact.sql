CREATE DATABASE IF NOT EXISTS compras;

CREATE TABLE IF NOT EXISTS compras.item_fact
(
    item_id UUID,
    contratacao_id UUID,
    fornecedor_id Nullable(UUID),
    orgao_id Nullable(UUID),
    pncp_id String,
    descricao String,
    catmat Nullable(String),
    catser Nullable(String),
    quantidade Float64,
    unidade_medida String,
    unidade_canonica Nullable(String),
    valor_unitario Nullable(Float64),
    valor_total Nullable(Float64),
    valor_unitario_base Nullable(Float64),
    uf String,
    quarter String,
    snapshot_id String,
    methodology_version String,
    source String,
    record_hash String,
    publicado_em Nullable(DateTime64(3, 'UTC'))
)
ENGINE = ReplacingMergeTree
ORDER BY (uf, quarter, item_id);
