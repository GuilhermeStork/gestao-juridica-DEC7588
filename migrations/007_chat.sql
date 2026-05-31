CREATE TABLE IF NOT EXISTS conversas (
  id          SERIAL PRIMARY KEY,
  nome        TEXT,
  processo_id INTEGER REFERENCES processos(id) ON DELETE SET NULL,
  cliente_id  INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
  criado_por  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversa_participantes (
  conversa_id   INTEGER NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
  usuario_id    INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  ultima_leitura TIMESTAMPTZ,
  entrou_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (conversa_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS mensagens (
  id          SERIAL PRIMARY KEY,
  conversa_id INTEGER NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
  usuario_id  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  conteudo    TEXT NOT NULL,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_criado   ON mensagens(criado_em);
CREATE INDEX IF NOT EXISTS idx_participantes_usuario ON conversa_participantes(usuario_id);
