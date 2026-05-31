CREATE TABLE IF NOT EXISTS clientes (
  id              SERIAL PRIMARY KEY,
  nome            VARCHAR(300) NOT NULL,
  cpf             VARCHAR(14) NOT NULL,
  rg              VARCHAR(20),
  email           VARCHAR(200),
  telefone        VARCHAR(30),
  endereco        TEXT,
  criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS processos (
  id               SERIAL PRIMARY KEY,
  cliente_id       INTEGER NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
  nome             VARCHAR(300) NOT NULL,
  numero_processo  VARCHAR(100),
  vara             VARCHAR(200),
  comarca          VARCHAR(200),
  area             VARCHAR(100),
  status           VARCHAR(50) NOT NULL DEFAULT 'ativo',
  criado_em        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_status_processo CHECK (status IN ('ativo', 'arquivado', 'encerrado'))
);

CREATE INDEX IF NOT EXISTS processos_cliente_idx ON processos (cliente_id);
