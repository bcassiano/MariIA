# Roadmap de Evolução - MariIA 2026

Este documento define os próximos passos para a evolução da plataforma MariIA, visando integração com o Portal Fantástico e melhorias operacionais.

## 1. Autenticação Real & Integração Portal Fantástico
**Objetivo:** Eliminar o vendedor "hardcoded" e permitir que o acesso aos dados seja dinâmico com base no usuário logado.
**Contexto:**
*   A aplicação MariIA fará parte do "Portal Fantástico".
*   O login deve respeitar as permissões e a carteira de clientes do usuário conforme cadastro no SAP.
*   Necessário implementar mecanismo para identificar o usuário na API (ex: JWT, Header de Usuário) e filtrar as queries do banco de dados (Views) por este usuário.

## 2. Notificações Push (Risco de Churn)
**Objetivo:** Alertar proativamente o vendedor quando um cliente importante entrar na zona de risco (30+ dias sem compra).
**Contexto:**
*   Monitorar a base de clientes.
*   Disparar notificação para o App Mobile.
*   Prioridade: Implementar logo após a autenticação.

## 3. Feedback Loop (Melhoria Contínua)
**Objetivo:** Refinar os prompts da IA com base no resultado real das interações.
**Contexto:**
*   Coletar dados mais ricos sobre o sucesso dos pitches.
*   Utilizar esses dados para re-treinar ou ajustar os prompts do Gemini.
*   Prioridade: Iniciar após a conclusão das notificações.
