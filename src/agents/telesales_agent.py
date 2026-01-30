import sys
import os
import json
import argparse
from typing import Dict, List, Optional, AsyncGenerator
import pandas as pd
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, Tool, FunctionDeclaration, Part, Content
import re
from cachetools import cached, TTLCache

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.database.connector import DatabaseConnector

# Configurações Vertex AI
from src.core.config import get_settings
settings = get_settings()

GLOBAL_ENDPOINT = "aiplatform.googleapis.com"

class TelesalesAgent:
    def __init__(self):
        print("DEBUG: Iniciando Vertex AI Agent com Tools...", flush=True)
        try:
            vertexai.init(project=settings.PROJECT_ID, location=settings.LOCATION, api_endpoint=GLOBAL_ENDPOINT)
            
            # --- Definição das Tools (Function Calling) ---
            
            get_customer_history_func = FunctionDeclaration(
                name="get_customer_history_markdown",
                description="Busca histórico de compras recente de um cliente. Use para entender o padrão de compra.",
                parameters={
                    "type": "object",
                    "properties": {
                        "card_code": {"type": "string", "description": "Código do Cliente (Ex: C00123)"},
                        "limit": {"type": "integer", "description": "Número máximo de pedidos para retornar (Padrão: 10)."}
                    },
                    "required": ["card_code"]
                },
            )

            get_customer_details_func = FunctionDeclaration(
                name="get_customer_details_json_string",
                description="Busca informações de cadastro do cliente (Nome, Endereço, Contato).",
                parameters={
                    "type": "object",
                    "properties": {
                        "card_code": {"type": "string", "description": "Código do Cliente (Ex: C00123)"}
                    },
                    "required": ["card_code"]
                },
            )

            get_sales_insights_func = FunctionDeclaration(
                name="get_sales_insights_markdown",
                description="Busca insights gerais de vendas e clientes ativos na carteira do vendedor.",
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Dias para análise (Padrão: 30)"}
                    }
                },
            )

            get_inactive_customers_func = FunctionDeclaration(
                name="get_inactive_customers_markdown",
                description="Busca clientes INATIVOS (risco de churn) na carteira.",
                parameters={
                    "type": "object",
                    "properties": {
                        "days_without_purchase": {"type": "integer", "description": "Dias sem comprar (Padrão: 30)"}
                    }
                },
            )

            get_top_products_func = FunctionDeclaration(
                name="get_top_products",
                description="Busca os produtos mais vendidos (Catálogo/Ranking).",
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Período de dias (Padrão: 90)"}
                    }
                },
            )
            
            get_company_kpis_func = FunctionDeclaration(
                name="get_company_kpis",
                description="Busca KPIs globais da empresa (Faturamento, Totais) para Diretores.",
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Período de dias (Padrão: 30)"}
                    }
                },
            )
            
            get_top_sellers_func = FunctionDeclaration(
                name="get_top_sellers",
                description="Busca ranking de melhores vendedores.",
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer", "description": "Período de dias (Padrão: 30)"}
                    }
                },
            )

            # Agrupa as tools
            telesales_tools = Tool(
                function_declarations=[
                    get_customer_history_func,
                    get_customer_details_func,
                    get_sales_insights_func,
                    get_inactive_customers_func,
                    get_top_products_func,
                    get_company_kpis_func,
                    get_top_sellers_func
                ]
            )

            self.model = GenerativeModel(
                model_name=settings.MODEL_ID,
                system_instruction="""
                Você é um Assistente Especialista em Televendas (B2B) da empresa Fantástico Alimentos.
                Sua missão é ajudar vendedores e diretores com dados e insights.
                
                FERRAMENTAS DISPONÍVEIS:
                Você tem acesso a ferramentas reais para buscar dados do banco de dados (SAP B1).
                USE AS FERRAMENTAS SEMPRE QUE PRECISAR DE DADOS REAIS. NÃO INVENTE DADOS.
                
                DIRETRIZES:
                1. Contexto: Você fala com vendedores na rua (mobile). Seja BREVE e PRÁTICO.
                2. Formatação: Use Markdown (negrito, listas) para facilitar a leitura.
                3. Proatividade: Se o usuário pedir "Clientes", pergunte se ele quer "Positivados" ou "Inativos".
                4. Clientes: Quando falar de um cliente, sempre cite o Código (CardCode).
                5. Erros: Se uma ferramenta falhar, avise o usuário e tente outra abordagem.
                
                Lembre-se: Você deve sempre filtrar os dados pela carteira do vendedor atual quando utilizar as ferramentas de busca.
                """,
                tools=[telesales_tools]
            )
            print("DEBUG: Vertex AI Model + Tools OK.", flush=True)

        except Exception as e:
            print(f"AVISO: Falha ao iniciar Vertex AI ({e}).", flush=True)
            self.model = None
            
        print("DEBUG: Iniciando DatabaseConnector...", flush=True)
        self.db = DatabaseConnector()
        print("DEBUG: Init concluído.", flush=True)

    # --- Métodos de Negócio (Implementação das Tools) ---

    def get_customer_history_markdown(self, card_code: str, limit: int = 10) -> str:
        """Busca histórico de pedidos (Versão Chat/Markdown)."""
        try:
            query = f"SELECT TOP {limit} Data_Emissao, Numero_Documento, SKU, Nome_Produto, Quantidade, Valor_Liquido, Nome_Cliente FROM FAL_IA_Dados_Vendas_Televendas WHERE Codigo_Cliente = :card_code ORDER BY Data_Emissao DESC"
            df = self.db.get_dataframe(query, params={"card_code": card_code})
            if df.empty: return "Nenhuma compra recente encontrada."
            return df.to_markdown(index=False)
        except Exception as e: return f"Erro ao buscar histórico: {str(e)}"

    def get_customer_history(self, card_code: str, limit: int = 20) -> pd.DataFrame:
        """Busca histórico de pedidos (Versão API/DataFrame)."""
        # Aumentei o limit default para API
        # Nota: Corrigido Valor_Unitario -> Preco_Unitario_Original
        query = f"""
        SELECT TOP {limit} 
            Data_Emissao, Numero_Documento, SKU, Nome_Produto, 
            Quantidade, Valor_Liquido, Nome_Cliente, Tipo_Documento, 
            Status_Documento, Valor_Total_Linha, 
            Preco_Unitario_Original as Valor_Unitario 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Codigo_Cliente = :card_code 
        ORDER BY Data_Emissao DESC
        """
        return self.db.get_dataframe(query, params={"card_code": card_code})

    def get_customer_details_json_string(self, card_code: str) -> str:
        """Busca detalhes do cliente (Versão Chat/JSON String)."""
        try:
            query = "SELECT TOP 1 CardCode, CardName, Telefone, Email, Endereco, AtivoDesde FROM VW_MariIA_ClientDetails WHERE CardCode = :card_code"
            df = self.db.get_dataframe(query, params={"card_code": card_code})
            if df.empty: return "Cliente não encontrado."
            return df.iloc[0].to_json()
        except Exception as e: return f"Erro ao buscar detalhes: {str(e)}"
        
    def get_customer_details(self, card_code: str) -> dict:
        """Busca detalhes do cliente (Versão API/Dict)."""
        try:
            query = "SELECT TOP 1 CardCode, CardName, Telefone, Email, Endereco, AtivoDesde FROM VW_MariIA_ClientDetails WHERE CardCode = :card_code"
            df = self.db.get_dataframe(query, params={"card_code": card_code})
            if df.empty: return {}
            return df.iloc[0].to_dict()
        except: return {}

    def get_sales_trend(self, card_code: str, months: int = 6) -> dict:
        """Busca tendência de vendas para o gráfico (Versão API)."""
        try:
            # SQL Server Query
            query = f"""
            SELECT 
                FORMAT(Data_Emissao, 'MM/yy') as Mes,
                CASE 
                    WHEN Categoria_Produto LIKE '%ARROZ%' THEN 'Arroz'
                    WHEN Categoria_Produto LIKE '%FEIJAO%' THEN 'Feijão'
                    WHEN Categoria_Produto LIKE '%MASSA%' THEN 'Massas'
                    ELSE 'Outros'
                END as Categoria,
                SUM(Valor_Liquido) as Total,
                MIN(Data_Emissao) as SortDate
            FROM FAL_IA_Dados_Vendas_Televendas 
            WHERE Codigo_Cliente = :card_code 
              AND Data_Emissao >= DATEADD(month, -{months}, GETDATE())
            GROUP BY FORMAT(Data_Emissao, 'MM/yy'),
                     CASE 
                        WHEN Categoria_Produto LIKE '%ARROZ%' THEN 'Arroz'
                        WHEN Categoria_Produto LIKE '%FEIJAO%' THEN 'Feijão'
                        WHEN Categoria_Produto LIKE '%MASSA%' THEN 'Massas'
                        ELSE 'Outros'
                     END
            ORDER BY SortDate ASC
            """
            df = self.db.get_dataframe(query, params={"card_code": card_code})
            
            if df.empty:
                return {"labels": [], "datasets": []}

            # Garantir ordenação correta e labels únicos
            ordered_months = df.sort_values('SortDate')['Mes'].unique().tolist()
            
            categories = ['Arroz', 'Feijão', 'Massas']
            colors = {
                'Arroz': '#1A2F5A',
                'Feijão': '#22C55E',
                'Massas': '#F97316'
            }
            
            datasets = []
            for cat in categories:
                cat_data = []
                for m in ordered_months:
                    val = df[(df['Mes'] == m) & (df['Categoria'] == cat)]['Total'].sum()
                    cat_data.append(float(val))
                
                datasets.append({
                    "name": cat,
                    "data": cat_data,
                    "color": colors.get(cat)
                })
                
            return {
                "labels": ordered_months,
                "datasets": datasets
            }
        except Exception as e:
            print(f"Erro em get_sales_trend: {str(e)}")
            return {"labels": [], "datasets": []}

    def get_sales_insights_markdown(self, days: int = 30, vendor_filter: str = None) -> str:
        """Busca vendas recentes carteira (Versão Chat/Markdown)."""
        query = f"""
        SELECT TOP 10 Nome_Cliente, Valor_Liquido, Data_Emissao 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Data_Emissao >= DATEADD(day, -{days}, GETDATE())
        """
        if vendor_filter:
            query += f" AND Vendedor_Atual = '{vendor_filter}'"
        
        query += " ORDER BY Valor_Liquido DESC"
        
        df = self.db.get_dataframe(query)
        if df.empty: return "Sem vendas no período para sua carteira."
        return df.to_markdown(index=False)

    def get_sales_insights(self, min_days: int = 0, max_days: int = 30, vendor_filter: str = None) -> pd.DataFrame:
        """Busca vendas agregadas por cliente (Versão Dashboard/DataFrame)."""
        # 1. Calcula a Média de Perfil (Fardos totais por Pedido) nos últimos 180 dias
        # Isso garante uma média estável e condizente com a "carga" do cliente
        vendor_clause = f" AND Vendedor_Atual = '{vendor_filter}'" if vendor_filter else ""
        
        query = f"""
        WITH Vendas_Ultimos_6_Meses AS (
            SELECT 
                Codigo_Cliente,
                Numero_Documento,
                SUM(Quantidade) as Total_Fardos_Pedido
            FROM FAL_IA_Dados_Vendas_Televendas
            WHERE Data_Emissao >= DATEADD(day, -180, GETDATE())
            {vendor_clause}
            GROUP BY Codigo_Cliente, Numero_Documento
        ),
        Media_Perfil AS (
            SELECT 
                Codigo_Cliente,
                ROUND(AVG(CAST(Total_Fardos_Pedido AS FLOAT)), 1) as Media_Perfil_Fardos
            FROM Vendas_Ultimos_6_Meses
            GROUP BY Codigo_Cliente
        )
        SELECT 
            V.Codigo_Cliente,
            MAX(V.Nome_Cliente) as Nome_Cliente,
            MAX(V.Cidade) as Cidade,
            MAX(V.Estado) as Estado,
            SUM(V.Valor_Liquido) as Total_Venda,
            ISNULL(MAX(MP.Media_Perfil_Fardos), 0) as Media_Fardos,
            MAX(V.Data_Emissao) as Ultima_Compra
        FROM FAL_IA_Dados_Vendas_Televendas V
        LEFT JOIN Media_Perfil MP ON V.Codigo_Cliente = MP.Codigo_Cliente
        WHERE V.Data_Emissao >= DATEADD(day, -{max_days}, GETDATE()) 
          AND V.Data_Emissao <= DATEADD(day, -{min_days}, GETDATE())
        """
        
        if vendor_filter:
             query += f" AND V.Vendedor_Atual = '{vendor_filter}'"
             
        query += " GROUP BY V.Codigo_Cliente ORDER BY Total_Venda DESC"
        
        return self.db.get_dataframe(query)

    def get_bales_breakdown(self, card_code: str, days: int = 180) -> pd.DataFrame:
        """Busca a média de fardos por SKU para um cliente específico."""
        query = f"""
        SELECT 
            SKU,
            MAX(Nome_Produto) as Produto,
            ROUND(AVG(Quantidade), 1) as Media_SKU,
            COUNT(Numero_Documento) as Vezes_Comprado
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Codigo_Cliente = :card_code 
          AND Data_Emissao >= DATEADD(day, -{days}, GETDATE())
        GROUP BY SKU
        ORDER BY Media_SKU DESC
        """
        return self.db.get_dataframe(query, params={"card_code": card_code})

    def get_inactive_customers_markdown(self, days_without_purchase: int = 30, vendor_filter: str = None) -> str:
        """Clientes inativos (Versão Chat/Markdown)."""
        vendor_clause = f" AND Vendedor_Atual = '{vendor_filter}'" if vendor_filter else ""
        query = f"""
        SELECT TOP 15 Codigo_Cliente, MAX(Nome_Cliente) as Nome, MAX(Data_Emissao) as Ultima_Compra 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE 1=1 {vendor_clause}
        GROUP BY Codigo_Cliente 
        HAVING MAX(Data_Emissao) < DATEADD(day, -{days_without_purchase}, GETDATE()) 
        ORDER BY Ultima_Compra DESC
        """
        df = self.db.get_dataframe(query)
        if df.empty: return "Nenhum cliente inativo relevante encontrado na sua carteira."
        return df.to_markdown(index=False)

    def get_inactive_customers(self, min_days: int = 30, max_days: int = 365, vendor_filter: str = None) -> pd.DataFrame:
        """Busca clientes inativos (sem compras no período) para o dashboard."""
        
        # Filtro de vendedor
        vendor_clause = f" AND Vendedor_Atual = '{vendor_filter}'" if vendor_filter else ""
        
        query = f"""
        WITH Base_Inativos AS (
            SELECT 
                Codigo_Cliente,
                MAX(Nome_Cliente) as Nome_Cliente,
                MAX(Cidade) as Cidade,
                MAX(Estado) as Estado,
                MAX(Data_Emissao) as Ultima_Compra
            FROM FAL_IA_Dados_Vendas_Televendas 
            WHERE 1=1 {vendor_clause}
            GROUP BY Codigo_Cliente
            HAVING MAX(Data_Emissao) < DATEADD(day, -{min_days}, GETDATE())
               AND MAX(Data_Emissao) >= DATEADD(day, -{max_days}, GETDATE())
        )
        SELECT 
            BI.Codigo_Cliente,
            BI.Nome_Cliente,
            BI.Cidade,
            BI.Estado,
            0 as Total_Venda, -- Inativo não tem venda no período filtrado
            ISNULL((
                SELECT ROUND(AVG(CAST(SumQ.Total_Fardos_Pedido AS FLOAT)), 1)
                FROM (
                    SELECT Numero_Documento, SUM(Quantidade) as Total_Fardos_Pedido
                    FROM FAL_IA_Dados_Vendas_Televendas S
                    WHERE S.Codigo_Cliente = BI.Codigo_Cliente
                      AND S.Data_Emissao >= DATEADD(month, -6, BI.Ultima_Compra)
                      AND S.Data_Emissao <= BI.Ultima_Compra
                    GROUP BY Numero_Documento
                ) SumQ
            ), 0) as Media_Fardos,
            BI.Ultima_Compra
        FROM Base_Inativos BI
        ORDER BY BI.Ultima_Compra DESC
        """
        
        return self.db.get_dataframe(query)

    def get_top_products(self, days: int = 90, vendor_filter: str = None) -> str:
        query = f"""
        SELECT TOP 20 SKU, MAX(Nome_Produto) as Produto, SUM(Valor_Liquido) as Total 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Data_Emissao >= DATEADD(day, -{days}, GETDATE())
        """
        if vendor_filter:
            query += f" AND Vendedor_Atual = '{vendor_filter}'"
            
        query += " GROUP BY SKU ORDER BY Total DESC"
        df = self.db.get_dataframe(query)
        return df.to_markdown(index=False)

    def get_company_kpis(self, days: int = 30) -> str:
        query = f"""
        SELECT 
            SUM(Valor_Liquido) as Faturamento, 
            COUNT(DISTINCT Numero_Documento) as Pedidos 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Data_Emissao >= DATEADD(day, -{days}, GETDATE())
        """
        df = self.db.get_dataframe(query)
        return df.iloc[0].to_json()

    def get_top_sellers(self, days: int = 30) -> str:
        query = f"""
        SELECT TOP 5 Vendedor_Atual, SUM(Valor_Liquido) as Total 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Data_Emissao >= DATEADD(day, -{days}, GETDATE()) 
        GROUP BY Vendedor_Atual ORDER BY Total DESC
        """
        df = self.db.get_dataframe(query)
        return df.to_markdown(index=False)
    
    # --- Chat Stream ---

    async def chat_stream(self, user_message: str, history: list = [], vendor_filter: str = None) -> AsyncGenerator[str, None]:
        """
        Gera resposta em stream, lidando automaticamente com chamadas de função.
        """
        if not self.model:
            yield "O modelo de IA não está disponível."
            return

        chat = self.model.start_chat() 
        # Nota: Vertex AI SDK gerencia o histórico na sessão 'chat', mas como recebemos history do frontend (stateless), 
        # idealmente deveríamos reconstruir o history do chat object. 
        # Para simplificar e performar, enviaremos o history como contexto na mensagem ou reconstruiremos.
        # Reconstruindo histórico básico:
        
        history_instruction = []
        if history:
            for msg in history[-6:]: # Limit history
                role = "user" if msg.get('sender') == 'user' else "model"
                part = Part.from_text(msg.get('text'))
                history_instruction.append(Content(role=role, parts=[part]))
        
        chat = self.model.start_chat(history=history_instruction)

        # Envia instrução de sistema dinâmica para o vendedor atual
        vendor_context = f"\n\nCONTEXTO DO USUÁRIO:\nVocê está conversando com: {vendor_filter or 'Vendedor'}.\nLembre-se: Use as ferramentas de busca e elas automaticamente filtrarão os dados para a sua carteira, se necessário."
        
        # Envia mensagem inicial
        response_stream = await chat.send_message_async(user_message + vendor_context, stream=True)
        
        # Itera sobre chunks. O SDK cuida da execução automática de tools? 
        # R: Não automaticamente no modo stream async simples sem orquestração. 
        # Precisamos detectar o FunctionCall, executar e devolver o FunctionResponse.
        
        # OBSERVAÇÃO CRÍTICA SOBRE VERTEX AI PYTHON SDK + STREAM + TOOLS:
        # A implementação padrão de `send_message_async(stream=True)` retorna chunks.
        # Se a IA decidir chamar uma func, o primeiro chunk conterá `function_call`.
        # Precisamos checar isso.
        
        # Para simplificar neste primeiro passo de otimização, devido à complexidade de loop manual de function calling com stream,
        # vamos usar uma abordagem híbrida ou a Feature "Automatic Function Calling" se disponível na versão da lib.
        # Assumindo loop manual padrão:
        
        collected_chunks = []
        function_call_detected = None
        
        async for chunk in response_stream:
            # Verifica tool call no primeiro chunk ou acumulado
            # (Lógica simplificada: Vertex AI geralmente manda o FunctionCall completo no primeiro response não-streamado ou streamado estruturado)
            # Mas com stream=True, pode vir picado.
            
            # WORKAROUND: Para Tool Calling robusto, é mais seguro não usar stream NA PRIMEIRA PERNA (decisão de tool).
            # Mas queremos streamar a resposta final.
            # Vamos testar se o chunk tem function_call.
            
            # Se tiver function calling, precisamos executar e mandar de volta.
            
            if chunk.candidates[0].function_calls:
                function_call_detected = chunk.candidates[0].function_calls[0]
                break # Sai do loop de stream de texto pois é uma tool call
            
            if chunk.text:
                yield chunk.text
                
        if function_call_detected:
            # Executa a tool
            func_name = function_call_detected.name
            func_args = function_call_detected.args
            
            print(f"DEBUG: Tool Call Detectada: {func_name} Args: {func_args}")
            
            tool_result = "Erro na execução da ferramenta."
            
            # Mapeamento dinâmico
            if hasattr(self, func_name):
                method = getattr(self, func_name)
                # Converte args (proto map) para dict python
                kwargs = {k: v for k, v in func_args.items()}
                
                # Injeta vendor_filter se o método aceitar
                import inspect
                sig = inspect.signature(method)
                if 'vendor_filter' in sig.parameters:
                    kwargs['vendor_filter'] = vendor_filter
                    
                try:
                    tool_result = method(**kwargs)
                except Exception as e:
                    tool_result = f"Erro ao executar {func_name}: {e}"
            
            print(f"DEBUG: Tool Result size: {len(str(tool_result))}")
            
            # Envia resposta da tool de volta para o modelo gerar a resposta final (agora sim com stream de texto)
            
            part_func_response = Part.from_function_response(
                name=func_name,
                response={"content": tool_result}
            )
            
            # Continua a conversa com o resultado da função
            final_response_stream = await chat.send_message_async(
                [part_func_response],
                stream=True
            )
            
            async for chunk in final_response_stream:
                 if chunk.text:
                    yield chunk.text
    
    # Manter método legado para evitar quebrar endpoints antigos por enquanto (se necessário) ou redirecionar
    async def chat(self, user_message: str, history: list = [], vendor_filter: str = None) -> str:
        """Versão não-stream (legado/compatibilidade)."""
        full_response = ""
        async for chunk in self.chat_stream(user_message, history, vendor_filter):
            full_response += chunk
        return full_response

    # Legacy Stubs - Manter para não quebrar API.py que chama métodos diretamente (ex: /insights)
    # Mas agora eles são chamados internamente pelas tools.
    # O ideal é refatorar o api.py para usar métodos de business, mas a estrutura da classe unificou isso.
    # Os métodos business estão definidos acima (get_customer_history, etc).
    
    # generate_pitch precisa ser mantido pois é um fluxo específico
    async def generate_pitch(self, card_code: str, target_sku: str = "", vendor_filter: str = None) -> dict:
        """Gera um pitch de vendas estruturado (Versão API)."""
        # 1. Recupera dados de contexto
        details = self.get_customer_details(card_code)
        hist = self.get_customer_history(card_code, limit=20)
        top_selling = self.get_top_products(days=90) # Top produtos gerais como sugestão
        
        customer_name = details.get('CardName', card_code)
        
        # 2. Constrói o Prompt Robusto
        prompt = f"""
        Você é a MARI IA, a assistente de inteligência de vendas da Fantástico Alimentos.
        Seu objetivo é gerar um PITCH DE VENDAS e um PEDIDO IDEAL para o vendedor abordar o cliente {customer_name} ({card_code}).

        DADOS DO CLIENTE:
        - Nome: {customer_name}
        - Ativo Desde: {details.get('AtivoDesde', 'N/A')}
        
        HISTÓRICO RECENTE DE COMPRAS:
        {hist.to_markdown(index=False) if not hist.empty else "Nenhuma compra recente encontrada."}

        PRODUTOS MAIS VENDIDOS DA EMPRESA (PARA OPORTUNIDADES):
        {top_selling}

        TAREFAS E REGRAS DE NEGÓCIO:
        1. **Perfil de Compra**: Resuma o que o cliente compra (ex: Foco em Arroz, itens de cesta básica).
        2. **Frequência**: Avalie a recorrência e dias desde o último pedido faturado.
        3. **Pitch de Venda**: Crie uma abordagem curta (2-3 frases), matadora e persuasiva.
        4. **Pedido Ideal**: Sugira 2 a 4 SKUs. Inclua ITENS RECORRENTES (que ele sempre compra) e 1 OPORTUNIDADE (um item do Top Selling que ele NÃO comprou recentemente).
        5. **Transparência (REGRAS ESTRITAS)**: Você DEVE retornar exatamente 3 motivos na lista `reasons`, com os seguintes títulos e ícones:
           - Título: "Timing Ideal" | Ícone: "history" | Conteúdo: Análise de dias desde a última compra e risco de ruptura.
           - Título: "Giro Garantido" | Ícone: "star" | Conteúdo: SKU recorrente do cliente que não pode faltar.
           - Título: "Oportunidade" | Ícone: "trending_up" | Conteúdo: Por que ele deve comprar o item novo sugerido (ex: é o mais vendido da cia).
        6. **Motivação**: Uma frase curta no campo `motivation` que resuma a estratégia (ex: "Reposição de estoque + Oportunidade de Mix").

        REGRAS DO JSON:
        - "suggested_order": [ {{"product_name": "...", "sku": "...", "quantity": 10, "unit_price": 25.50}} ]
        - "reasons": [ {{"title": "Timing Ideal", "text": "...", "icon": "history"}}, ... ]
        - "motivation": "Frase de impacto"

        RESPONDA EXATAMENTE NESTE FORMATO JSON:
        {{
            "pitch_text": "...",
            "profile_summary": "...",
            "frequency_assessment": "...",
            "suggested_order": [...],
            "motivation": "...",
            "reasons": [
                {{"title": "Timing Ideal", "text": "...", "icon": "history"}},
                {{"title": "Giro Garantido", "text": "...", "icon": "star"}},
                {{"title": "Oportunidade", "text": "...", "icon": "trending_up"}}
            ]
        }}
        """
        
        try:
            response = await self.model.generate_content_async(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            
            # Validação básica de campos obrigatórios
            for field in ["suggested_order", "reasons"]:
                if field not in data or not isinstance(data[field], list):
                    data[field] = []
            
            return data
        except Exception as e:
            print(f"Erro em generate_pitch: {e}")
            return {
                "pitch_text": "Olá! Notei que faz um tempo que não repomos o estoque de Arroz e Feijão Fantástico. Que tal aproveitar o pedido hoje?",
                "profile_summary": "Cliente recorrente de produtos básicos.",
                "frequency_assessment": "Frequência regular observada.",
                "suggested_order": [],
                "reasons": []
            }

if __name__ == "__main__":
    # Teste rápido
    import asyncio
    async def main():
        agent = TelesalesAgent()
        print("\n--- Teste Chat Stream ---")
        async for chunk in agent.chat_stream("Quem são meus melhores clientes?"):
            print(chunk, end="", flush=True)
        print("\n")
        
    asyncio.run(main())
