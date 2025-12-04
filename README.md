# MariIA - Inteligência Artificial para Varejo e Televendas

**MariIA** é um ecossistema de agentes inteligentes projetado para otimizar operações de varejo, conectando dados do ERP (SQL Server) com Inteligência Artificial Generativa (Google Vertex AI).

## 🏗️ Arquitetura do Projeto

O projeto segue uma arquitetura modular:

1.  **Camada de Dados (SQL Server)**:
    *   Views otimizadas (ex: `FAL_IA_Dados_Vendas_Televendas`) consolidam dados de Faturas, Pedidos, Cotações, Entregas e Devoluções.
    *   Foco em performance e nomes de colunas amigáveis para IA (PT-BR).

2.  **Camada de Conexão (Python)**:
    *   `src/database/connector.py`: Gerencia conexões seguras usando `SQLAlchemy` e `pyodbc`.
    *   Suporte a queries parametrizadas para segurança (Anti-SQL Injection).

3.  **Camada de Agentes (AI)**:
    *   **Telesales Agent** (`src/agents/telesales_agent.py`): Especialista em vendas B2B. Analisa histórico de clientes e gera "Pitches" de venda personalizados usando Gemini 3.0 Pro.
    *   **Inventory Agent** (`src/agents/inventory_agent.py`): (Em desenvolvimento) Para análise de estoque e reposição.

## 🚀 Como Executar

### Pré-requisitos
*   Python 3.10+
*   Acesso ao Google Cloud Project (Vertex AI habilitado)
*   Acesso ao Banco de Dados SQL Server

### Instalação
1.  Clone o repositório.
2.  Crie um ambiente virtual: `python -m venv .venv`
3.  Instale as dependências: `pip install -r requirements.txt`
4.  Configure o arquivo `.env` (use `.env.example` como base).

### Uso do Agente de Televendas

**Gerar Insights Gerais (Top Clientes):**
```bash
python src/agents/telesales_agent.py --insights
```

**Gerar Pitch para um Cliente Específico:**
```bash
python src/agents/telesales_agent.py --customer C00123
```

**Vender um Produto Específico:**
```bash
python src/agents/telesales_agent.py --customer C00123 --sku "FEIJAO-PRETO"
```

## 🛡️ Segurança
*   Credenciais de banco de dados são lidas estritamente de variáveis de ambiente (`.env`).
*   O arquivo `.env` é ignorado pelo Git (`.gitignore`).
*   Queries SQL utilizam parâmetros bindados.

## ☁️ Infraestrutura AI
*   **Modelo**: Gemini 1.5 Pro (Estável) ou Gemini 3.0 Pro (Preview).
*   **Endpoint**: Global (`aiplatform.googleapis.com`) para garantir acesso aos modelos mais recentes.
