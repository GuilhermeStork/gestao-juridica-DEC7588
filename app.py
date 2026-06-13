import os
import glob
import time
from datetime import date, datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
import streamlit as st

load_dotenv()

# ── conexão ──────────────────────────────────────────────────────────────────

def get_conn():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "controladoria"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        row_factory=dict_row,
    )

def get_readonly_conn():
    conn = get_conn()
    conn.read_only = True
    return conn

def fetch(sql, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
            return cur.fetchall()

def execute(sql, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
        conn.commit()

# ── seed ─────────────────────────────────────────────────────────────────────

def run_seed():
    existing = fetch("SELECT 1 FROM usuarios WHERE email='admin@gestao-juridica.dev' LIMIT 1")
    if existing:
        st.warning("Dados de exemplo já existem. Use 'Apagar tudo' antes de popular novamente.")
        return
    with get_conn() as conn:
        with conn.cursor() as cur:
            # usuarios
            cur.execute("""
                INSERT INTO usuarios (nome, email, senha_hash, tipo, ativo, acesso_financeiro, pode_excluir) VALUES
                ('Administrador',  'admin@gestao-juridica.dev', 'hash_placeholder', 'admin',   true, true,  true),
                ('Ana Paula Souza','ana@gestao-juridica.dev',   'hash_placeholder', 'usuario', true, true,  false),
                ('Carlos Mendes',  'carlos@gestao-juridica.dev','hash_placeholder', 'usuario', true, false, false)
                ON CONFLICT (email) DO NOTHING
            """)

            # clientes
            cur.execute("""
                INSERT INTO clientes (nome, cpf, email, telefone, endereco) VALUES
                ('Roberto Alves Lima',      '111.222.333-44', 'roberto@email.com',  '(48) 99111-2222', 'Rua das Flores, 100 – Florianópolis/SC'),
                ('Mariana Costa Ferreira',  '222.333.444-55', 'mariana@email.com',  '(48) 99222-3333', 'Av. Beira Mar, 200 – Florianópolis/SC'),
                ('Pedro Henrique Santos',   '333.444.555-66', 'pedro@email.com',    '(48) 99333-4444', 'Rua Bocaiúva, 300 – Florianópolis/SC'),
                ('Fernanda Oliveira Dias',  '444.555.666-77', 'fernanda@email.com', '(48) 99444-5555', 'Rua Tenente Silveira, 400 – Florianópolis/SC'),
                ('Luiz Eduardo Martins',    '555.666.777-88', 'luiz@email.com',     '(48) 99555-6666', 'Av. Mauro Ramos, 500 – Florianópolis/SC')
                ON CONFLICT DO NOTHING
            """)

            cur.execute("SELECT id FROM clientes ORDER BY id LIMIT 5")
            cids = [r["id"] for r in cur.fetchall()]
            if len(cids) < 5:
                st.error("Seed parcial detectado — use 'Apagar todas as tabelas' antes de popular novamente.")
                conn.rollback()
                return
            c1, c2, c3, c4, c5 = cids

            # processos
            cur.execute("""
                INSERT INTO processos (cliente_id, nome, numero_processo, vara, comarca, area, status) VALUES
                (%s, 'Reclamação Trabalhista - Verbas Rescisórias',    '0001234-10.2023.5.12.0001', '1ª Vara do Trabalho', 'Florianópolis', 'Trabalhista', 'ativo'),
                (%s, 'Ação Trabalhista - Horas Extras',                '0001235-20.2023.5.12.0001', '2ª Vara do Trabalho', 'Florianópolis', 'Trabalhista', 'ativo'),
                (%s, 'Divórcio Consensual',                            '0002100-30.2023.8.24.0090', '1ª Vara de Família',  'Florianópolis', 'Família',    'ativo'),
                (%s, 'Guarda e Alimentos',                             '0002101-40.2023.8.24.0090', '2ª Vara de Família',  'Florianópolis', 'Família',    'ativo'),
                (%s, 'Indenização por Danos Morais',                   '0003000-50.2023.8.24.0090', '3ª Vara Cível',       'Florianópolis', 'Cível',      'ativo'),
                (%s, 'Cobrança de Contrato',                           '0003001-60.2022.8.24.0090', '4ª Vara Cível',       'Florianópolis', 'Cível',      'arquivado'),
                (%s, 'Inventário e Partilha',                          '0004000-70.2023.8.24.0090', '1ª Vara de Família',  'Florianópolis', 'Sucessões',  'ativo'),
                (%s, 'Usucapião Especial Urbana',                      '0005000-80.2023.8.24.0090', '1ª Vara de Registros','Florianópolis', 'Imobiliário','ativo'),
                (%s, 'Regularização de Imóvel',                       '0005001-90.2022.8.24.0090', '2ª Vara Cível',       'Florianópolis', 'Imobiliário','encerrado'),
                (%s, 'Revisão de Contrato Bancário',                   '0006000-00.2023.8.24.0090', '5ª Vara Cível',       'Florianópolis', 'Bancário',   'ativo')
            """, [c1,c1, c2,c2, c3,c3, c4, c5,c5, c4])

            cur.execute("SELECT id FROM processos ORDER BY id LIMIT 10")
            pids = [r["id"] for r in cur.fetchall()]
            if len(pids) < 10:
                st.error("Seed parcial detectado — use 'Apagar todas as tabelas' antes de popular novamente.")
                conn.rollback()
                return

            # financeiros (10) + parcelas automáticas
            financeiros_data = [
                (pids[0], 'Honorários advocatícios',           'honorario', 6000.00, 3),
                (pids[1], 'Honorários ação horas extras',      'honorario', 4500.00, 3),
                (pids[2], 'Honorários divórcio',               'honorario', 3000.00, 2),
                (pids[3], 'Honorários guarda e alimentos',     'honorario', 2400.00, 2),
                (pids[4], 'Honorários danos morais',           'honorario', 5000.00, 5),
                (pids[6], 'Honorários inventário',             'honorario', 8000.00, 4),
                (pids[7], 'Honorários usucapião',              'honorario', 7500.00, 3),
                (pids[9], 'Honorários revisão contrato',       'honorario', 3500.00, 2),
                (pids[0], 'Reembolso custas processuais',      'reembolso',  800.00, 1),
                (pids[1], 'Reembolso despesas cartorárias',    'reembolso', 1200.00, 1),
            ]
            for proc_id, desc, tipo, valor, nparcelas in financeiros_data:
                cur.execute("""
                    INSERT INTO financeiros (processo_id, descricao, tipo, valor_total, num_parcelas)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, [proc_id, desc, tipo, valor, nparcelas])
                fid = cur.fetchone()["id"]
                valor_parcela = round(valor / nparcelas, 2)
                for i in range(1, nparcelas + 1):
                    venc = date(2024, i % 12 + 1, 10)
                    status = "pendente" if i == nparcelas else "pago"
                    pago_em = datetime(2024, i % 12 + 1, 8) if status == "pago" else None
                    cur.execute("""
                        INSERT INTO parcelas (financeiro_id, numero, valor, vencimento, status, pago_em)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [fid, i, valor_parcela, venc, status, pago_em])

            cur.execute("SELECT id FROM usuarios WHERE email = 'ana@gestao-juridica.dev'")
            ana_id = cur.fetchone()["id"]
            cur.execute("SELECT id FROM usuarios WHERE email = 'carlos@gestao-juridica.dev'")
            carlos_id = cur.fetchone()["id"]

            # tarefas (10)
            tarefas = [
                ('Analisar documentos trabalhistas',   pids[0], ana_id,    ana_id,    '2024-06-15', 'alta',    'concluida'),
                ('Elaborar petição inicial',            pids[1], ana_id,    ana_id,    '2024-07-01', 'urgente', 'em_andamento'),
                ('Coletar documentos do divórcio',      pids[2], carlos_id, carlos_id, '2024-07-10', 'normal',  'pendente'),
                ('Agendar audiência de conciliação',    pids[3], carlos_id, carlos_id, '2024-07-20', 'alta',    'pendente'),
                ('Pesquisar jurisprudência',            pids[4], ana_id,    ana_id,    '2024-06-30', 'normal',  'concluida'),
                ('Preparar memorial descritivo',        pids[6], carlos_id, carlos_id, '2024-08-01', 'alta',    'em_andamento'),
                ('Obter certidões de óbito',            pids[6], ana_id,    carlos_id, '2024-07-05', 'urgente', 'concluida'),
                ('Vistoria do imóvel',                  pids[7], carlos_id, ana_id,    '2024-08-15', 'normal',  'pendente'),
                ('Analisar contrato bancário',          pids[9], ana_id,    ana_id,    '2024-07-25', 'alta',    'em_andamento'),
                ('Protocolar petição de revisão',       pids[9], carlos_id, carlos_id, '2024-08-10', 'urgente', 'cancelada'),
            ]
            for titulo, proc_id, atrib, criador, venc, prio, status in tarefas:
                cur.execute("""
                    INSERT INTO tarefas (titulo, processo_id, atribuido_para, criado_por, data_vencimento, prioridade, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, [titulo, proc_id, atrib, criador, venc, prio, status])

            # atendimentos (10)
            cur.execute("SELECT id FROM usuarios WHERE tipo='admin' LIMIT 1")
            admin_id = cur.fetchone()["id"]
            atendimentos = [
                (c1, pids[0],  ana_id,    'presencial',      '2024-05-10 09:00', 60,  'Triagem do caso trabalhista',       'Análise de documentos',           'Caso aceito'),
                (c2, pids[2],  ana_id,    'presencial',      '2024-05-12 14:00', 45,  'Consulta sobre divórcio',           'Orientação sobre processo',       'Documentos solicitados'),
                (c3, pids[4],  carlos_id, 'presencial',      '2024-05-15 10:00', 90,  'Análise de danos morais',           'Avaliação do caso',               'Petição em elaboração'),
                (c4, pids[6],  carlos_id, 'presencial',      '2024-05-20 11:00', 60,  'Inventário dos bens',               'Levantamento patrimonial',        'Certidões solicitadas'),
                (c5, pids[7],  ana_id,    'presencial',      '2024-05-22 15:00', 75,  'Usucapião - documentos',            'Análise da posse',                'Parecer favorável'),
                (c1, pids[1],  carlos_id, 'telefone',        '2024-06-01 08:30', 20,  'Andamento da ação trabalhista',     'Atualização processual',          'Aguardando audiência'),
                (c3, pids[5],  ana_id,    'telefone',        '2024-06-05 16:00', 15,  'Cobrança arquivada',               'Esclarecimento sobre arquivo',    'Cliente ciente'),
                (c2, pids[3],  admin_id,  'email',           '2024-06-10 09:00', 10,  'Alimentos provisórios',            'Resposta sobre pedido urgente',   'Petição protocolada'),
                (c4, pids[9],  carlos_id, 'videoconferencia','2024-06-15 14:00', 50,  'Revisão do contrato bancário',     'Explicação das cláusulas abusivas','Recurso em preparação'),
                (c5, pids[8],  ana_id,    'whatsapp',        '2024-06-20 10:00', 10,  'Regularização encerrada',          'Entrega dos documentos finais',   'Processo encerrado'),
            ]
            for cli, proc, usr, tipo, data_hora, dur, assunto, desc, result in atendimentos:
                cur.execute("""
                    INSERT INTO atendimentos (cliente_id, processo_id, usuario_id, tipo, data_hora, duracao_min, assunto, descricao, resultado)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, [cli, proc, usr, tipo, data_hora, dur, assunto, desc, result])

            # notificacoes (5)
            notifs = [
                (admin_id,   'sistema', 'Banco populado com sucesso',              'Dados de exemplo inseridos.',          True),
                (ana_id,     'tarefa',  'Nova tarefa atribuída',                   'Elaborar petição inicial (urgente).',  False),
                (carlos_id,  'tarefa',  'Tarefa concluída',                        'Obter certidões de óbito marcada OK.', True),
                (ana_id,     'sistema', 'Audiência agendada',                      'Audiência marcada para 15/07.',        False),
                (carlos_id,  'sistema', 'Documento pendente de revisão',           'Verifique o memorial descritivo.',     False),
            ]
            for uid, tipo, titulo, corpo, lida in notifs:
                cur.execute("""
                    INSERT INTO notificacoes (usuario_id, tipo, titulo, corpo, lida)
                    VALUES (%s,%s,%s,%s,%s)
                """, [uid, tipo, titulo, corpo, lida])

            # documentos (5)
            documentos = [
                (pids[0], 'Procuração - Roberto Alves',     'gerado', 'https://docs.exemplo/proc-roberto.pdf',  'application/pdf', admin_id),
                (pids[0], 'Contrato de honorários',          'gerado', 'https://docs.exemplo/contrato-hon.pdf',  'application/pdf', ana_id),
                (pids[2], 'Certidão de casamento',           'upload', 'https://docs.exemplo/cert-casamento.pdf','application/pdf', carlos_id),
                (pids[4], 'Petição inicial - danos morais',  'gerado', 'https://docs.exemplo/peticao-danos.pdf', 'application/pdf', ana_id),
                (pids[6], 'Certidão de óbito',               'upload', 'https://docs.exemplo/cert-obito.pdf',    'application/pdf', carlos_id),
            ]
            for proc_id, nome, tipo, url, mime, criador in documentos:
                cur.execute("""
                    INSERT INTO documentos (processo_id, nome, tipo, url, mime_type, criado_por)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, [proc_id, nome, tipo, url, mime, criador])

            # conversas (3) + participantes + mensagens
            conversas = [
                ('Caso Trabalhista - Roberto',   pids[0], c1,   admin_id,  [admin_id, ana_id]),
                ('Divórcio Consensual - Pedro',  pids[2], c3,   carlos_id, [carlos_id, ana_id]),
                ('Equipe Interna',               None,    None, admin_id,  [admin_id, ana_id, carlos_id]),
            ]
            mensagens_por_conversa = [
                [(admin_id, 'Pessoal, abri esta conversa para acompanharmos o caso do Roberto.'),
                 (ana_id,   'Perfeito. Já analisei os documentos, vou elaborar a petição inicial.')],
                [(carlos_id,'O cliente trouxe a certidão de casamento hoje.'),
                 (ana_id,   'Ótimo, podemos protocolar o divórcio na próxima semana.')],
                [(admin_id, 'Bom dia, equipe! Reunião de alinhamento às 14h.'),
                 (carlos_id,'Combinado, estarei lá.'),
                 (ana_id,   'Presente.')],
            ]
            for (nome, proc_id, cli_id, criador, participantes), msgs in zip(conversas, mensagens_por_conversa):
                cur.execute("""
                    INSERT INTO conversas (nome, processo_id, cliente_id, criado_por)
                    VALUES (%s,%s,%s,%s) RETURNING id
                """, [nome, proc_id, cli_id, criador])
                conv_id = cur.fetchone()["id"]
                for uid in participantes:
                    cur.execute("""
                        INSERT INTO conversa_participantes (conversa_id, usuario_id)
                        VALUES (%s,%s) ON CONFLICT DO NOTHING
                    """, [conv_id, uid])
                for autor, conteudo in msgs:
                    cur.execute("""
                        INSERT INTO mensagens (conversa_id, usuario_id, conteudo)
                        VALUES (%s,%s,%s)
                    """, [conv_id, autor, conteudo])

        conn.commit()

# ── helpers de UI ─────────────────────────────────────────────────────────────

def show_df(rows):
    if not rows:
        st.info("Nenhum registro encontrado.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

def _opts(rows, id_col, label_col):
    """Retorna dict {label: id} para st.selectbox."""
    return {f"{r[id_col]} – {r[label_col]}": r[id_col] for r in rows}

# ── SEÇÃO: Configuração do Banco ──────────────────────────────────────────────

def page_config():
    st.header("Configuração do Banco")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Criar tabelas", use_container_width=True):
            migration_dir = os.path.join(os.path.dirname(__file__), "migrations")
            files = sorted(glob.glob(os.path.join(migration_dir, "*.sql")))
            try:
                with get_conn() as conn:
                    with conn.cursor() as cur:
                        for f in files:
                            sql = open(f).read()
                            cur.execute(sql)
                    conn.commit()
                st.success(f"{len(files)} arquivos de migração executados.")
            except Exception as e:
                st.error(str(e))

    with col2:
        if st.button("Popular dados de exemplo", use_container_width=True):
            try:
                run_seed()
                st.success("Dados de exemplo inseridos com sucesso.")
            except Exception as e:
                st.error(str(e))

    with col3:
        if st.button("Apagar todas as tabelas", use_container_width=True, type="primary"):
            try:
                execute("""
                    DROP TABLE IF EXISTS
                        notificacoes, mensagens, conversa_participantes, conversas,
                        atendimentos, tarefas, documentos, parcelas, financeiros,
                        processos, clientes, usuarios
                    CASCADE
                """)
                st.success("Todas as tabelas foram removidas.")
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Usuários ───────────────────────────────────────────────────────────

def page_usuarios():
    st.header("Usuários")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])

    with tabs[0]:
        show_df(fetch("SELECT id, nome, email, tipo, ativo, acesso_financeiro, pode_excluir, foto_perfil_url, criado_em FROM usuarios ORDER BY id"))

    with tabs[1]:
        with st.form("ins_usuario"):
            nome  = st.text_input("Nome")
            email = st.text_input("E-mail")
            tipo  = st.selectbox("Tipo", ["usuario", "admin"])
            ativo = st.checkbox("Ativo", value=True)
            af    = st.checkbox("Acesso financeiro")
            pe    = st.checkbox("Pode excluir")
            foto  = st.text_input("Foto de perfil (URL)")
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO usuarios (nome, email, senha_hash, tipo, ativo, acesso_financeiro, pode_excluir, foto_perfil_url)
                        VALUES (%s,%s,'hash_placeholder',%s,%s,%s,%s,%s)
                    """, [nome, email, tipo, ativo, af, pe, foto or None])
                    st.success("Usuário inserido.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows = fetch("SELECT id, nome FROM usuarios ORDER BY id")
        opts = _opts(rows, "id", "nome")
        sel  = st.selectbox("Selecionar usuário", list(opts.keys()), key="sel_upd_usr")
        if sel:
            uid  = opts[sel]
            rec  = fetch("SELECT * FROM usuarios WHERE id=%s", [uid])[0]
            with st.form("upd_usuario"):
                nome  = st.text_input("Nome",  value=rec["nome"])
                email = st.text_input("E-mail", value=rec["email"])
                tipo  = st.selectbox("Tipo", ["usuario","admin"], index=["usuario","admin"].index(rec["tipo"]))
                ativo = st.checkbox("Ativo", value=rec["ativo"])
                af    = st.checkbox("Acesso financeiro", value=rec["acesso_financeiro"])
                pe    = st.checkbox("Pode excluir", value=rec["pode_excluir"])
                foto  = st.text_input("Foto de perfil (URL)", value=rec["foto_perfil_url"] or "")
                if st.form_submit_button("Atualizar"):
                    try:
                        execute("""
                            UPDATE usuarios SET nome=%s, email=%s, tipo=%s, ativo=%s,
                            acesso_financeiro=%s, pode_excluir=%s, foto_perfil_url=%s WHERE id=%s
                        """, [nome, email, tipo, ativo, af, pe, foto or None, uid])
                        st.success("Usuário atualizado.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT id, nome FROM usuarios ORDER BY id")
        opts = _opts(rows, "id", "nome")
        sel  = st.selectbox("Selecionar usuário", list(opts.keys()), key="sel_del_usr")
        if sel and st.button("Excluir usuário", type="primary"):
            try:
                execute("DELETE FROM usuarios WHERE id=%s", [opts[sel]])
                st.success("Usuário excluído.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Clientes ───────────────────────────────────────────────────────────

def page_clientes():
    st.header("Clientes")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])

    with tabs[0]:
        show_df(fetch("SELECT * FROM clientes ORDER BY id"))

    with tabs[1]:
        with st.form("ins_cliente"):
            nome     = st.text_input("Nome completo")
            cpf      = st.text_input("CPF")
            rg       = st.text_input("RG")
            email    = st.text_input("E-mail")
            telefone = st.text_input("Telefone")
            endereco = st.text_area("Endereço")
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO clientes (nome, cpf, rg, email, telefone, endereco)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, [nome, cpf, rg or None, email, telefone, endereco])
                    st.success("Cliente inserido.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows = fetch("SELECT id, nome FROM clientes ORDER BY id")
        opts = _opts(rows, "id", "nome")
        sel  = st.selectbox("Selecionar cliente", list(opts.keys()), key="sel_upd_cli")
        if sel:
            cid = opts[sel]
            rec = fetch("SELECT * FROM clientes WHERE id=%s", [cid])[0]
            with st.form("upd_cliente"):
                nome     = st.text_input("Nome",     value=rec["nome"])
                cpf      = st.text_input("CPF",      value=rec["cpf"] or "")
                rg       = st.text_input("RG",       value=rec["rg"] or "")
                email    = st.text_input("E-mail",   value=rec["email"] or "")
                telefone = st.text_input("Telefone", value=rec["telefone"] or "")
                endereco = st.text_area("Endereço",  value=rec["endereco"] or "")
                if st.form_submit_button("Atualizar"):
                    try:
                        execute("""
                            UPDATE clientes SET nome=%s, cpf=%s, rg=%s, email=%s, telefone=%s, endereco=%s
                            WHERE id=%s
                        """, [nome, cpf, rg or None, email, telefone, endereco, cid])
                        st.success("Cliente atualizado.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT id, nome FROM clientes ORDER BY id")
        opts = _opts(rows, "id", "nome")
        sel  = st.selectbox("Selecionar cliente", list(opts.keys()), key="sel_del_cli")
        if sel and st.button("Excluir cliente", type="primary"):
            try:
                execute("DELETE FROM clientes WHERE id=%s", [opts[sel]])
                st.success("Cliente excluído.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Processos ──────────────────────────────────────────────────────────

AREAS = ['Cível','Trabalhista','Família','Criminal','Tributário','Imobiliário','Sucessões','Bancário','Ambiental','Outro']
STATUS_PROC = ['ativo','arquivado','encerrado']

def page_processos():
    st.header("Processos")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    clientes = fetch("SELECT id, nome FROM clientes ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT p.id, c.nome AS cliente, p.nome, p.numero_processo,
                   p.vara, p.comarca, p.area, p.status, p.criado_em
            FROM processos p JOIN clientes c ON c.id=p.cliente_id ORDER BY p.id
        """))

    with tabs[1]:
        opts_c = _opts(clientes, "id", "nome")
        with st.form("ins_processo"):
            cli_sel       = st.selectbox("Cliente", list(opts_c.keys()))
            nome          = st.text_input("Nome do processo")
            num_processo  = st.text_input("Número do processo")
            vara          = st.text_input("Vara")
            comarca       = st.text_input("Comarca")
            area          = st.selectbox("Área", AREAS)
            status        = st.selectbox("Status", STATUS_PROC)
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO processos (cliente_id, nome, numero_processo, vara, comarca, area, status)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, [opts_c[cli_sel], nome, num_processo, vara, comarca, area, status])
                    st.success("Processo inserido.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows = fetch("SELECT id, nome FROM processos ORDER BY id")
        opts = _opts(rows, "id", "nome")
        opts_c = _opts(clientes, "id", "nome")
        sel  = st.selectbox("Selecionar processo", list(opts.keys()), key="sel_upd_proc")
        if sel:
            pid = opts[sel]
            rec = fetch("SELECT * FROM processos WHERE id=%s", [pid])[0]
            cli_labels = list(opts_c.keys())
            cli_key    = next((k for k,v in opts_c.items() if v == rec["cliente_id"]), cli_labels[0])
            with st.form("upd_processo"):
                cli_sel      = st.selectbox("Cliente", cli_labels, index=cli_labels.index(cli_key))
                nome         = st.text_input("Nome",            value=rec["nome"])
                num_processo = st.text_input("Número",          value=rec["numero_processo"] or "")
                vara         = st.text_input("Vara",            value=rec["vara"] or "")
                comarca      = st.text_input("Comarca",         value=rec["comarca"] or "")
                area         = st.selectbox("Área", AREAS,      index=AREAS.index(rec["area"]) if rec["area"] in AREAS else 0)
                status       = st.selectbox("Status", STATUS_PROC, index=STATUS_PROC.index(rec["status"]) if rec["status"] in STATUS_PROC else 0)
                if st.form_submit_button("Atualizar"):
                    try:
                        execute("""
                            UPDATE processos SET cliente_id=%s, nome=%s, numero_processo=%s,
                            vara=%s, comarca=%s, area=%s, status=%s WHERE id=%s
                        """, [opts_c[cli_sel], nome, num_processo, vara, comarca, area, status, pid])
                        st.success("Processo atualizado.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT id, nome FROM processos ORDER BY id")
        opts = _opts(rows, "id", "nome")
        sel  = st.selectbox("Selecionar processo", list(opts.keys()), key="sel_del_proc")
        if sel and st.button("Excluir processo", type="primary"):
            try:
                execute("DELETE FROM processos WHERE id=%s", [opts[sel]])
                st.success("Processo excluído.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Financeiros ────────────────────────────────────────────────────────

TIPOS_FIN  = ['honorario','reembolso','outro']
STATUS_FIN = ['pendente','pago_parcial','pago','cancelado']

def page_financeiros():
    st.header("Financeiros")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    processos = fetch("SELECT id, nome FROM processos ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT f.id, p.nome AS processo, f.descricao, f.tipo,
                   f.valor_total, f.num_parcelas, f.status, f.criado_em
            FROM financeiros f JOIN processos p ON p.id=f.processo_id ORDER BY f.id
        """))

    with tabs[1]:
        opts_p = _opts(processos, "id", "nome")
        with st.form("ins_fin"):
            proc_sel   = st.selectbox("Processo", list(opts_p.keys()))
            descricao  = st.text_input("Descrição")
            tipo       = st.selectbox("Tipo", TIPOS_FIN)
            valor      = st.number_input("Valor total (R$)", min_value=0.01, step=0.01)
            nparcelas  = st.number_input("Nº de parcelas", min_value=1, step=1, value=1)
            status     = st.selectbox("Status", STATUS_FIN)
            observacoes= st.text_area("Observações")
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO financeiros (processo_id, descricao, tipo, valor_total, num_parcelas, status, observacoes)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, [opts_p[proc_sel], descricao, tipo, valor, int(nparcelas), status, observacoes or None])
                    st.success("Financeiro inserido.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows  = fetch("SELECT id, descricao FROM financeiros ORDER BY id")
        opts  = _opts(rows, "id", "descricao")
        opts_p= _opts(processos, "id", "nome")
        sel   = st.selectbox("Selecionar financeiro", list(opts.keys()), key="sel_upd_fin")
        if sel:
            fid = opts[sel]
            rec = fetch("SELECT * FROM financeiros WHERE id=%s", [fid])[0]
            proc_labels = list(opts_p.keys())
            proc_key    = next((k for k,v in opts_p.items() if v == rec["processo_id"]), proc_labels[0])
            with st.form("upd_fin"):
                proc_sel   = st.selectbox("Processo", proc_labels, index=proc_labels.index(proc_key))
                descricao  = st.text_input("Descrição",  value=rec["descricao"])
                tipo       = st.selectbox("Tipo", TIPOS_FIN, index=TIPOS_FIN.index(rec["tipo"]) if rec["tipo"] in TIPOS_FIN else 0)
                valor      = st.number_input("Valor total (R$)", value=float(rec["valor_total"]), min_value=0.01, step=0.01)
                nparcelas  = st.number_input("Nº de parcelas", value=int(rec["num_parcelas"]), min_value=1, step=1)
                status     = st.selectbox("Status", STATUS_FIN, index=STATUS_FIN.index(rec["status"]) if rec["status"] in STATUS_FIN else 0)
                observacoes= st.text_area("Observações", value=rec["observacoes"] or "")
                if st.form_submit_button("Atualizar"):
                    try:
                        execute("""
                            UPDATE financeiros SET processo_id=%s, descricao=%s, tipo=%s,
                            valor_total=%s, num_parcelas=%s, status=%s, observacoes=%s WHERE id=%s
                        """, [opts_p[proc_sel], descricao, tipo, valor, int(nparcelas), status, observacoes or None, fid])
                        st.success("Financeiro atualizado.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT id, descricao FROM financeiros ORDER BY id")
        opts = _opts(rows, "id", "descricao")
        sel  = st.selectbox("Selecionar financeiro", list(opts.keys()), key="sel_del_fin")
        if sel and st.button("Excluir financeiro", type="primary"):
            try:
                execute("DELETE FROM financeiros WHERE id=%s", [opts[sel]])
                st.success("Financeiro excluído.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Parcelas ───────────────────────────────────────────────────────────

STATUS_PARC = ['pendente','pago','cancelado']

def page_parcelas():
    st.header("Parcelas")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    financeiros = fetch("SELECT id, descricao FROM financeiros ORDER BY id")

    with tabs[0]:
        show_df(fetch("""
            SELECT pa.id, f.descricao AS financeiro, pa.numero, pa.valor,
                   pa.vencimento, pa.status, pa.pago_em
            FROM parcelas pa JOIN financeiros f ON f.id=pa.financeiro_id ORDER BY pa.id
        """))

    with tabs[1]:
        opts_f = _opts(financeiros, "id", "descricao")
        with st.form("ins_parcela"):
            fin_sel   = st.selectbox("Financeiro", list(opts_f.keys()))
            numero    = st.number_input("Número da parcela", min_value=1, step=1)
            valor     = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
            vencimento= st.date_input("Vencimento")
            status    = st.selectbox("Status", STATUS_PARC)
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO parcelas (financeiro_id, numero, valor, vencimento, status)
                        VALUES (%s,%s,%s,%s,%s)
                    """, [opts_f[fin_sel], int(numero), valor, vencimento, status])
                    st.success("Parcela inserida.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows  = fetch("SELECT pa.id, CONCAT(f.descricao,' #',pa.numero) AS label FROM parcelas pa JOIN financeiros f ON f.id=pa.financeiro_id ORDER BY pa.id")
        opts  = _opts(rows, "id", "label")
        opts_f= _opts(financeiros, "id", "descricao")
        sel   = st.selectbox("Selecionar parcela", list(opts.keys()), key="sel_upd_parc")
        if sel:
            pid = opts[sel]
            rec = fetch("SELECT * FROM parcelas WHERE id=%s", [pid])[0]
            fin_labels = list(opts_f.keys())
            fin_key    = next((k for k,v in opts_f.items() if v == rec["financeiro_id"]), fin_labels[0])
            with st.form("upd_parcela"):
                fin_sel   = st.selectbox("Financeiro", fin_labels, index=fin_labels.index(fin_key))
                numero    = st.number_input("Número", value=int(rec["numero"]), min_value=1, step=1)
                valor     = st.number_input("Valor (R$)", value=float(rec["valor"]), min_value=0.01, step=0.01)
                vencimento= st.date_input("Vencimento", value=rec["vencimento"])
                status    = st.selectbox("Status", STATUS_PARC, index=STATUS_PARC.index(rec["status"]) if rec["status"] in STATUS_PARC else 0)
                if st.form_submit_button("Atualizar"):
                    try:
                        if status == "pago" and rec["status"] != "pago":
                            pago_em = datetime.now(timezone.utc)
                        elif status != "pago":
                            pago_em = None
                        else:
                            pago_em = rec["pago_em"]
                        execute("""
                            UPDATE parcelas SET financeiro_id=%s, numero=%s, valor=%s,
                            vencimento=%s, status=%s, pago_em=%s WHERE id=%s
                        """, [opts_f[fin_sel], int(numero), valor, vencimento, status, pago_em, pid])
                        st.success("Parcela atualizada.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT pa.id, CONCAT(f.descricao,' #',pa.numero) AS label FROM parcelas pa JOIN financeiros f ON f.id=pa.financeiro_id ORDER BY pa.id")
        opts = _opts(rows, "id", "label")
        sel  = st.selectbox("Selecionar parcela", list(opts.keys()), key="sel_del_parc")
        if sel and st.button("Excluir parcela", type="primary"):
            try:
                execute("DELETE FROM parcelas WHERE id=%s", [opts[sel]])
                st.success("Parcela excluída.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Documentos ─────────────────────────────────────────────────────────

TIPOS_DOC = ['gerado','upload']

def page_documentos():
    st.header("Documentos")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    processos = fetch("SELECT id, nome FROM processos ORDER BY nome")
    usuarios  = fetch("SELECT id, nome FROM usuarios ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT d.id, p.nome AS processo, u.nome AS criado_por, d.nome,
                   d.tipo, d.url, d.mime_type, d.criado_em
            FROM documentos d
            JOIN processos p ON p.id=d.processo_id
            LEFT JOIN usuarios u ON u.id=d.criado_por
            ORDER BY d.id
        """))

    with tabs[1]:
        opts_p = _opts(processos, "id", "nome")
        opts_u = _opts(usuarios,  "id", "nome")
        with st.form("ins_doc"):
            proc_sel  = st.selectbox("Processo", list(opts_p.keys()))
            usr_sel   = st.selectbox("Criado por", list(opts_u.keys()))
            nome      = st.text_input("Nome do documento")
            tipo      = st.selectbox("Tipo", TIPOS_DOC)
            url       = st.text_input("URL")
            mime_type = st.text_input("MIME type")
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO documentos (processo_id, criado_por, nome, tipo, url, mime_type)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, [opts_p[proc_sel], opts_u[usr_sel], nome, tipo, url or None, mime_type or None])
                    st.success("Documento inserido.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows  = fetch("SELECT id, nome FROM documentos ORDER BY id")
        opts  = _opts(rows, "id", "nome")
        opts_p= _opts(processos, "id", "nome")
        opts_u= _opts(usuarios,  "id", "nome")
        sel   = st.selectbox("Selecionar documento", list(opts.keys()), key="sel_upd_doc")
        if sel:
            did = opts[sel]
            rec = fetch("SELECT * FROM documentos WHERE id=%s", [did])[0]
            proc_labels = list(opts_p.keys())
            usr_labels  = list(opts_u.keys())
            proc_key = next((k for k,v in opts_p.items() if v == rec["processo_id"]), proc_labels[0])
            usr_key  = next((k for k,v in opts_u.items() if v == rec["criado_por"]), usr_labels[0])
            with st.form("upd_doc"):
                proc_sel  = st.selectbox("Processo",    proc_labels, index=proc_labels.index(proc_key))
                usr_sel   = st.selectbox("Criado por",  usr_labels,  index=usr_labels.index(usr_key))
                nome      = st.text_input("Nome",      value=rec["nome"])
                tipo      = st.selectbox("Tipo", TIPOS_DOC, index=TIPOS_DOC.index(rec["tipo"]) if rec["tipo"] in TIPOS_DOC else 0)
                url       = st.text_input("URL",       value=rec["url"] or "")
                mime_type = st.text_input("MIME type", value=rec["mime_type"] or "")
                if st.form_submit_button("Atualizar"):
                    try:
                        execute("""
                            UPDATE documentos SET processo_id=%s, criado_por=%s, nome=%s,
                            tipo=%s, url=%s, mime_type=%s WHERE id=%s
                        """, [opts_p[proc_sel], opts_u[usr_sel], nome, tipo, url or None, mime_type or None, did])
                        st.success("Documento atualizado.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT id, nome FROM documentos ORDER BY id")
        opts = _opts(rows, "id", "nome")
        sel  = st.selectbox("Selecionar documento", list(opts.keys()), key="sel_del_doc")
        if sel and st.button("Excluir documento", type="primary"):
            try:
                execute("DELETE FROM documentos WHERE id=%s", [opts[sel]])
                st.success("Documento excluído.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Tarefas ────────────────────────────────────────────────────────────

PRIORIDADES  = ['baixa','normal','alta','urgente']
STATUS_TAREF = ['pendente','em_andamento','concluida','cancelada']
RECORRENCIAS = ['diaria','semanal','mensal']

def page_tarefas():
    st.header("Tarefas")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    processos = fetch("SELECT id, nome FROM processos ORDER BY nome")
    usuarios  = fetch("SELECT id, nome FROM usuarios ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT t.id, t.titulo, p.nome AS processo, u1.nome AS atribuido, u2.nome AS criado_por,
                   t.data_vencimento, t.prioridade, t.status, t.recorrencia, t.criado_em
            FROM tarefas t
            LEFT JOIN processos p  ON p.id=t.processo_id
            LEFT JOIN usuarios u1  ON u1.id=t.atribuido_para
            LEFT JOIN usuarios u2  ON u2.id=t.criado_por
            ORDER BY t.id
        """))

    with tabs[1]:
        opts_p = _opts(processos, "id", "nome")
        opts_u = _opts(usuarios,  "id", "nome")
        with st.form("ins_tarefa"):
            titulo     = st.text_input("Título")
            descricao  = st.text_area("Descrição")
            proc_sel   = st.selectbox("Processo (opcional)", ["—"] + list(opts_p.keys()))
            atrib_sel  = st.selectbox("Atribuído para", list(opts_u.keys()))
            criador_sel= st.selectbox("Criado por",     list(opts_u.keys()))
            vencimento = st.date_input("Vencimento")
            prioridade = st.selectbox("Prioridade", PRIORIDADES, index=1)
            status     = st.selectbox("Status", STATUS_TAREF)
            recorrencia= st.selectbox("Recorrência", ["—"] + RECORRENCIAS)
            if st.form_submit_button("Inserir"):
                try:
                    proc_id = opts_p[proc_sel] if proc_sel != "—" else None
                    rec_val = recorrencia if recorrencia != "—" else None
                    execute("""
                        INSERT INTO tarefas (titulo, descricao, processo_id, atribuido_para, criado_por, data_vencimento, prioridade, status, recorrencia)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, [titulo, descricao or None, proc_id, opts_u[atrib_sel], opts_u[criador_sel],
                          datetime(vencimento.year, vencimento.month, vencimento.day, tzinfo=timezone.utc),
                          prioridade, status, rec_val])
                    st.success("Tarefa inserida.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows  = fetch("SELECT id, titulo FROM tarefas ORDER BY id")
        opts  = _opts(rows, "id", "titulo")
        opts_p= _opts(processos, "id", "nome")
        opts_u= _opts(usuarios,  "id", "nome")
        sel   = st.selectbox("Selecionar tarefa", list(opts.keys()), key="sel_upd_tar")
        if sel:
            tid = opts[sel]
            rec = fetch("SELECT * FROM tarefas WHERE id=%s", [tid])[0]
            proc_labels  = ["—"] + list(opts_p.keys())
            usr_labels   = list(opts_u.keys())
            proc_key     = next((k for k,v in opts_p.items() if v == rec["processo_id"]), None)
            atrib_key    = next((k for k,v in opts_u.items() if v == rec["atribuido_para"]), usr_labels[0])
            criador_key  = next((k for k,v in opts_u.items() if v == rec["criado_por"]),     usr_labels[0])
            with st.form("upd_tarefa"):
                titulo     = st.text_input("Título",    value=rec["titulo"])
                descricao  = st.text_area("Descrição",  value=rec["descricao"] or "")
                proc_sel   = st.selectbox("Processo",   proc_labels, index=proc_labels.index(proc_key) if proc_key else 0)
                atrib_sel  = st.selectbox("Atribuído",  usr_labels,  index=usr_labels.index(atrib_key))
                criador_sel= st.selectbox("Criado por", usr_labels,  index=usr_labels.index(criador_key))
                vencimento = st.date_input("Vencimento", value=rec["data_vencimento"].date() if rec["data_vencimento"] else date.today())
                prioridade = st.selectbox("Prioridade", PRIORIDADES, index=PRIORIDADES.index(rec["prioridade"]) if rec["prioridade"] in PRIORIDADES else 1)
                status     = st.selectbox("Status", STATUS_TAREF, index=STATUS_TAREF.index(rec["status"]) if rec["status"] in STATUS_TAREF else 0)
                recorrencia= st.selectbox("Recorrência", ["—"] + RECORRENCIAS,
                              index=(["—"] + RECORRENCIAS).index(rec["recorrencia"]) if rec["recorrencia"] in RECORRENCIAS else 0)
                if st.form_submit_button("Atualizar"):
                    try:
                        proc_id = opts_p[proc_sel] if proc_sel != "—" else None
                        rec_val = recorrencia if recorrencia != "—" else None
                        if status == "concluida" and rec["status"] != "concluida":
                            concluida_em = datetime.now(timezone.utc)
                        elif status != "concluida":
                            concluida_em = None
                        else:
                            concluida_em = rec["concluida_em"]
                        execute("""
                            UPDATE tarefas SET titulo=%s, descricao=%s, processo_id=%s, atribuido_para=%s,
                            criado_por=%s, data_vencimento=%s, prioridade=%s, status=%s, recorrencia=%s, concluida_em=%s WHERE id=%s
                        """, [titulo, descricao or None, proc_id, opts_u[atrib_sel], opts_u[criador_sel],
                              datetime(vencimento.year, vencimento.month, vencimento.day, tzinfo=timezone.utc),
                              prioridade, status, rec_val, concluida_em, tid])
                        st.success("Tarefa atualizada.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT id, titulo FROM tarefas ORDER BY id")
        opts = _opts(rows, "id", "titulo")
        sel  = st.selectbox("Selecionar tarefa", list(opts.keys()), key="sel_del_tar")
        if sel and st.button("Excluir tarefa", type="primary"):
            try:
                execute("DELETE FROM tarefas WHERE id=%s", [opts[sel]])
                st.success("Tarefa excluída.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Atendimentos ───────────────────────────────────────────────────────

TIPOS_ATEND = ['presencial','telefone','email','videoconferencia','whatsapp','outro']

def page_atendimentos():
    st.header("Atendimentos")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    clientes  = fetch("SELECT id, nome FROM clientes  ORDER BY nome")
    processos = fetch("SELECT id, nome FROM processos ORDER BY nome")
    usuarios  = fetch("SELECT id, nome FROM usuarios  ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT a.id, c.nome AS cliente, p.nome AS processo, u.nome AS usuario,
                   a.tipo, a.data_hora, a.duracao_min, a.assunto, a.resultado
            FROM atendimentos a
            JOIN clientes c ON c.id=a.cliente_id
            LEFT JOIN processos p ON p.id=a.processo_id
            LEFT JOIN usuarios u ON u.id=a.usuario_id
            ORDER BY a.id
        """))

    with tabs[1]:
        opts_c = _opts(clientes,  "id", "nome")
        opts_p = _opts(processos, "id", "nome")
        opts_u = _opts(usuarios,  "id", "nome")
        with st.form("ins_atend"):
            cli_sel  = st.selectbox("Cliente",            list(opts_c.keys()))
            proc_sel = st.selectbox("Processo (opcional)",["—"] + list(opts_p.keys()))
            usr_sel  = st.selectbox("Usuário/Advogado",   list(opts_u.keys()))
            tipo      = st.selectbox("Tipo", TIPOS_ATEND)
            col_d, col_t = st.columns(2)
            with col_d:
                atend_data = st.date_input("Data", value=date.today())
            with col_t:
                atend_hora = st.time_input("Hora", value=datetime.now().time().replace(second=0, microsecond=0))
            duracao  = st.number_input("Duração (min)", min_value=1, step=1)
            assunto  = st.text_input("Assunto")
            descricao= st.text_area("Descrição")
            resultado= st.text_input("Resultado")
            if st.form_submit_button("Inserir"):
                try:
                    proc_id   = opts_p[proc_sel] if proc_sel != "—" else None
                    data_hora = datetime.combine(atend_data, atend_hora, tzinfo=timezone.utc)
                    execute("""
                        INSERT INTO atendimentos (cliente_id, processo_id, usuario_id, tipo, data_hora, duracao_min, assunto, descricao, resultado)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, [opts_c[cli_sel], proc_id, opts_u[usr_sel], tipo, data_hora, int(duracao), assunto, descricao or None, resultado or None])
                    st.success("Atendimento inserido.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows  = fetch("SELECT a.id, CONCAT(c.nome,' – ',a.assunto) AS label FROM atendimentos a JOIN clientes c ON c.id=a.cliente_id ORDER BY a.id")
        opts  = _opts(rows, "id", "label")
        opts_c= _opts(clientes,  "id", "nome")
        opts_p= _opts(processos, "id", "nome")
        opts_u= _opts(usuarios,  "id", "nome")
        sel   = st.selectbox("Selecionar atendimento", list(opts.keys()), key="sel_upd_atend")
        if sel:
            aid = opts[sel]
            rec = fetch("SELECT * FROM atendimentos WHERE id=%s", [aid])[0]
            cli_labels  = list(opts_c.keys())
            proc_labels = ["—"] + list(opts_p.keys())
            usr_labels  = list(opts_u.keys())
            cli_key  = next((k for k,v in opts_c.items() if v == rec["cliente_id"]),  cli_labels[0])
            proc_key = next((k for k,v in opts_p.items() if v == rec["processo_id"]), None)
            usr_key  = next((k for k,v in opts_u.items() if v == rec["usuario_id"]),  usr_labels[0])
            with st.form("upd_atend"):
                cli_sel  = st.selectbox("Cliente",   cli_labels,  index=cli_labels.index(cli_key))
                proc_sel = st.selectbox("Processo",  proc_labels, index=proc_labels.index(proc_key) if proc_key else 0)
                usr_sel  = st.selectbox("Usuário",   usr_labels,  index=usr_labels.index(usr_key))
                tipo     = st.selectbox("Tipo", TIPOS_ATEND, index=TIPOS_ATEND.index(rec["tipo"]) if rec["tipo"] in TIPOS_ATEND else 0)
                _dh_val  = rec["data_hora"]
                _dh_dt   = _dh_val.date() if _dh_val else date.today()
                _dh_tm   = _dh_val.time().replace(second=0, microsecond=0) if _dh_val else datetime.now().time().replace(second=0, microsecond=0)
                col_d, col_t = st.columns(2)
                with col_d:
                    atend_data = st.date_input("Data", value=_dh_dt)
                with col_t:
                    atend_hora = st.time_input("Hora", value=_dh_tm)
                duracao  = st.number_input("Duração (min)", value=int(rec["duracao_min"] or 0), min_value=1, step=1)
                assunto  = st.text_input("Assunto",   value=rec["assunto"])
                descricao= st.text_area("Descrição",  value=rec["descricao"] or "")
                resultado= st.text_input("Resultado", value=rec["resultado"] or "")
                if st.form_submit_button("Atualizar"):
                    try:
                        proc_id   = opts_p[proc_sel] if proc_sel != "—" else None
                        data_hora = datetime.combine(atend_data, atend_hora, tzinfo=timezone.utc)
                        execute("""
                            UPDATE atendimentos SET cliente_id=%s, processo_id=%s, usuario_id=%s, tipo=%s,
                            data_hora=%s, duracao_min=%s, assunto=%s, descricao=%s, resultado=%s WHERE id=%s
                        """, [opts_c[cli_sel], proc_id, opts_u[usr_sel], tipo, data_hora, int(duracao), assunto, descricao or None, resultado or None, aid])
                        st.success("Atendimento atualizado.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT a.id, CONCAT(c.nome,' – ',a.assunto) AS label FROM atendimentos a JOIN clientes c ON c.id=a.cliente_id ORDER BY a.id")
        opts = _opts(rows, "id", "label")
        sel  = st.selectbox("Selecionar atendimento", list(opts.keys()), key="sel_del_atend")
        if sel and st.button("Excluir atendimento", type="primary"):
            try:
                execute("DELETE FROM atendimentos WHERE id=%s", [opts[sel]])
                st.success("Atendimento excluído.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Conversas ──────────────────────────────────────────────────────────

def page_conversas():
    st.header("Conversas")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    processos = fetch("SELECT id, nome FROM processos ORDER BY nome")
    clientes  = fetch("SELECT id, nome FROM clientes  ORDER BY nome")
    usuarios  = fetch("SELECT id, nome FROM usuarios  ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT cv.id, cv.nome, p.nome AS processo, c.nome AS cliente,
                   u.nome AS criado_por, cv.criado_em
            FROM conversas cv
            LEFT JOIN processos p ON p.id=cv.processo_id
            LEFT JOIN clientes  c ON c.id=cv.cliente_id
            LEFT JOIN usuarios  u ON u.id=cv.criado_por
            ORDER BY cv.id
        """))

    with tabs[1]:
        opts_p = _opts(processos, "id", "nome")
        opts_c = _opts(clientes,  "id", "nome")
        opts_u = _opts(usuarios,  "id", "nome")
        with st.form("ins_conversa"):
            nome     = st.text_input("Nome da conversa")
            proc_sel = st.selectbox("Processo (opcional)", ["—"] + list(opts_p.keys()))
            cli_sel  = st.selectbox("Cliente (opcional)",  ["—"] + list(opts_c.keys()))
            usr_sel  = st.selectbox("Criado por", list(opts_u.keys()))
            if st.form_submit_button("Inserir"):
                try:
                    proc_id = opts_p[proc_sel] if proc_sel != "—" else None
                    cli_id  = opts_c[cli_sel]  if cli_sel  != "—" else None
                    execute("""
                        INSERT INTO conversas (nome, processo_id, cliente_id, criado_por)
                        VALUES (%s,%s,%s,%s)
                    """, [nome or None, proc_id, cli_id, opts_u[usr_sel]])
                    st.success("Conversa inserida.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows  = fetch("SELECT id, COALESCE(nome, CONCAT('Conversa #',id)) AS label FROM conversas ORDER BY id")
        opts  = _opts(rows, "id", "label")
        opts_p= _opts(processos, "id", "nome")
        opts_c= _opts(clientes,  "id", "nome")
        opts_u= _opts(usuarios,  "id", "nome")
        sel   = st.selectbox("Selecionar conversa", list(opts.keys()), key="sel_upd_conv")
        if sel:
            cvid = opts[sel]
            rec  = fetch("SELECT * FROM conversas WHERE id=%s", [cvid])[0]
            proc_labels = ["—"] + list(opts_p.keys())
            cli_labels  = ["—"] + list(opts_c.keys())
            usr_labels  = list(opts_u.keys())
            proc_key = next((k for k,v in opts_p.items() if v == rec["processo_id"]), None)
            cli_key  = next((k for k,v in opts_c.items() if v == rec["cliente_id"]),  None)
            usr_key  = next((k for k,v in opts_u.items() if v == rec["criado_por"]),  usr_labels[0])
            with st.form("upd_conversa"):
                nome    = st.text_input("Nome", value=rec["nome"] or "")
                proc_sel= st.selectbox("Processo", proc_labels, index=proc_labels.index(proc_key) if proc_key else 0)
                cli_sel = st.selectbox("Cliente",  cli_labels,  index=cli_labels.index(cli_key)   if cli_key  else 0)
                usr_sel = st.selectbox("Criado por",usr_labels, index=usr_labels.index(usr_key))
                if st.form_submit_button("Atualizar"):
                    try:
                        proc_id = opts_p[proc_sel] if proc_sel != "—" else None
                        cli_id  = opts_c[cli_sel]  if cli_sel  != "—" else None
                        execute("""
                            UPDATE conversas SET nome=%s, processo_id=%s, cliente_id=%s, criado_por=%s
                            WHERE id=%s
                        """, [nome or None, proc_id, cli_id, opts_u[usr_sel], cvid])
                        st.success("Conversa atualizada.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT id, COALESCE(nome, CONCAT('Conversa #',id)) AS label FROM conversas ORDER BY id")
        opts = _opts(rows, "id", "label")
        sel  = st.selectbox("Selecionar conversa", list(opts.keys()), key="sel_del_conv")
        if sel and st.button("Excluir conversa", type="primary"):
            try:
                execute("DELETE FROM conversas WHERE id=%s", [opts[sel]])
                st.success("Conversa excluída.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Conversa Participantes ─────────────────────────────────────────────

def page_conversa_participantes():
    st.header("Conversa Participantes")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    conversas = fetch("SELECT id, COALESCE(nome, CONCAT('Conversa #',id)) AS label FROM conversas ORDER BY id")
    usuarios  = fetch("SELECT id, nome FROM usuarios ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT cp.conversa_id, cv.nome AS conversa, u.nome AS usuario,
                   cp.ultima_leitura, cp.entrou_em
            FROM conversa_participantes cp
            JOIN conversas cv ON cv.id=cp.conversa_id
            JOIN usuarios  u  ON u.id=cp.usuario_id
            ORDER BY cp.conversa_id, cp.usuario_id
        """))

    with tabs[1]:
        opts_cv = _opts(conversas, "id", "label")
        opts_u  = _opts(usuarios,  "id", "nome")
        with st.form("ins_part"):
            cv_sel = st.selectbox("Conversa", list(opts_cv.keys()))
            u_sel  = st.selectbox("Usuário",  list(opts_u.keys()))
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO conversa_participantes (conversa_id, usuario_id)
                        VALUES (%s,%s) ON CONFLICT DO NOTHING
                    """, [opts_cv[cv_sel], opts_u[u_sel]])
                    st.success("Participante adicionado.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows = fetch("""
            SELECT cp.conversa_id, cp.usuario_id, cp.ultima_leitura,
                   CONCAT(cv.nome,' – ',u.nome) AS label
            FROM conversa_participantes cp
            JOIN conversas cv ON cv.id=cp.conversa_id
            JOIN usuarios  u  ON u.id=cp.usuario_id
            ORDER BY cp.conversa_id
        """)
        if rows:
            labels = {r["label"]: r for r in rows}
            sel = st.selectbox("Selecionar participante", list(labels.keys()), key="sel_upd_part")
            if sel:
                rec = labels[sel]
                _ul = rec["ultima_leitura"]
                with st.form("upd_part"):
                    col_d, col_t = st.columns(2)
                    with col_d:
                        leitura_data = st.date_input("Última leitura (data)", value=_ul.date() if _ul else date.today())
                    with col_t:
                        leitura_hora = st.time_input("Última leitura (hora)", value=_ul.time().replace(second=0, microsecond=0) if _ul else datetime.now().time().replace(second=0, microsecond=0))
                    if st.form_submit_button("Atualizar"):
                        try:
                            ultima_leitura = datetime.combine(leitura_data, leitura_hora, tzinfo=timezone.utc)
                            execute("""
                                UPDATE conversa_participantes SET ultima_leitura=%s
                                WHERE conversa_id=%s AND usuario_id=%s
                            """, [ultima_leitura, rec["conversa_id"], rec["usuario_id"]])
                            st.success("Participante atualizado.")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
        else:
            st.info("Nenhum participante cadastrado.")

    with tabs[3]:
        rows = fetch("""
            SELECT cp.conversa_id, cp.usuario_id,
                   CONCAT(cv.nome,' – ',u.nome) AS label
            FROM conversa_participantes cp
            JOIN conversas cv ON cv.id=cp.conversa_id
            JOIN usuarios  u  ON u.id=cp.usuario_id
            ORDER BY cp.conversa_id
        """)
        if rows:
            labels = {r["label"]: (r["conversa_id"], r["usuario_id"]) for r in rows}
            sel = st.selectbox("Selecionar participante", list(labels.keys()), key="sel_del_part")
            if sel and st.button("Remover participante", type="primary"):
                try:
                    cv_id, u_id = labels[sel]
                    execute("DELETE FROM conversa_participantes WHERE conversa_id=%s AND usuario_id=%s", [cv_id, u_id])
                    st.success("Participante removido.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("Nenhum participante cadastrado.")

# ── SEÇÃO: Mensagens ──────────────────────────────────────────────────────────

def page_mensagens():
    st.header("Mensagens")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    conversas = fetch("SELECT id, COALESCE(nome, CONCAT('Conversa #',id)) AS label FROM conversas ORDER BY id")
    usuarios  = fetch("SELECT id, nome FROM usuarios ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT m.id, cv.nome AS conversa, u.nome AS usuario, m.conteudo, m.criado_em
            FROM mensagens m
            JOIN conversas cv ON cv.id=m.conversa_id
            LEFT JOIN usuarios u ON u.id=m.usuario_id
            ORDER BY m.id
        """))

    with tabs[1]:
        opts_cv = _opts(conversas, "id", "label")
        opts_u  = _opts(usuarios,  "id", "nome")
        with st.form("ins_msg"):
            cv_sel  = st.selectbox("Conversa", list(opts_cv.keys()))
            u_sel   = st.selectbox("Usuário",  list(opts_u.keys()))
            conteudo= st.text_area("Mensagem")
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO mensagens (conversa_id, usuario_id, conteudo)
                        VALUES (%s,%s,%s)
                    """, [opts_cv[cv_sel], opts_u[u_sel], conteudo])
                    st.success("Mensagem inserida.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows  = fetch("SELECT m.id, SUBSTR(m.conteudo,1,50) AS label FROM mensagens m ORDER BY m.id")
        opts  = _opts(rows, "id", "label")
        opts_cv= _opts(conversas, "id", "label")
        opts_u = _opts(usuarios,  "id", "nome")
        sel    = st.selectbox("Selecionar mensagem", list(opts.keys()), key="sel_upd_msg")
        if sel:
            mid = opts[sel]
            rec = fetch("SELECT * FROM mensagens WHERE id=%s", [mid])[0]
            cv_labels = list(opts_cv.keys())
            u_labels  = list(opts_u.keys())
            cv_key = next((k for k,v in opts_cv.items() if v == rec["conversa_id"]), cv_labels[0])
            u_key  = next((k for k,v in opts_u.items()  if v == rec["usuario_id"]),  u_labels[0])
            with st.form("upd_msg"):
                cv_sel   = st.selectbox("Conversa", cv_labels, index=cv_labels.index(cv_key))
                u_sel    = st.selectbox("Usuário",  u_labels,  index=u_labels.index(u_key))
                conteudo = st.text_area("Mensagem", value=rec["conteudo"])
                if st.form_submit_button("Atualizar"):
                    try:
                        execute("""
                            UPDATE mensagens SET conversa_id=%s, usuario_id=%s, conteudo=%s WHERE id=%s
                        """, [opts_cv[cv_sel], opts_u[u_sel], conteudo, mid])
                        st.success("Mensagem atualizada.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT m.id, SUBSTR(m.conteudo,1,50) AS label FROM mensagens m ORDER BY m.id")
        opts = _opts(rows, "id", "label")
        sel  = st.selectbox("Selecionar mensagem", list(opts.keys()), key="sel_del_msg")
        if sel and st.button("Excluir mensagem", type="primary"):
            try:
                execute("DELETE FROM mensagens WHERE id=%s", [opts[sel]])
                st.success("Mensagem excluída.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Notificações ───────────────────────────────────────────────────────

TIPOS_NOTIF = ['tarefa', 'sistema', 'processo', 'financeiro', 'mensagem']

def page_notificacoes():
    st.header("Notificações")
    tabs = st.tabs(["Listar", "Inserir", "Atualizar", "Excluir"])
    usuarios = fetch("SELECT id, nome FROM usuarios ORDER BY nome")

    with tabs[0]:
        show_df(fetch("""
            SELECT n.id, u.nome AS usuario, n.tipo, n.titulo, n.corpo, n.lida, n.link, n.criado_em
            FROM notificacoes n JOIN usuarios u ON u.id=n.usuario_id ORDER BY n.id
        """))

    with tabs[1]:
        opts_u = _opts(usuarios, "id", "nome")
        with st.form("ins_notif"):
            u_sel  = st.selectbox("Usuário", list(opts_u.keys()))
            tipo   = st.selectbox("Tipo", TIPOS_NOTIF)
            titulo = st.text_input("Título")
            corpo  = st.text_area("Corpo")
            link   = st.text_input("Link (opcional)")
            lida   = st.checkbox("Lida")
            if st.form_submit_button("Inserir"):
                try:
                    execute("""
                        INSERT INTO notificacoes (usuario_id, tipo, titulo, corpo, lida, link)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, [opts_u[u_sel], tipo, titulo, corpo or None, lida, link or None])
                    st.success("Notificação inserida.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with tabs[2]:
        rows  = fetch("SELECT n.id, n.titulo FROM notificacoes n ORDER BY n.id")
        opts  = _opts(rows, "id", "titulo")
        opts_u= _opts(usuarios, "id", "nome")
        sel   = st.selectbox("Selecionar notificação", list(opts.keys()), key="sel_upd_notif")
        if sel:
            nid = opts[sel]
            rec = fetch("SELECT * FROM notificacoes WHERE id=%s", [nid])[0]
            u_labels = list(opts_u.keys())
            u_key    = next((k for k,v in opts_u.items() if v == rec["usuario_id"]), u_labels[0])
            with st.form("upd_notif"):
                u_sel  = st.selectbox("Usuário", u_labels, index=u_labels.index(u_key))
                tipo   = st.selectbox("Tipo", TIPOS_NOTIF, index=TIPOS_NOTIF.index(rec["tipo"]) if rec["tipo"] in TIPOS_NOTIF else 0)
                titulo = st.text_input("Título", value=rec["titulo"])
                corpo  = st.text_area("Corpo",   value=rec["corpo"] or "")
                link   = st.text_input("Link",   value=rec["link"] or "")
                lida   = st.checkbox("Lida",     value=rec["lida"])
                if st.form_submit_button("Atualizar"):
                    try:
                        execute("""
                            UPDATE notificacoes SET usuario_id=%s, tipo=%s, titulo=%s, corpo=%s, lida=%s, link=%s
                            WHERE id=%s
                        """, [opts_u[u_sel], tipo, titulo, corpo or None, lida, link or None, nid])
                        st.success("Notificação atualizada.")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    with tabs[3]:
        rows = fetch("SELECT id, titulo FROM notificacoes ORDER BY id")
        opts = _opts(rows, "id", "titulo")
        sel  = st.selectbox("Selecionar notificação", list(opts.keys()), key="sel_del_notif")
        if sel and st.button("Excluir notificação", type="primary"):
            try:
                execute("DELETE FROM notificacoes WHERE id=%s", [opts[sel]])
                st.success("Notificação excluída.")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(str(e))

# ── SEÇÃO: Relatórios ─────────────────────────────────────────────────────────

def page_relatorios():
    st.header("Relatórios Analíticos")

    st.subheader("1 — Receita por área jurídica")
    try:
        rows = fetch("""
            SELECT p.area,
                   COUNT(DISTINCT p.id)              AS total_processos,
                   COUNT(DISTINCT c.id)              AS total_clientes,
                   STRING_AGG(DISTINCT c.nome, ', ') AS clientes,
                   SUM(f.valor_total)                AS receita_total
            FROM financeiros f
            JOIN processos p ON p.id = f.processo_id
            JOIN clientes  c ON c.id = p.cliente_id
            GROUP BY p.area
            ORDER BY receita_total DESC
        """)
        df1 = pd.DataFrame(rows)
        st.dataframe(df1, use_container_width=True)
        if not df1.empty:
            fig1 = px.bar(df1, x="area", y="receita_total",
                          labels={"area": "Área", "receita_total": "Receita Total (R$)"},
                          title="Receita por Área Jurídica")
            st.plotly_chart(fig1, use_container_width=True)
    except Exception as e:
        st.error(str(e))

    st.subheader("2 — Tarefas por usuário e status")
    try:
        rows = fetch("""
            SELECT u.nome AS usuario, t.status,
                   COUNT(t.id)                       AS total_tarefas,
                   COUNT(DISTINCT p.id)              AS processos_envolvidos,
                   STRING_AGG(DISTINCT p.area, ', ') AS areas
            FROM tarefas t
            JOIN usuarios u ON u.id = t.atribuido_para
            LEFT JOIN processos p ON p.id = t.processo_id
            GROUP BY u.nome, t.status
            ORDER BY u.nome, t.status
        """)
        df2 = pd.DataFrame(rows)
        st.dataframe(df2, use_container_width=True)
        if not df2.empty:
            fig2 = px.bar(df2, x="usuario", y="total_tarefas", color="status",
                          barmode="group",
                          labels={"usuario": "Usuário", "total_tarefas": "Total de Tarefas"},
                          title="Tarefas por Usuário e Status")
            st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(str(e))

    st.subheader("3 — Atendimentos por tipo")
    try:
        rows = fetch("""
            SELECT a.tipo,
                   COUNT(*)                          AS total_atendimentos,
                   COUNT(DISTINCT c.id)              AS clientes_atendidos,
                   COUNT(DISTINCT u.id)              AS advogados_envolvidos,
                   STRING_AGG(DISTINCT u.nome, ', ') AS advogados,
                   ROUND(AVG(a.duracao_min), 1)      AS duracao_media_min
            FROM atendimentos a
            JOIN clientes c ON c.id = a.cliente_id
            JOIN usuarios u ON u.id = a.usuario_id
            GROUP BY a.tipo
            ORDER BY total_atendimentos DESC
        """)
        df3 = pd.DataFrame(rows)
        st.dataframe(df3, use_container_width=True)
        if not df3.empty:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=df3["tipo"], y=df3["total_atendimentos"],
                name="Total atendimentos", yaxis="y"
            ))
            fig3.add_trace(go.Scatter(
                x=df3["tipo"], y=df3["duracao_media_min"],
                name="Duração média (min)", yaxis="y2", mode="lines+markers"
            ))
            fig3.update_layout(
                title="Atendimentos por Tipo",
                yaxis=dict(title="Total atendimentos"),
                yaxis2=dict(title="Duração média (min)", overlaying="y", side="right"),
                legend=dict(x=0.01, y=0.99),
            )
            st.plotly_chart(fig3, use_container_width=True)
    except Exception as e:
        st.error(str(e))

# ── SEÇÃO: Assistente IA ──────────────────────────────────────────────────────

DB_SCHEMA = """
Tabelas do banco de dados controladoria (PostgreSQL):

usuarios(id, nome, email, senha_hash, tipo, ativo, acesso_financeiro, pode_excluir, foto_perfil_url, criado_em)
  tipo: 'admin','usuario'
clientes(id, nome, cpf, rg, email, telefone, endereco, criado_em)
processos(id, cliente_id, nome, numero_processo, vara, comarca, area, status, criado_em)
  area: 'Cível','Trabalhista','Família','Criminal','Tributário','Imobiliário','Sucessões','Bancário','Ambiental','Outro'
  status: 'ativo','arquivado','encerrado'
financeiros(id, processo_id, descricao, tipo, valor_total, num_parcelas, status, observacoes, criado_em)
  tipo: 'honorario','reembolso','outro'
  status: 'pendente','pago_parcial','pago','cancelado'
parcelas(id, financeiro_id, numero, valor, vencimento, status, pago_em)
  status: 'pendente','pago','cancelado'
documentos(id, processo_id, nome, tipo, url, mime_type, criado_por, criado_em)
  tipo: 'gerado','upload'
  criado_por referencia usuarios(id)
tarefas(id, titulo, descricao, processo_id, atribuido_para, criado_por, data_vencimento, prioridade, status, recorrencia, concluida_em, criado_em)
  prioridade: 'baixa','normal','alta','urgente'
  status: 'pendente','em_andamento','concluida','cancelada'
  recorrencia: 'diaria','semanal','mensal' (nullable)
atendimentos(id, cliente_id, processo_id, usuario_id, tipo, data_hora, duracao_min, assunto, descricao, resultado, criado_em)
  tipo: 'presencial','telefone','email','videoconferencia','whatsapp','outro'
conversas(id, nome, processo_id, cliente_id, criado_por, criado_em)
conversa_participantes(conversa_id, usuario_id, ultima_leitura, entrou_em)
mensagens(id, conversa_id, usuario_id, conteudo, criado_em)
notificacoes(id, usuario_id, tipo, titulo, corpo, lida, link, criado_em)
"""

def page_assistente_ia():
    st.header("Assistente IA (Text-to-SQL)")

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        st.warning("GROQ_API_KEY não configurada. Defina no arquivo .env para usar este módulo.")
        return

    from groq import Groq
    client = Groq(api_key=groq_key)

    pergunta = st.text_area("Digite sua pergunta em linguagem natural:", height=100,
                            placeholder="Ex.: Quais clientes têm processos trabalhistas ativos?")

    if st.button("Perguntar") and pergunta.strip():
        with st.spinner("Gerando SQL..."):
            try:
                resp_sql = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": (
                            "Você é um especialista em SQL PostgreSQL. "
                            "Dado o schema abaixo, gere APENAS o SQL SELECT que responde à pergunta do usuário. "
                            "Não inclua explicações, markdown, nem blocos de código — apenas o SQL puro.\n\n"
                            + DB_SCHEMA
                        )},
                        {"role": "user", "content": pergunta},
                    ],
                    temperature=0,
                )
                sql_gerado = resp_sql.choices[0].message.content.strip()

                # remove possíveis ```sql ... ``` se o modelo incluir
                if sql_gerado.startswith("```"):
                    sql_gerado = "\n".join(
                        line for line in sql_gerado.splitlines()
                        if not line.strip().startswith("```")
                    ).strip()

                _sql_norm = sql_gerado.upper().lstrip()
                if not (_sql_norm.startswith("SELECT") or _sql_norm.startswith("WITH")):
                    st.error("O modelo retornou um SQL que não é SELECT. Rejeitado por segurança.")
                    st.code(sql_gerado, language="sql")
                    return

                # executa em transação read-only
                conn = get_readonly_conn()
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(sql_gerado)
                            rows = cur.fetchall()
                finally:
                    conn.close()

                df_result = pd.DataFrame(rows)

                # segunda chamada: explicação em português
                with st.spinner("Explicando o resultado..."):
                    resp_exp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "Você explica resultados de consultas SQL em português claro e objetivo, em no máximo 3 frases."},
                            {"role": "user",   "content": (
                                f"Pergunta original: {pergunta}\n"
                                f"SQL executado: {sql_gerado}\n"
                                f"Resultado ({len(rows)} linhas): {df_result.head(5).to_string()}"
                            )},
                        ],
                        temperature=0.3,
                    )
                    explicacao = resp_exp.choices[0].message.content.strip()

                st.markdown(f"**Explicação:** {explicacao}")
                st.dataframe(df_result, use_container_width=True)
                with st.expander("Ver SQL gerado"):
                    st.code(sql_gerado, language="sql")

            except Exception as e:
                st.error(str(e))

# ── Navegação principal ───────────────────────────────────────────────────────

PAGES = {
    "Configuração do Banco":      page_config,
    "Usuários":                   page_usuarios,
    "Clientes":                   page_clientes,
    "Processos":                  page_processos,
    "Financeiros":                page_financeiros,
    "Parcelas":                   page_parcelas,
    "Documentos":                 page_documentos,
    "Tarefas":                    page_tarefas,
    "Atendimentos":               page_atendimentos,
    "Conversas":                  page_conversas,
    "Conversa Participantes":     page_conversa_participantes,
    "Mensagens":                  page_mensagens,
    "Notificações":               page_notificacoes,
    "Relatórios Analíticos":      page_relatorios,
    "Assistente IA":              page_assistente_ia,
}

st.set_page_config(page_title="Gestão Jurídica", layout="wide")
st.title("Gestão Jurídica")

pagina = st.sidebar.radio("Navegação", list(PAGES.keys()))
PAGES[pagina]()
