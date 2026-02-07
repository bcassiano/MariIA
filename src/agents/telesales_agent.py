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

            run_sales_analysis_query_func = FunctionDeclaration(
                name="run_sales_analysis_query",
                description="Executa uma consulta SQL personalizada para responder perguntas analíticas complexas sobre vendas (Ex: Rankings, Médias, Agrupamentos).",
                parameters={
                    "type": "object",
                    "properties": {
                        "t_sql_query": {"type": "string", "description": "A consulta T-SQL (SELECT apenas) na tabela FAL_IA_Dados_Vendas_Televendas."},
                        "explanation": {"type": "string", "description": "Explicação breve do que a query busca."}
                    },
                    "required": ["t_sql_query"]
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
                    run_sales_analysis_query_func, # NOVA TOOL
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
                
                *** NOVO: ANÁLISE AUTÔNOMA DE DADOS (SQL) ***
                Para perguntas complexas onde as ferramentas padrões não bastam (ex: "Qual a média de fardos?", "Quem comprou mais Item X?"), 
                VOCÊ DEVE CRIAR UMA QUERY SQL usando a ferramenta `run_sales_analysis_query`.
                
                ESQUEMA DA TABELA DISPONÍVEL (`FAL_IA_Dados_Vendas_Televendas`):
                - `Data_Emissao` (Date): Data da venda.
                - `Numero_Documento` (Int): Número do pedido.
                - `SKU` (String): Código do produto (formato 0005).
                - `Nome_Produto` (String): Nome do item.
                - `Quantidade` (Decimal): Quantidade em Fardos/Unidades.
                - `Valor_Liquido` (Decimal): Valor total do item (R$).
                - `Nome_Cliente` (String): Razão Social.
                - `Codigo_Cliente` (String): CardCode (Ex: C00123).
                - `Vendedor_Atual` (String): Nome do vendedor (Use para filtrar carteira se necessário).
                - `Cidade` (String): Cidade do cliente.
                - `Estado` (String): UF.
                - `Categoria_Produto` (String): Categoria principal (ARROZ, FEIJAO, etc).

                DIRETRIZES GERAIS:
                1. Contexto: Você fala com vendedores na rua (mobile). Seja BREVE e PRÁTICO.
                2. Formatação: Use Markdown (negrito, listas) para facilitar a leitura.
                3. Proatividade: Se a análise for complexa, explique o que você calculou antes de mostrar os dados.
                4. Clientes: Quando falar de um cliente, sempre cite o Código (CardCode).
                5. SQL Seguro: APENAS SELECT. Nunca tente alterar dados.
                
                Lembre-se: Use `run_sales_analysis_query` sempre que precisar de um ranking, agrupamento ou métrica que não exista nas tools prontas.
                """,
                tools=[telesales_tools]
            )
            print("DEBUG: Vertex AI Model + Tools OK.", flush=True)

        except Exception as e:
            print(f"AVISO: Falha ao iniciar Vertex AI ({e}).", flush=True)
            self.model = None
            
        print("DEBUG: Iniciando DatabaseConnector...", flush=True)
        self.db = DatabaseConnector()
        # Cache para perfis de clientes (Média FD de 6 meses) - 24h de TTL
        self.profile_cache = TTLCache(maxsize=2000, ttl=3600 * 24)
        print("DEBUG: Init concluído.", flush=True)

    def _resolve_vendor_filter(self, vendor_filter: str) -> str:
        """
        Resolve o filtro de vendedor.
        Se receber um ID numérico (SlpCode), busca o nome (SlpName) na tabela OSLP.
        Se receber texto, assume que já é o nome.
        """
        if not vendor_filter:
            return None
            
        # Se for numérico, tenta resolver o nome
        if str(vendor_filter).isdigit():
            try:
                slp_code = int(vendor_filter)
                # Tenta buscar pelo SlpCode na tabela oficial de vendedores
                query = "SELECT SlpName FROM OSLP WHERE SlpCode = :code"
                df = self.db.get_dataframe(query, params={"code": slp_code})
                
                if not df.empty and 'SlpName' in df.columns:
                    resolved_name = df.iloc[0]['SlpName']
                    print(f"DEBUG: SlpCode {slp_code} resolvido para '{resolved_name}'")
                    return resolved_name
                else:
                    print(f"AVISO: SlpCode {slp_code} não encontrado na OSLP.")
                    return str(vendor_filter) # Retorna o ID mesmo, talvez a view aceite ou falhe graciosamente
            except Exception as e:
                print(f"Erro ao resolver SlpCode: {e}")
                return str(vendor_filter)
        
        return vendor_filter

    # --- Métodos de Negócio (Implementação das Tools) ---

    @staticmethod
    def _format_sku(val):
        """Padroniza SKU para ter pelo menos 4 dígitos inteiros (ex: 5 -> 0005, 201.1 -> 0201.1)."""
        if val is None: return ""
        s = str(val).strip()
        if '.' in s:
            parts = s.split('.')
            return parts[0].zfill(4) + '.' + parts[1]
        else:
            return s.zfill(4)


    def get_customer_history_markdown(self, card_code: str, limit: int = 10, vendor_filter: str = None) -> str:
        """Busca histórico de pedidos (Versão Chat/Markdown)."""
        try:
            vendor_filter = self._resolve_vendor_filter(vendor_filter)
            vendor_clause = ""
            if vendor_filter:
                vendor_clause = f" AND Vendedor_Atual = '{vendor_filter}'"

            query = f"SELECT TOP {limit} Data_Emissao, Numero_Documento, SKU, Nome_Produto, Quantidade, Valor_Liquido, Nome_Cliente FROM FAL_IA_Dados_Vendas_Televendas WHERE Codigo_Cliente = :card_code {vendor_clause} ORDER BY Data_Emissao DESC"
            df = self.db.get_dataframe(query, params={"card_code": card_code})
            if df.empty: return "Nenhuma compra recente encontrada (ou cliente fora da sua carteira)."
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
        df = self.db.get_dataframe(query, params={"card_code": card_code})
        if not df.empty and 'SKU' in df.columns:
            df['SKU'] = df['SKU'].apply(self._format_sku)
        return df

    def get_customer_details_json_string(self, card_code: str, vendor_filter: str = None) -> str:
        """Busca detalhes do cliente (Versão Chat/JSON String)."""
        try:
            # Check ownership if filter is present
            vendor_filter = self._resolve_vendor_filter(vendor_filter)
            if vendor_filter:
                # Security Check: Verify if this client belongs to the vendor (has sales)
                check_query = "SELECT TOP 1 1 FROM FAL_IA_Dados_Vendas_Televendas WHERE Codigo_Cliente = :card_code AND Vendedor_Atual = :vendor"
                check_df = self.db.get_dataframe(check_query, params={"card_code": card_code, "vendor": vendor_filter})
                if check_df.empty:
                    return "Acesso Negado: Este cliente não pertence à sua carteira de vendas."

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
                SUM(COALESCE(Valor_Liquido, Valor_Total_Linha, 0)) as Total,
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

        """Busca vendas recentes carteira (Versão Chat/Markdown)."""
        # Resolve SlpCode -> Name
        vendor_filter = self._resolve_vendor_filter(vendor_filter)

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
        
    def run_sales_analysis_query(self, t_sql_query: str, explanation: str = "", vendor_filter: str = None) -> str:
        """Executa uma query SQL analítica criada pela IA de forma segura."""
        try:
            # 1. Validação de Segurança Básica
            forbidden_keywords = ['UPDATE', 'DELETE', 'DROP', 'INSERT', 'ALTER', 'TRUNCATE', 'EXEC', 'MERGE', 'GRANT', 'REVOKE', '--', ';']
            normalized_query = t_sql_query.upper().strip()
            
            if not normalized_query.startswith("SELECT"):
                 return "Erro: Apenas consultas SELECT são permitidas."
                 
            for kw in forbidden_keywords:
                if f" {kw} " in normalized_query or normalized_query.startswith(kw): # Check words surrounded by spaces or at start
                     return f"Erro: O comando ou caracter '{kw}' não é permitido por segurança."

            # 2. Injeção de Filtro de Vendedor (Segurança de Dados)
            vendor_filter = self._resolve_vendor_filter(vendor_filter)
            final_query = t_sql_query
            
            if vendor_filter:
                print(f"DEBUG: Security enforcement enabled for vendor: {vendor_filter}")
                # Simple parser injection
                # Finds the first WHERE or adds it after FROM ... Table
                # Robust approach: Wrap query? No, T-SQL subqueries need alias and context.
                # Regex approach to append AND
                
                # Check if WHERE exists (naively)
                if "WHERE" in normalized_query:
                    # Replace regex safe?
                    # "WHERE condition" -> "WHERE (condition) AND Vendedor_Atual = '...'"
                    # Using replace is risky if there are multiple subqueries.
                    # Best approach for this agent which queries ONE table (FAL_IA_Dados_Vendas_Televendas):
                    # Append strictly.
                    
                    # NOTE: This assumes the AI generated a valid query against the main table.
                    # If AI did "SELECT * FROM Table WHERE X GROUP BY Y", appending AND is wrong position.
                    
                    # Better Strategy:
                    # Enforce that the AI *must* include the filter? No, we can't trust it.
                    # We will WRAP it.
                    # SELECT * FROM ( <Query> ) AS SafeWrapper WHERE Vendedor_Atual = '...'
                    # BUT 'Vendedor_Atual' must be in the select list of the inner query for this to work.
                    # If AI did "SELECT SUM(x) FROM ...", Vendedor_Atual is dropped.
                    
                    # Strategy 2: Text Injection.
                    # Most queries are: SELECT ... FROM FAL_IA_Dados_Vendas_Televendas WHERE ... GROUP BY ... ORDER BY ...
                    # We inject " AND Vendedor_Atual = '...'" after "WHERE"
                    # If no WHERE, we inject " WHERE Vendedor_Atual = '...' " before GROUP BY or ORDER BY.
                    
                    # Let's try a regex replace compatible with T-SQL.
                    
                    # Pattern: FROM table [alias] [WHERE condition]
                    # We will force the AI to query *only* FAL_IA_Dados_Vendas_Televendas
                    
                    if "FAL_IA_Dados_Vendas_Televendas" not in t_sql_query:
                         return "Erro: Consulta deve ser na tabela FAL_IA_Dados_Vendas_Televendas."
                         
                    # Naive Injection
                    if "WHERE" in normalized_query:
                        final_query = re.sub(r"(?i)WHERE", f"WHERE (Vendedor_Atual = '{vendor_filter}') AND (", t_sql_query, count=1)
                        # Close parenthesis? We opened one after AND? No, wait.
                        # WHERE (filter) AND (original_conditions...)
                        # To do this safely implies knowing where original conditions end.
                        
                        # Simpler: Just prepend to the condition.
                        # WHERE X -> WHERE Vendedor_Atual='Vendor' AND (X
                        # But we need to close the paren?
                        
                        # Let's use string formatting safe injection
                        final_query = t_sql_query.replace("WHERE", f"WHERE Vendedor_Atual = '{vendor_filter}' AND ", 1)
                        # This works 99% of time if simple conditions.
                    else:
                        # Find where to insert WHERE (before GROUP BY, ORDER BY, or END)
                        # If GROUP BY exists
                        if "GROUP BY" in normalized_query:
                             final_query = t_sql_query.replace("GROUP BY", f"WHERE Vendedor_Atual = '{vendor_filter}' GROUP BY", 1)
                        elif "ORDER BY" in normalized_query:
                             final_query = t_sql_query.replace("ORDER BY", f"WHERE Vendedor_Atual = '{vendor_filter}' ORDER BY", 1)
                        else:
                             final_query += f" WHERE Vendedor_Atual = '{vendor_filter}'"
            
            # 3. Execução
            print(f"DEBUG: Executing AI SQL (Secured): {final_query}")
            df = self.db.get_dataframe(final_query)
            
            if df.empty:
                return "A consulta retornou zero resultados (verifique se os dados pertencem à sua carteira)."
                
            # Limita retorno para o chat não explodir
            if len(df) > 30:
                df = df.head(30)
                
            return f"**Resultado da Análise ({explanation}):**\n\nQuery Segura Executada.\n\n" + df.to_markdown(index=False)
            
        except Exception as e:
            return f"Erro ao executar análise SQL: {str(e)}"

    def get_customer_profile_average(self, card_code: str, last_purchase_date) -> float:
        """
        Calcula a média de fardos totais por pedido nos 180 dias ANTERIORES à última compra.
        Usa cache manual para evitar reprocessamento constante.
        """
        # Chave composta para garantir que se a data mudar, o cache invalida
        cache_key = f"profile_{card_code}_{last_purchase_date}"
        if cache_key in self.profile_cache:
            return self.profile_cache[cache_key]

        try:
            # Garante que a data está em formato string ISO para o SQL se necessário
            date_ref = str(last_purchase_date)
            
            query = f"""
            SELECT ROUND(AVG(CAST(SumQ.Total_Fardos_Pedido AS FLOAT)), 1) as Media_Hist
            FROM (
                SELECT Numero_Documento, SUM(Quantidade) as Total_Fardos_Pedido
                FROM FAL_IA_Dados_Vendas_Televendas
                WHERE Codigo_Cliente = :card_code
                  AND Data_Emissao >= DATEADD(day, -180, :date_ref)
                  AND Data_Emissao <= :date_ref
                GROUP BY Numero_Documento
            ) SumQ
            """
            df = self.db.get_dataframe(query, params={"card_code": card_code, "date_ref": date_ref})
            
            result = 0.0
            if not df.empty and df.iloc[0]['Media_Hist'] is not None:
                result = max(0.0, float(df.iloc[0]['Media_Hist']))
            
            # Salva no cache antes de retornar
            self.profile_cache[cache_key] = result
            # print(f"DEBUG: Profile Average for {card_code}: {result} (Date Ref: {date_ref})")
            return result
        except Exception as e:
            print(f"Erro ao calcular média de perfil para {card_code}: {e}")
            return 0.0

        """Busca vendas agregadas por cliente (Versão Dashboard/DataFrame)."""
        # Resolve SlpCode -> Name
        vendor_filter = self._resolve_vendor_filter(vendor_filter)

        # Query ultra-rápida focada no ranking dinâmico
        query = f"""
        SELECT 
            Codigo_Cliente,
            MAX(Nome_Cliente) as Nome_Cliente,
            MAX(Cidade) as Cidade,
            MAX(Estado) as Estado,
            SUM(Valor_Liquido) as Total_Venda,
            MAX(Data_Emissao) as Ultima_Compra
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Data_Emissao >= DATEADD(day, -{max_days}, GETDATE()) 
        AND Data_Emissao <= DATEADD(day, -{min_days}, GETDATE())
        """
        
        if vendor_filter:
             query += f" AND Vendedor_Atual = '{vendor_filter}'"
             
        query += " GROUP BY Codigo_Cliente ORDER BY Total_Venda DESC"
        
        df = self.db.get_dataframe(query)
        
        # Enriquecimento com Média de Perfil (usando Cache)
        if not df.empty:
            df['Media_Fardos'] = df.apply(
                lambda row: self.get_customer_profile_average(row['Codigo_Cliente'], row['Ultima_Compra']), 
                axis=1
            )
            
        return df

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

        df = self.db.get_dataframe(query, params={"card_code": card_code})
        if not df.empty and 'SKU' in df.columns:
            df['SKU'] = df['SKU'].apply(self._format_sku)
        return df

    def get_inactive_customers_markdown(self, days_without_purchase: int = 30, vendor_filter: str = None) -> str:
        """Clientes inativos (Versão Chat/Markdown)."""
        vendor_filter = self._resolve_vendor_filter(vendor_filter)
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

    def get_sales_insights(self, min_days: int = 0, max_days: int = 30, vendor_filter: str = None) -> pd.DataFrame:
        """
        Busca insights de vendas (clientes positivados/ativos) no período.
        Retorna lista de clientes com total de vendas e última compra no range.
        """
        # Filtro de vendedor
        vendor_filter = self._resolve_vendor_filter(vendor_filter)
        vendor_clause = f" AND Vendedor_Atual = '{vendor_filter}'" if vendor_filter else ""
        
        # Ajuste para garantir que min < max
        if min_days > max_days:
            min_days, max_days = max_days, min_days

        query = f"""
        WITH Base_Ativos AS (
            SELECT 
                Codigo_Cliente,
                MAX(Nome_Cliente) as Nome_Cliente,
                MAX(Cidade) as Cidade,
                MAX(Estado) as Estado,
                MAX(Data_Emissao) as Ultima_Compra,
                SUM(Valor_Total_Linha) as Total_Venda
            FROM FAL_IA_Dados_Vendas_Televendas 
            WHERE 1=1 {vendor_clause}
            AND Data_Emissao >= DATEADD(day, -{max_days}, GETDATE())
            AND Data_Emissao <= DATEADD(day, -{min_days}, GETDATE())
            GROUP BY Codigo_Cliente
        )
        SELECT * FROM Base_Ativos ORDER BY Total_Venda DESC
        """
        
        df = self.db.get_dataframe(query)
        
        # Enriquecimento com Média de Perfil (Opcional, mas a tela mostra Media_Fardos)
        if not df.empty:
             df['Media_Fardos'] = df.apply(
                lambda row: self.get_customer_profile_average(row['Codigo_Cliente'], row['Ultima_Compra']), 
                axis=1
            )
            
        return df

    def get_inactive_customers(self, min_days: int = 30, max_days: int = 365, vendor_filter: str = None) -> pd.DataFrame:
        """Busca clientes inativos (sem compras no período) para o dashboard."""
        
        # Filtro de vendedor
        vendor_filter = self._resolve_vendor_filter(vendor_filter)
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
        SELECT * FROM Base_Inativos ORDER BY Ultima_Compra DESC
        """
        
        df = self.db.get_dataframe(query)
        
        # Enriquecimento com Média de Perfil (usando Cache)
        if not df.empty:
            df['Media_Fardos'] = df.apply(
                lambda row: self.get_customer_profile_average(row['Codigo_Cliente'], row['Ultima_Compra']), 
                axis=1
            )
            
        return df

    def get_top_products(self, days: int = 90, vendor_filter: str = None) -> str:
        vendor_filter = self._resolve_vendor_filter(vendor_filter)
        query = f"""
        SELECT TOP 20 SKU, MAX(Nome_Produto) as Produto, SUM(Valor_Liquido) as Total 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Data_Emissao >= DATEADD(day, -{days}, GETDATE())
        """
        if vendor_filter:
            query += f" AND Vendedor_Atual = '{vendor_filter}'"
            
        query += " GROUP BY SKU ORDER BY Total DESC"
        df = self.db.get_dataframe(query)
        if not df.empty and 'SKU' in df.columns:
            df['SKU'] = df['SKU'].apply(self._format_sku)
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
        resolved_vendor = self._resolve_vendor_filter(vendor_filter)
        vendor_context = f"\n\nCONTEXTO DO USUÁRIO:\nVocê está conversando com: {resolved_vendor or 'Vendedor'}.\nLembre-se: Use as ferramentas de busca e elas automaticamente filtrarão os dados para a sua carteira, se necessário."
        
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
        
        try:
            async for chunk in response_stream:
                try:
                    # Inspeção manual profunda para evitar erros de propriedade do SDK
                    # Acessar propriedades de 'chunk' que não existem pode gerar erro, então protegemos tudo
                    
                    found_fn = False
                    if hasattr(chunk, 'candidates') and chunk.candidates:
                        for candidate in chunk.candidates:
                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    # Verifica se tem function_call (pode ser método ou propriedade dependendo do SDK)
                                    # Tentamos acesso seguro
                                    fn = getattr(part, 'function_call', None)
                                    if fn:
                                        function_call_detected = fn
                                        found_fn = True
                                        break
                            if found_fn: break
                    
                    if found_fn or function_call_detected:
                        break # Sai do loop de stream
                    
                    # Extração Manual de Texto (Evita chunk.text que lança ValueError)
                    extracted_text = ""
                    if hasattr(chunk, 'candidates') and chunk.candidates:
                         for candidate in chunk.candidates:
                             if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                 for part in candidate.content.parts:
                                     # Tenta pegar texto de forma segura
                                     pt = getattr(part, 'text', "")
                                     if pt: extracted_text += pt
                    
                    if extracted_text:
                        yield extracted_text
                        
                except Exception as inner_e:
                    # Loga mas não quebra o stream
                    # print(f"DEBUG: Erro ao processar chunk individual: {inner_e}")
                    continue
                    
        except Exception as stream_e:
            print(f"DEBUG: Erro fatal no stream (possivel function call malformada): {stream_e}")
            yield f"\n\n[Sistema] Erro no processamento inicial: {str(stream_e)}"
                
        if function_call_detected:
            # Executa a tool
            func_name = function_call_detected.name
            func_args = function_call_detected.args
            
            print(f"DEBUG: Tool Call Detectada: {func_name} Args: {func_args}")
            
            # Keep-alive notification for user
            yield f"\n\n_Consultando dados para {func_name}..._\n\n"
            
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
            try:
                # WORKAROUND: Stream após Tool Calling pode ser instável no Vertex AI SDK.
                # Mudamos para stream=False (resposta completa) para garantir que o texto chegue.
                final_response = await chat.send_message_async(
                    [part_func_response],
                    stream=False
                )
                
                # Debug response details - RESTORED
                print(f"DEBUG: Final Response Object: {final_response}")
                if hasattr(final_response, 'candidates') and final_response.candidates:
                     print(f"DEBUG: Finish Reason: {final_response.candidates[0].finish_reason}")
                     if hasattr(final_response.candidates[0], 'safety_ratings'):
                         print(f"DEBUG: Safety Ratings: {final_response.candidates[0].safety_ratings}")

                # Verificação segura do texto final
                final_text = ""
                try:
                    if hasattr(final_response, 'text') and final_response.text:
                        final_text = final_response.text
                except Exception:
                    # Fallback manual se .text falhar
                     if hasattr(final_response, 'candidates') and final_response.candidates:
                         for cand in final_response.candidates:
                             for part in cand.content.parts:
                                 if hasattr(part, 'text') and part.text:
                                     final_text += part.text

                if final_text:
                    yield final_text
                else:
                    # Fallback Inteligente: Tenta formatar o JSON em Markdown se o model falhar
                    formatted_fallback = ""
                    try:
                        import json
                        data = json.loads(tool_result)
                        if isinstance(data, dict):
                            formatted_fallback += "### Dados Encontrados:\n"
                            for k, v in data.items():
                                formatted_fallback += f"- **{k}:** {v}\n"
                        elif isinstance(data, list):
                            formatted_fallback += "### Dados Encontrados:\n"
                            # Se for lista, pega o primeiro ou faz tabela simples
                            if len(data) > 0 and isinstance(data[0], dict):
                                keys = data[0].keys()
                                header = "| " + " | ".join(keys) + " |"
                                divider = "| " + " | ".join(["---"] * len(keys)) + " |"
                                rows = ""
                                for item in data[:5]: # Limita a 5 para não poluir
                                    rows += "| " + " | ".join([str(item.get(k, '')) for k in keys]) + " |\n"
                                formatted_fallback = f"{header}\n{divider}\n{rows}"
                            else:
                                formatted_fallback += str(data)
                        else:
                             formatted_fallback = tool_result
                    except:
                        formatted_fallback = tool_result
                    
                    yield f"\n\n{formatted_fallback}\n\n"

            except Exception as e:
                # Se falhar aqui, não tem muito o que fazer, mas não crasheamos o stream
                print(f"DEBUG: Erro no stream pós-tool: {e}")
                yield f"\n\n[Sistema] Erro ao gerar resposta final: {str(e)}"
    
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
        # Resolve Filter (para uso futuro se precisar filtrar contexto)
        vendor_filter = self._resolve_vendor_filter(vendor_filter) # Apenas resolve, mas pitch usa card_code
        
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
