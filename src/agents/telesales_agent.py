import sys
import os
import json
import argparse
from typing import Dict, List, Optional
import pandas as pd
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
from cachetools import cached, TTLCache

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.database.connector import DatabaseConnector

# Configurações Vertex AI
PROJECT_ID = os.getenv("PROJECT_ID", "amazing-firefly-475113-p3")
LOCATION = os.getenv("LOCATION", "us-central1")
GLOBAL_ENDPOINT = "aiplatform.googleapis.com"
MODEL_ID = "gemini-3-pro-preview" 

class TelesalesAgent:
    def __init__(self):
        print("DEBUG: Iniciando Vertex AI...", flush=True)
        try:
            # FIX: Força o endpoint global para evitar 404 em modelos preview/novos
            vertexai.init(project=PROJECT_ID, location=LOCATION, api_endpoint=GLOBAL_ENDPOINT)
            self.model = GenerativeModel(
                model_name=MODEL_ID,
                system_instruction="""
                Você é um Assistente Especialista em Televendas (B2B).
                Sua missão é analisar dados de clientes e produtos para gerar insights acionáveis e argumentos de venda.
                
                Diretrizes:
                1. Seja conciso e direto. Vendedores têm pouco tempo.
                2. Foque no LUCRO e na MARGEM.
                3. Identifique oportunidades de Cross-Selling (venda cruzada).
                4. Se o cliente parou de comprar, sugira uma abordagem de reativação.
                5. Sempre forneça argumentos concretos baseados nos dados.
                6. Sempre que possível, forneça informações sobre otimização de frete.
                """
            )
            print("DEBUG: Vertex AI OK.", flush=True)
        except Exception as e:
            print(f"AVISO: Falha ao iniciar Vertex AI ({e}). O agente funcionará apenas em modo de dados.", flush=True)
            self.model = None
            
        print("DEBUG: Iniciando DatabaseConnector...", flush=True)
        self.db = DatabaseConnector()
        print("DEBUG: Init concluído.", flush=True)
        # Cache para insights e inativos (10 minutos de duração, máx 100 itens)
        self.cache = TTLCache(maxsize=100, ttl=600)

    def get_customer_history(self, card_code: str, limit: int = 10) -> pd.DataFrame:
        """Busca histórico recente de um cliente específico (Query Parametrizada)."""
        query = f"""
        SELECT
            Data_Emissao,
            Numero_Documento,
            Status_Documento,
            SKU,
            Nome_Produto,
            Quantidade,
            Valor_Liquido,
            Margem_Valor,
            Nome_Cliente,
            Tipo_Documento
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Numero_Documento IN (
            SELECT TOP {limit} Numero_Documento
            FROM FAL_IA_Dados_Vendas_Televendas
            WHERE Codigo_Cliente = :card_code
            GROUP BY Numero_Documento, Data_Emissao
            ORDER BY Data_Emissao DESC
        )
        AND Codigo_Cliente = :card_code
        ORDER BY Data_Emissao DESC, Numero_Documento
        """
        # Passa o parâmetro de forma segura
        return self.db.get_dataframe(query, params={"card_code": card_code})

    @cached(cache=TTLCache(maxsize=100, ttl=600))
    def get_sales_insights(self, days: int = 30) -> pd.DataFrame:
        """Busca insights gerais de vendas recentes (Query Parametrizada)."""
        # Nota: DATEADD aceita parâmetros numéricos, mas para garantir, passamos via params
        query = """
        SELECT TOP 50
            Codigo_Cliente,
            Nome_Cliente,
            Cidade,
            Estado,
            SUM(Valor_Liquido) as Total_Venda,
            SUM(Margem_Valor) as Total_Margem
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Data_Emissao >= DATEADD(day, -:days, GETDATE())
          AND Nome_Cliente NOT LIKE '%FANTASTICO ALIMENTOS LTDA%'
        GROUP BY Codigo_Cliente, Nome_Cliente, Cidade, Estado
        ORDER BY Total_Venda DESC
        """
        return self.db.get_dataframe(query, params={"days": days})

    @cached(cache=TTLCache(maxsize=100, ttl=600))
    def get_inactive_customers(self, days: int = 30) -> pd.DataFrame:
        """Busca clientes sem compras há mais de 'days' dias (Risco de Churn)."""
        # Otimização: Agrupa apenas pelo Código (mais rápido) e pega o MAX dos textos
        query = """
        SELECT TOP 50
            Codigo_Cliente,
            MAX(Nome_Cliente) as Nome_Cliente,
            MAX(Cidade) as Cidade,
            MAX(Estado) as Estado,
            MAX(Data_Emissao) as Ultima_Compra,
            SUM(Valor_Liquido) as Total_Historico
        FROM FAL_IA_Dados_Vendas_Televendas WITH (NOLOCK)
        WHERE Nome_Cliente NOT LIKE '%FANTASTICO ALIMENTOS LTDA%'
        GROUP BY Codigo_Cliente
        HAVING MAX(Data_Emissao) < DATEADD(day, -:days, GETDATE())
        ORDER BY Ultima_Compra DESC
        """
        return self.db.get_dataframe(query, params={"days": days})

    def get_customers_by_vendor(self, vendor_name: str) -> pd.DataFrame:
        """Busca clientes da carteira de um vendedor específico."""
        query = """
        SELECT DISTINCT
            Codigo_Cliente,
            Nome_Cliente,
            Cidade,
            Estado
        FROM FAL_IA_Dados_Vendas_Televendas WITH (NOLOCK)
        WHERE Vendedor LIKE :vendor
          AND Nome_Cliente NOT LIKE '%FANTASTICO ALIMENTOS LTDA%'
        ORDER BY Nome_Cliente
        """
        return self.db.get_dataframe(query, params={"vendor": f"%{vendor_name}%"})

    @cached(cache=TTLCache(maxsize=1, ttl=3600)) # Cache de 1 hora
    def get_top_products(self, days: int = 90) -> pd.DataFrame:
        """Retorna lista dos produtos mais vendidos para referência (Catálogo)."""
        query = """
        SELECT TOP 50
            SKU,
            MAX(Nome_Produto) as Nome_Produto,
            SUM(Valor_Liquido) as Total_Vendas
        FROM FAL_IA_Dados_Vendas_Televendas WITH (NOLOCK)
        WHERE Data_Emissao >= DATEADD(day, -:days, GETDATE())
        GROUP BY SKU
        ORDER BY Total_Vendas DESC
        """
        return self.db.get_dataframe(query, params={"days": days})

    def generate_pitch(self, card_code: str, target_sku: str = "") -> str:
        """Gera um pitch de vendas personalizado para o cliente."""
        
        # 1. Coleta dados do cliente
        history_df = self.get_customer_history(card_code, limit=20)
        
        if history_df.empty:
            return f"Não encontrei dados para o cliente {card_code}."

        # Resume os dados para o prompt (evita estourar tokens)
        history_summary = history_df.to_markdown(index=False)
        
        # 2. Monta o prompt
        prompt = f"""
        ANALISE ESTE CLIENTE ({card_code}):
        
        Histórico Recente de Compras:
        {history_summary}
        
        TAREFA:
        1. Identifique o perfil de compra (o que ele mais compra?).
        2. Calcule a frequência média (ele comprou recentemente?).
        3. Crie um PITCH DE VENDA para ligar para ele hoje.
           {f'Foco especial em vender o produto: {target_sku}' if target_sku else 'Sugira um produto para reposição ou novidade.'}
        
        REGRAS DE OURO (ANTI-ALUCINAÇÃO):
        - Baseie-se ESTRITAMENTE nos dados de histórico fornecidos acima.
        - NÃO invente produtos, datas ou valores que não estejam na tabela.
        - Se não houver dados suficientes para uma conclusão, diga "Não há dados suficientes".

        TRANSPARÊNCIA (OBRIGATÓRIO):
        Ao final do pitch, adicione uma seção "🔍 Por que sugeri isso?":
        - Cite a fonte dos dados (ex: "Baseado no histórico de 20 compras do ERP").
        - Explique o cálculo ou lógica (ex: "Cliente compra a cada 15 dias e está há 20 sem comprar", "Margem deste produto é 10% superior à média").
        """

        if not self.model:
            return "Modelo de IA não disponível. Apenas dados carregados."

        # 3. Chama o Gemini
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.2, # Baixa temperatura para reduzir criatividade/alucinação
                },
                safety_settings=[
                    SafetySetting(
                        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                    ),
                    SafetySetting(
                        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                    ),
                    SafetySetting(
                        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                    ),
                    SafetySetting(
                        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                    ),
                ]
            )
            return response.text
        except Exception as e:
            return f"Erro ao gerar insight de IA: {e}"

    def chat(self, user_message: str, history: list = []) -> str:
        """Conversa livre com o assistente, com capacidade de buscar dados de clientes."""
        if not self.model:
            return "O modelo de IA não está disponível no momento."
            
        # Tenta identificar um código de cliente na mensagem (Ex: C00123)
        import re
        customer_match = re.search(r'\b(C\d+)\b', user_message, re.IGNORECASE)
        
        context_data = ""
        
        # Carrega catálogo de produtos (Top 50) para evitar alucinações
        try:
            products_df = self.get_top_products()
            if not products_df.empty:
                products_list = products_df.to_markdown(index=False)
                context_data += f"\n\n[CATÁLOGO DE PRODUTOS DISPONÍVEIS (TOP 50)]:\n{products_list}\n\nATENÇÃO: Apenas sugira produtos listados acima ou que constem no histórico do cliente. NÃO invente produtos."
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")
        
        # Cenário 1: Cliente Específico
        if customer_match:
            card_code = customer_match.group(1).upper()
            try:
                history_df = self.get_customer_history(card_code, limit=15)
                if not history_df.empty:
                    history_summary = history_df.to_markdown(index=False)
                    context_data = f"\n\n[DADOS DO SISTEMA PARA O CLIENTE {card_code}]:\n{history_summary}\n\nUse esses dados para responder à pergunta do usuário com base no histórico real."
                else:
                    context_data = f"\n\n[SISTEMA]: Busquei no banco de dados, mas não encontrei vendas recentes para o cliente {card_code}."
            except Exception as e:
                print(f"Erro ao buscar dados no chat: {e}")

        # Cenário 2: Carteira de Vendedor (Otimizado)
        elif "carteira" in user_message.lower():
            vendor_match = re.search(r'carteira (?:de|da|do)?\s*([A-Za-zÀ-ÿ]+)', user_message, re.IGNORECASE)
            if vendor_match:
                vendor_name = vendor_match.group(1)
                try:
                    customers_df = self.get_customers_by_vendor(vendor_name)
                    if not customers_df.empty:
                        # Limita a 50 para não estourar tokens
                        context_data = f"\n\n[DADOS DO SISTEMA - CARTEIRA DE {vendor_name.upper()}]:\n{customers_df.head(50).to_markdown(index=False)}"
                    else:
                        context_data = f"\n\n[SISTEMA]: Não encontrei clientes para o vendedor {vendor_name}."
                except Exception as e:
                    print(f"Erro ao buscar carteira: {e}")
        
        # Cenário 3: Perguntas Gerais sobre Vendas/Clientes (Ex: "Quem devo ligar?", "Melhores clientes")
        elif any(term in user_message.lower() for term in ["venda", "ligar", "cliente", "melhor", "top", "inativo", "parado", "comprou", "ranking", "faturamento"]):
            try:
                # Busca Top 20 Clientes Ativos
                active_df = self.get_sales_insights(days=30).head(20)
                # Busca Top 20 Clientes Inativos
                inactive_df = self.get_inactive_customers(days=30).head(20)
                
                context_data = f"""
                \n\n[DADOS DO SISTEMA - TOP CLIENTES ATIVOS (30 DIAS)]:
                {active_df.to_markdown(index=False) if not active_df.empty else "Sem dados."}
                
                \n[DADOS DO SISTEMA - CLIENTES INATIVOS/RISCO (30 DIAS)]:
                {inactive_df.to_markdown(index=False) if not inactive_df.empty else "Sem dados."}
                
                \nUse essas listas para sugerir clientes para o vendedor ligar. Priorize inativos com alto histórico ou ativos com queda."""
            except Exception as e:
                print(f"Erro ao buscar insights no chat: {e}")

        try:
            # Formata o histórico para o prompt
            history_text = ""
            if history:
                # Pega as últimas 6 mensagens para contexto (evita estourar tokens)
                recent_history = history[-6:] 
                for msg in recent_history:
                    role = "USUÁRIO" if msg.get('sender') == 'user' else "ASSISTENTE"
                    history_text += f"{role}: {msg.get('text')}\n"

            # Configuração simples para chat com histórico
            prompt = f"""
            HISTÓRICO DA CONVERSA:
            {history_text}
            
            CONTEXTO ATUAL:
            {context_data}
            
            USUÁRIO: {user_message}
            ASSISTENTE:"""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.2,
                }
            )
            return response.text
        except Exception as e:
            return f"Erro ao processar mensagem: {e}"

# --- CLI para Teste ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente de Televendas MariIA")
    parser.add_argument("--customer", type=str, help="Código do Cliente (CardCode)")
    parser.add_argument("--sku", type=str, help="SKU Alvo para venda (Opcional)", default="")
    parser.add_argument("--insights", action="store_true", help="Gerar insights gerais de vendas")

    args = parser.parse_args()
    agent = TelesalesAgent()

    if args.customer:
        print(f"\n--- Analisando Cliente: {args.customer} ---")
        print("Gerando Pitch de Vendas...\n")
        print(agent.generate_pitch(args.customer, args.sku))
        
    elif args.insights:
        print("\n--- Insights de Vendas (Top 50 - 30 dias) ---")
        df = agent.get_sales_insights()
        print(df.to_markdown(index=False))
    else:
        parser.print_help()
