# Histórico de Versões (Changelog)

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [1.0.0] - 2025-12-04
### Adicionado
- **Agente de Televendas (`TelesalesAgent`)**:
    - Integração com SQL Server via `FAL_IA_Dados_Vendas_Televendas`.
    - Geração de Pitches de Venda com Gemini (Vertex AI).
    - Modos de operação: `--insights` (Ranking) e `--customer` (Foco no Cliente).
- **Módulo de Conexão (`DatabaseConnector`)**:
    - Conexão robusta com `SQLAlchemy`.
    - Tratamento de caracteres especiais em senhas.
    - Suporte a queries parametrizadas.
- **Documentação**:
    - `README.md` com visão geral e instruções.
    - `.env.example` para configuração segura.

### Segurança
- **Remoção de Hardcoded Secrets**: Todas as credenciais movidas para variáveis de ambiente.
- **Correção de SQL Injection**: Implementação de `params={}` nas chamadas SQL.
- **Gitignore**: Configurado para ignorar `.env`, `__pycache__` e arquivos de sistema.

### Infraestrutura
- **SQL View**: Criação da view `FAL_IA_Dados_Vendas_Televendas` otimizada para performance (filtros SARGable) e nomenclatura PT-BR.
- **Vertex AI**: Configuração do Endpoint Global (`aiplatform.googleapis.com`) para acesso a modelos Preview.
- **Dependências**: Atualização do `requirements.txt` com `python-dotenv`, `tabulate`, `sqlalchemy`, `pyodbc`.

---
*Versão Inicial do Projeto MariIA.*
