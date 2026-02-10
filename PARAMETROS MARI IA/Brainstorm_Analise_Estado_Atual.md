# 🧠 Brainstorm: Análise do Estado Atual (MariIA)

### Contexto
O projeto **MariIA** está em estágio avançado de desenvolvimento, com uma arquitetura híbrida (FastAPI + React Native) funcional. O foco é empoderar vendedores externos e televendas com insights de dados (SQL Server) e inteligência artificial generativa (Vertex AI/Gemini).

---

### Opção A: Funcionalidades Prontas (O Que Já Temos)
O sistema já entrega valor real nas seguintes áreas:

✅ **Backend de Inteligência (TelesalesAgent)**
- **Consultas em Linguagem Natural**: O agente converte perguntas em SQL seguro (`run_sales_analysis_query`).
- **Segurança de Dados**: Implementação robusta de RLS (Row Level Security) via filtro de vendedor (`Vendedor_Atual`).
- **Ferramentas Especializadas**:
  - `get_sales_insights`: Dashboard de vendas.
  - `get_inactive_customers`: Detecção de risco de churn.
  - `get_portfolio_analysis`: Taxa de positivação da carteira.
  - `get_bales_breakdown`: Análise detalhada de média de fardos por SKU.

✅ **Aplicação Móvel (React Native/Expo)**
- **Dashboard Interativo**: Alternância rápida entre clientes "Positivados" e "Em Recuperação".
- **Chat Integrado**: Interface de chat funcional para conversar com a MariIA.
- **Detalhamento de Cliente**: Visualização de KPIs específicos e histórico.
- **Minha Carteira**: Tela dedicada para análise macro da carteira de clientes.

📊 **Maturidade:** Alta (Core Features funcionais).

---

### Opção B: Qualidade Técnica & Arquitetura
A base técnica é sólida, mas com pontos de atenção para escalabilidade.

✅ **Pontos Fortes:**
- **Stack Moderna**: Python 3.10+, FastAPI, Vertex AI, React Native com Tailwind.
- **Documentação**: `technical_overview.md` e `README.md` estão atualizados.
- **Segurança**: Prevenção de SQL Injection e validação de comandos proibidos no agente.

❌ **Pontos de Atenção (Débito Técnico):**
- **Lógica de "Média FD"**: O cálculo de média de fardos parece ser pesado e foi otimizado/desabilitado em alguns pontos (`telesales_agent.py:615`).
- **Tratamento de Filtros SQL**: A injeção do filtro de vendedor no `run_sales_analysis_query` usa regex/replace simples (`telesales_agent.py:440`), o que pode falhar em queries muito complexas.

📊 **Esforço de Manutenção:** Médio.

---

### Opção C: Roadmap Sugerido (Próximos Passos)
Com base no que temos, os caminhos naturais de evolução são:

1.  **Otimização de Performance**:
    -   Cachear queries pesadas (Média FD) no Redis ou tabela de resumo.
    -   Refinar a query de `Sales Trend` para evitar cálculos repetitivos.

2.  **Expansão do Agente**:
    -   Adicionar tools para **Estoque** (já existe um esboço em `inventory_agent.py`).
    -   Permitir ações transacionais (ex: criar rascunho de pedido).

3.  **Refinamento de UI/UX**:
    -   Melhorar feedback visual durante o carregamento de "insights profundos".
    -   Implementar modo offline para consulta de dados cacheados.

---

## 💡 Conclusão

O projeto **MariIA** é um case robusto de **GenAI aplicada a Dados Corporativos**.
O core (Chat com SQL + Dashboard) está pronto e funcional.
O foco agora deve ser **Estabilidade** (garantir que queries complexas da IA não quebrem o banco) e **Refinamento de UX**.

**Status Geral**: 🟢 Funcional / Estável.
