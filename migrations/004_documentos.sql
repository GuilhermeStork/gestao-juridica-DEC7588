CREATE TABLE IF NOT EXISTS documentos (
  id              SERIAL PRIMARY KEY,
  processo_id     INTEGER NOT NULL REFERENCES processos(id) ON DELETE RESTRICT,
  nome            TEXT NOT NULL,
  tipo            TEXT NOT NULL CHECK (tipo IN ('gerado','upload')),
  url             TEXT,
  mime_type       TEXT,
  criado_por      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documentos_processo ON documentos(processo_id);
