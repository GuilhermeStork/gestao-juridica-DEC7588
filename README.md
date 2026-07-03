# Gestão Jurídica — Banco de Dados (UFSC)

Aplicação web para gestão de escritório de advocacia, desenvolvida com Streamlit e PostgreSQL como trabalho final da disciplina de Banco de Dados (UFSC).

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução
- Python 3.9+

## Configuração inicial

**1. Clone o repositório**

```bash
git clone https://github.com/GuilhermeStork/gestao-juridica-DEC7588
cd gestao-juridica-DEC7588
```

**2. Crie o arquivo de variáveis de ambiente**

```bash
cp .env.example .env
```

Abra o `.env` e preencha o `GROQ_API_KEY` com sua chave da [Groq](https://console.groq.com). Os demais valores podem ser mantidos como estão.

**3. Crie e ative o ambiente virtual Python**

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows
```

**4. Instale as dependências**

```bash
pip install -r requirements.txt
```

## Rodando a aplicação

**1. Suba o banco de dados**

```bash
docker compose up -d
```

**2. Inicie a aplicação**

```bash
streamlit run app.py
```

**3. Acesse no navegador**

```
http://localhost:8501
```

**4. Configure o banco (primeiro uso)**

Na barra lateral, acesse **Configuração do Banco** e execute:
1. **Criar tabelas** — cria toda a estrutura do banco
2. **Popular dados de exemplo** — insere dados iniciais para teste

## Desligando a aplicação

Encerre o Streamlit com `Ctrl+C` no terminal e pare o container do banco:

```bash
docker compose down
```

Para remover também os dados armazenados (volume do PostgreSQL):

```bash
docker compose down -v
```
