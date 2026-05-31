CREATE TABLE IF NOT EXISTS atendimentos (
  id           SERIAL PRIMARY KEY,
  cliente_id   INTEGER NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
  processo_id  INTEGER REFERENCES processos(id) ON DELETE SET NULL,
  usuario_id   INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  tipo         TEXT NOT NULL CHECK (tipo IN ('presencial','telefone','email','whatsapp','videoconferencia','outro')),
  data_hora    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  duracao_min  INTEGER CHECK (duracao_min > 0),
  assunto      TEXT NOT NULL,
  descricao    TEXT,
  resultado    TEXT,
  criado_em    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_atendimentos_cliente  ON atendimentos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_atendimentos_processo ON atendimentos(processo_id);
CREATE INDEX IF NOT EXISTS idx_atendimentos_data     ON atendimentos(data_hora);
