# 🧹 Relatório de Auditoria: Clean Code

> Este relatório analisa a conformidade do projeto **MariIA** com os princípios de *Clean Code* (Código Limpo), focado em manutenibilidade, legibilidade e robustez.

---

## 📊 Resumo Executivo

| Componente | Nota (0-10) | Status | Principais Problemas |
|------------|:-----------:|--------|----------------------|
| **Backend** (`telesales_agent.py`) | **4/10** | 🔴 Crítico | *God Class*, SRP violado, SQL hardcoded, Métodos longos. |
| **API** (`app.py`) | **6/10** | 🟡 Atenção | Tratamento de erro repetitivo, Lógica misturada na View. |
| **Mobile** (`HomeScreen.jsx`) | **7/10** | 🟡 Atenção | Componente grande, Lógica de negócio na UI. |

---

## 🔍 Análise Detalhada (Backend)

### 1. Violação de Responsabilidade Única (SRP) - 🔴 CRÍTICO
O arquivo `telesales_agent.py` define a classe `TelesalesAgent`, que assume responsabilidades demais:
-   Gerencia conexão com Vertex AI.
-   Define Tools/Schemas da IA.
-   Executa Queries SQL (Business Logic).
-   Gerencia Loop de Chat.
-   Formata Strings (Markdown/JSON).

**Impacto**: Difícil de testar e manter. Se mudar a lib de IA, quebra a lógica de vendas. Se mudar o banco, quebra a IA.
**Solução**: Separar em `TelesalesService` (Dados/SQL) e `TelesalesBot` (Interação IA).

### 2. "God Methods" (Métodos Gigantes) - 🔴 CRÍTICO
O método `chat_stream` tem quase **200 linhas**. Ele mistura:
-   Inicialização de chat.
-   Parsing manual de chunks da Vertex AI.
-   Detecção manual de *Function Calling*.
-   Execução de tools via `getattr`.
-   Tratamento de fallback/erros.

**Impacto**: Código frágil. Difícil de entender o fluxo de execução.
**Solução**: Extrair métodos privados: `_process_stream_chunk`, `_execute_tool`, `_format_fallback`.

### 3. SQL Hardcoded e Insegurança - 🟡 ALERTA
As queries SQL estão espalhadas dentro dos métodos python.
Além disso, a injeção do filtro de vendedor em `run_sales_analysis_query` usa manipulação de string (`replace`/`regex`) para inserir cláusulas `WHERE` em queries arbitrárias da IA. Isso é **frágil** e potencialmente inseguro (SQL Injection complexo pode passar).

**Solução**: Mover queries para um padrão *Repository* (`src/database/queries.py` ou `repositories/`). Para queries dinâmicas da IA, usar um *Parser SQL* real ou restringir a views seguras.

---

## 🔍 Análise Detalhada (API)

### 1. Repetição de Código (DRY)
Todo endpoint em `app.py` repete o bloco:
```python
try:
    ...
except Exception as e:
    import traceback
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=str(e))
```
**Solução**: Implementar um `exception_handler` global no FastAPI.

---

## 🔍 Análise Detalhada (Mobile)

### 1. Lógica na View
O componente `HomeScreen.jsx` contém a função `loadData` com lógica complexa de filtragem de datas e decisão de qual endpoint chamar (`getInsights` vs `getInactiveCustomers`).

**Solução**: Criar um *Custom Hook* `useDashboardData(filter, mode)` para isolar essa lógica.

---

## ✅ Plano de Ação Recomendado (Refatoração)

Para elevar a qualidade do código para "Production Grade", sugerimos as seguintes refatorações (em ordem de prioridade):

1.  **Backend - Extrair Camada de Serviço**:
    -   Mover métodos `get_customer_history`, `get_sales_insights`, etc. para `src/services/sales_service.py`.
    -   Deixar `TelesalesAgent` apenas como orquestrador da IA, chamando o Service.

2.  **Backend - Limpar `chat_stream`**:
    -   Criar uma classe manipuladora para o Stream da Vertex AI, isolando a complexidade do SDK.

3.  **API - Middleware de Erro**:
    -   Remover os `try/except` repetitivos e usar `@app.exception_handler`.

4.  **Mobile - Hooks**:
    -   Extrair lógica de `HomeScreen` para `hooks/useDashboard.js`.

---

**Você gostaria de prosseguir com alguma dessas refatorações agora?**
Recomendo começar pela **Extração da Camada de Serviço (Item 1)**, pois resolve o maior débito técnico (SRP).
