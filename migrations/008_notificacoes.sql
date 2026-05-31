CREATE TABLE IF NOT EXISTS notificacoes (
  id          SERIAL PRIMARY KEY,
  usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  tipo        TEXT NOT NULL,
  titulo      TEXT NOT NULL,
  corpo       TEXT,
  lida        BOOLEAN NOT NULL DEFAULT FALSE,
  link        TEXT,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario ON notificacoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_notificacoes_lida    ON notificacoes(usuario_id, lida);
