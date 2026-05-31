CREATE TABLE IF NOT EXISTS usuarios (
  id                SERIAL PRIMARY KEY,
  nome              VARCHAR(200) NOT NULL,
  email             VARCHAR(200) UNIQUE NOT NULL,
  senha_hash        TEXT NOT NULL,
  tipo              VARCHAR(20) NOT NULL DEFAULT 'usuario',
  ativo             BOOLEAN NOT NULL DEFAULT false,
  acesso_financeiro BOOLEAN NOT NULL DEFAULT false,
  pode_excluir      BOOLEAN NOT NULL DEFAULT false,
  foto_perfil_url   TEXT,
  criado_em         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_tipo CHECK (tipo IN ('admin', 'usuario'))
);

-- Tabela de sessões requerida pelo connect-pg-simple
CREATE TABLE IF NOT EXISTS sessions (
  sid    VARCHAR NOT NULL PRIMARY KEY,
  sess   JSON NOT NULL,
  expire TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expire_idx ON sessions (expire);
