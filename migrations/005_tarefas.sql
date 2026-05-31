CREATE TABLE IF NOT EXISTS tarefas (
  id              SERIAL PRIMARY KEY,
  titulo          TEXT NOT NULL,
  descricao       TEXT,
  processo_id     INTEGER REFERENCES processos(id) ON DELETE SET NULL,
  atribuido_para  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  criado_por      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  data_vencimento TIMESTAMPTZ,
  prioridade      TEXT NOT NULL DEFAULT 'normal' CHECK (prioridade IN ('baixa','normal','alta','urgente')),
  status          TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente','em_andamento','concluida','cancelada')),
  recorrencia     TEXT CHECK (recorrencia IN ('diaria','semanal','mensal')),
  concluida_em    TIMESTAMPTZ,
  criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tarefas_atribuido  ON tarefas(atribuido_para);
CREATE INDEX IF NOT EXISTS idx_tarefas_processo    ON tarefas(processo_id);
CREATE INDEX IF NOT EXISTS idx_tarefas_vencimento  ON tarefas(data_vencimento);
CREATE INDEX IF NOT EXISTS idx_tarefas_status      ON tarefas(status);
