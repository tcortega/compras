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
  "notifyArtifact" text,
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

CREATE TABLE IF NOT EXISTS cnae (
  codigo text PRIMARY KEY,
  descricao text NOT NULL
);

CREATE TABLE IF NOT EXISTS fornecedor_socio (
  id uuid PRIMARY KEY,
  "fornecedorId" uuid NOT NULL REFERENCES fornecedor (id),
  "fornecedorCnpj" text NOT NULL,
  nome text NOT NULL,
  "cpfMasked" text,
  qualificacao text
);

CREATE INDEX IF NOT EXISTS fornecedor_socio_cnpj_idx ON fornecedor_socio ("fornecedorCnpj");
CREATE INDEX IF NOT EXISTS fornecedor_socio_fornecedor_idx ON fornecedor_socio ("fornecedorId");

CREATE TABLE IF NOT EXISTS licitacao_participante (
  id uuid PRIMARY KEY,
  "licitacaoId" text NOT NULL,
  uf text NOT NULL CHECK (uf IN ('SP', 'RS')),
  orgao text NOT NULL,
  classe text NOT NULL DEFAULT '',
  "itemLote" text NOT NULL DEFAULT '',
  participante text NOT NULL,
  proposta numeric(18, 6),
  winner boolean NOT NULL,
  source text NOT NULL CHECK (source IN ('tce_sp', 'tce_rs')),
  "snapshotId" text NOT NULL,
  "methodologyVersion" text NOT NULL,
  "createdAt" timestamptz NOT NULL,
  UNIQUE ("licitacaoId", "itemLote", participante, source)
);

CREATE INDEX IF NOT EXISTS licitacao_participante_lic_idx ON licitacao_participante ("licitacaoId");
CREATE INDEX IF NOT EXISTS licitacao_participante_uf_idx ON licitacao_participante (uf);
CREATE INDEX IF NOT EXISTS licitacao_participante_source_idx ON licitacao_participante (source);

CREATE TABLE IF NOT EXISTS co_bid_edge (
  kind text NOT NULL CHECK (kind IN ('co_bid')),
  "leftCnpj" text NOT NULL,
  "rightCnpj" text NOT NULL,
  "licitacaoId" text NOT NULL,
  "itemLote" text NOT NULL DEFAULT '',
  "leftProposta" numeric(18, 6),
  "rightProposta" numeric(18, 6),
  winner text NOT NULL DEFAULT '',
  "snapshotId" text NOT NULL,
  "methodologyVersion" text NOT NULL,
  "createdAt" timestamptz NOT NULL,
  PRIMARY KEY (kind, "leftCnpj", "rightCnpj", "licitacaoId", "itemLote"),
  CONSTRAINT co_bid_edge_left_lt_right CHECK ("leftCnpj" < "rightCnpj" COLLATE "C")
);

ALTER TABLE co_bid_edge DROP CONSTRAINT IF EXISTS co_bid_edge_check;
ALTER TABLE co_bid_edge DROP CONSTRAINT IF EXISTS co_bid_edge_left_lt_right;
ALTER TABLE co_bid_edge ADD CONSTRAINT co_bid_edge_left_lt_right CHECK ("leftCnpj" < "rightCnpj" COLLATE "C");

CREATE INDEX IF NOT EXISTS co_bid_edge_lic_idx ON co_bid_edge ("licitacaoId");
CREATE INDEX IF NOT EXISTS co_bid_edge_left_idx ON co_bid_edge ("leftCnpj");
CREATE INDEX IF NOT EXISTS co_bid_edge_right_idx ON co_bid_edge ("rightCnpj");

CREATE TABLE IF NOT EXISTS co_bid_screen (
  id uuid PRIMARY KEY,
  kind text NOT NULL CHECK (kind IN (
    'bid_variance', 'skew', 'cover_bidding', 'winner_rotation'
  )),
  state text NOT NULL CHECK (state IN (
    'detected', 'internal_review', 'notified', 'published', 'resolved', 'retracted'
  )),
  "subjectId" text NOT NULL,
  "licitacaoId" text NOT NULL,
  evidence text NOT NULL,
  "snapshotId" text NOT NULL,
  "methodologyVersion" text NOT NULL,
  "createdAt" timestamptz NOT NULL,
  "updatedAt" timestamptz NOT NULL,
  UNIQUE (kind, "subjectId", "snapshotId")
);

CREATE INDEX IF NOT EXISTS co_bid_screen_kind_idx ON co_bid_screen (kind);
CREATE INDEX IF NOT EXISTS co_bid_screen_subject_idx ON co_bid_screen ("subjectId");
CREATE INDEX IF NOT EXISTS co_bid_screen_state_idx ON co_bid_screen (state);

ALTER TABLE item ADD COLUMN IF NOT EXISTS "valorPorUnidadeCanonica" numeric(18, 6);
ALTER TABLE item ADD COLUMN IF NOT EXISTS "specConcentracao" text;
ALTER TABLE item ADD COLUMN IF NOT EXISTS "specDosagem" text;
ALTER TABLE item ADD COLUMN IF NOT EXISTS "specTamanho" text;
ALTER TABLE flag ADD COLUMN IF NOT EXISTS "notifyArtifact" text;

CREATE TABLE IF NOT EXISTS flag_audit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "flagId" uuid NOT NULL REFERENCES flag (id),
  "fromState" text CHECK ("fromState" IS NULL OR "fromState" IN (
    'detected', 'internal_review', 'notified', 'published', 'resolved', 'retracted'
  )),
  "toState" text NOT NULL CHECK ("toState" IN (
    'detected', 'internal_review', 'notified', 'published', 'resolved', 'retracted'
  )),
  at timestamptz NOT NULL,
  actor text NOT NULL DEFAULT 'internal/staging',
  reason text,
  delta text
);

CREATE INDEX IF NOT EXISTS flag_audit_flag_idx ON flag_audit ("flagId");
CREATE INDEX IF NOT EXISTS flag_audit_at_idx ON flag_audit (at);

CREATE OR REPLACE FUNCTION flag_enforce_state() RETURNS trigger AS $flag_state$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.state IS DISTINCT FROM 'detected' THEN
      RAISE EXCEPTION 'illegal flag state transition: -> %', NEW.state;
    END IF;
    INSERT INTO flag_audit ("flagId", "fromState", "toState", at, actor, delta)
    VALUES (NEW.id, NULL, NEW.state, NEW."createdAt", 'internal/staging', NEW.delta);
    RETURN NEW;
  END IF;
  IF NEW.state IS NOT DISTINCT FROM OLD.state THEN
    RETURN NEW;
  END IF;
  IF (OLD.state = 'detected' AND NEW.state = 'internal_review')
     OR (OLD.state = 'internal_review' AND NEW.state = 'notified')
     OR (OLD.state = 'notified' AND NEW.state = 'published')
     OR (OLD.state = 'published' AND NEW.state IN ('resolved', 'retracted')) THEN
    INSERT INTO flag_audit ("flagId", "fromState", "toState", at, actor)
    VALUES (NEW.id, OLD.state, NEW.state, NEW."updatedAt", 'internal/staging');
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'illegal flag state transition: % -> %', OLD.state, NEW.state;
END;
$flag_state$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS flag_enforce_state ON flag;
CREATE TRIGGER flag_enforce_state
AFTER INSERT OR UPDATE OF state ON flag
FOR EACH ROW
EXECUTE FUNCTION flag_enforce_state();
