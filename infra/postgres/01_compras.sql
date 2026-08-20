CREATE TABLE IF NOT EXISTS orgao (
  id uuid PRIMARY KEY,
  cnpj text NOT NULL UNIQUE,
  "razaoSocial" text NOT NULL,
  esfera text NOT NULL CHECK (esfera IN ('federal', 'estadual', 'municipal')),
  poder text NOT NULL,
  uf text NOT NULL,
  "municipioIbge" text,
  "municipioNome" text,
  suspended boolean NOT NULL DEFAULT false,
  "createdAt" timestamptz NOT NULL,
  "updatedAt" timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS fornecedor (
  id uuid PRIMARY KEY,
  cnpj text NOT NULL UNIQUE,
  "razaoSocial" text NOT NULL,
  "openedOn" date,
  cnae text,
  suspended boolean NOT NULL DEFAULT false,
  "createdAt" timestamptz NOT NULL,
  "updatedAt" timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS contratacao (
  id uuid PRIMARY KEY,
  "pncpId" text NOT NULL UNIQUE,
  "orgaoId" uuid NOT NULL REFERENCES orgao (id),
  modalidade text NOT NULL,
  objeto text NOT NULL,
  ano int NOT NULL,
  "valorHomologado" numeric(18, 6),
  "publicadoEm" timestamptz,
  source text NOT NULL,
  "snapshotId" text NOT NULL,
  "methodologyVersion" text NOT NULL,
  suspended boolean NOT NULL DEFAULT false,
  "createdAt" timestamptz NOT NULL,
  "updatedAt" timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS item (
  id uuid PRIMARY KEY,
  "contratacaoId" uuid NOT NULL REFERENCES contratacao (id),
  "fornecedorId" uuid REFERENCES fornecedor (id),
  descricao text NOT NULL,
  catmat text,
  catser text,
  quantidade numeric(18, 6) NOT NULL,
  "unidadeMedida" text NOT NULL,
  "unidadeCanonica" text,
  "valorUnitario" numeric(18, 6),
  "valorTotal" numeric(18, 6),
  "valorPorUnidadeCanonica" numeric(18, 6),
  "specConcentracao" text,
  "specDosagem" text,
  "specTamanho" text,
  uf text NOT NULL,
  quarter text NOT NULL,
  "snapshotId" text NOT NULL,
  "methodologyVersion" text NOT NULL,
  suspended boolean NOT NULL DEFAULT false,
  "createdAt" timestamptz NOT NULL,
  "updatedAt" timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS flag (
  id uuid PRIMARY KEY,
  "itemId" uuid NOT NULL REFERENCES item (id),
  kind text NOT NULL,
  state text NOT NULL CHECK (state IN (
    'detected', 'internal_review', 'notified', 'published', 'resolved', 'retracted'
  )),
  "detectedAt" timestamptz NOT NULL,
  "notifiedAt" timestamptz,
  "publishAfter" timestamptz,
  "publishedAt" timestamptz,
  delta text NOT NULL,
  "sourceUrl" text,
  "snapshotId" text NOT NULL,
  "methodologyVersion" text NOT NULL,
  "replyText" text,
  "repliedAt" timestamptz,
  suspended boolean NOT NULL DEFAULT false,
  "createdAt" timestamptz NOT NULL,
  "updatedAt" timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS item_exclusion (
  "itemId" uuid NOT NULL REFERENCES item (id),
  reason text NOT NULL CHECK (reason IN (
    'qty_unit_price_neq_total',
    'decimal_shift',
    'qty_eq_1_collapse',
    'zero_or_negative',
    'duplicate_row',
    'catalog_magnitude'
  )),
  detail text,
  "snapshotId" text NOT NULL,
  "methodologyVersion" text NOT NULL,
  "createdAt" timestamptz NOT NULL,
  PRIMARY KEY ("itemId", reason)
);

CREATE INDEX IF NOT EXISTS item_contratacao_idx ON item ("contratacaoId");
CREATE INDEX IF NOT EXISTS item_peer_idx ON item (catmat, uf, quarter);
CREATE INDEX IF NOT EXISTS contratacao_orgao_idx ON contratacao ("orgaoId");
CREATE INDEX IF NOT EXISTS flag_item_idx ON flag ("itemId");
CREATE INDEX IF NOT EXISTS flag_state_idx ON flag (state);
CREATE INDEX IF NOT EXISTS flag_kind_idx ON flag (kind);
CREATE INDEX IF NOT EXISTS item_exclusion_item_idx ON item_exclusion ("itemId");
CREATE INDEX IF NOT EXISTS item_exclusion_reason_idx ON item_exclusion (reason);

CREATE TABLE IF NOT EXISTS catalog_code (
  codigo text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('catmat', 'catser')),
  PRIMARY KEY (codigo, kind)
);

CREATE TABLE IF NOT EXISTS landing_source (
  name text PRIMARY KEY,
  "lastUpdate" timestamptz,
  n int NOT NULL DEFAULT 0,
  "snapshotId" text
);

CREATE TABLE IF NOT EXISTS fornecedor_adjacency (
  kind text NOT NULL CHECK (kind IN (
    'shared_qsa_partner',
    'shared_address',
    'shared_phone',
    'shared_email'
  )),
  "leftCnpj" text NOT NULL,
  "rightCnpj" text NOT NULL,
  evidence text NOT NULL,
  "snapshotId" text NOT NULL,
  "methodologyVersion" text NOT NULL,
  "createdAt" timestamptz NOT NULL,
  PRIMARY KEY (kind, "leftCnpj", "rightCnpj"),
  CHECK ("leftCnpj" < "rightCnpj")
);

CREATE INDEX IF NOT EXISTS fornecedor_adjacency_left_idx ON fornecedor_adjacency ("leftCnpj");
CREATE INDEX IF NOT EXISTS fornecedor_adjacency_right_idx ON fornecedor_adjacency ("rightCnpj");
CREATE INDEX IF NOT EXISTS fornecedor_adjacency_kind_idx ON fornecedor_adjacency (kind);

ALTER TABLE item ADD COLUMN IF NOT EXISTS "valorPorUnidadeCanonica" numeric(18, 6);
ALTER TABLE item ADD COLUMN IF NOT EXISTS "specConcentracao" text;
ALTER TABLE item ADD COLUMN IF NOT EXISTS "specDosagem" text;
ALTER TABLE item ADD COLUMN IF NOT EXISTS "specTamanho" text;
