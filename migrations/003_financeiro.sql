CREATE TABLE IF NOT EXISTS financeiros (
  id              SERIAL PRIMARY KEY,
  processo_id     INTEGER NOT NULL REFERENCES processos(id) ON DELETE RESTRICT,
  descricao       TEXT NOT NULL,
  tipo            TEXT NOT NULL CHECK (tipo IN ('honorario','reembolso','outro')),
  valor_total     NUMERIC(12,2) NOT NULL CHECK (valor_total > 0),
  num_parcelas    INTEGER NOT NULL DEFAULT 1 CHECK (num_parcelas >= 1),
  status          TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente','pago_parcial','pago','cancelado')),
  observacoes     TEXT,
  criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parcelas (
  id              SERIAL PRIMARY KEY,
  financeiro_id   INTEGER NOT NULL REFERENCES financeiros(id) ON DELETE CASCADE,
  numero          INTEGER NOT NULL,
  valor           NUMERIC(12,2) NOT NULL CHECK (valor > 0),
  vencimento      DATE NOT NULL,
  status          TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente','pago','cancelado')),
  pago_em         TIMESTAMPTZ,
  UNIQUE (financeiro_id, numero)
);

CREATE INDEX IF NOT EXISTS idx_financeiros_processo ON financeiros(processo_id);
CREATE INDEX IF NOT EXISTS idx_parcelas_financeiro  ON parcelas(financeiro_id);
CREATE INDEX IF NOT EXISTS idx_parcelas_vencimento  ON parcelas(vencimento);
