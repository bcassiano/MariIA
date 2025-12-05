import sys
import os
import json
import argparse
from typing import Dict, List, Optional
import pandas as pd
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting

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
                """
            )
            print("DEBUG: Vertex AI OK.", flush=True)
        except Exception as e:
            print(f"AVISO: Falha ao iniciar Vertex AI ({e}). O agente funcionará apenas em modo de dados.", flush=True)
            self.model = None
            
        print("DEBUG: Iniciando DatabaseConnector...", flush=True)
        self.db = DatabaseConnector()
        print("DEBUG: Init concluído.", flush=True)

    def get_customer_history(self, card_code: str, limit: int = 10) -> pd.DataFrame:
        """Busca histórico recente de um cliente específico (Query Parametrizada)."""
        query = f"""
        SELECT TOP {limit}
            Data_Emissao,
            Numero_Documento,
            Status_Documento,
            SKU,
            Nome_Produto,
            Quantidade,
            Valor_Liquido,
            Margem_Valor
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Codigo_Cliente = :card_code
        ORDER BY Data_Emissao DESC
        """
        # Passa o parâmetro de forma segura
        return self.db.get_dataframe(query, params={"card_code": card_code})

    def get_sales_insights(self, days: int = 30) -> pd.DataFrame:
        """Busca insights gerais de vendas recentes (Query Parametrizada)."""
        # Nota: DATEADD aceita parâmetros numéricos, mas para garantir, passamos via params
        query = """
        SELECT TOP 50
            Nome_Cliente,
            Cidade,
            Estado,
            SUM(Valor_Liquido) as Total_Venda,
            SUM(Margem_Valor) as Total_Margem
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Data_Emissao >= DATEADD(day, -:days, GETDATE())
        GROUP BY Nome_Cliente, Cidade, Estado
        ORDER BY Total_Venda DESC
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
        """

        if not self.model:
            return "Modelo de IA não disponível. Apenas dados carregados."

        # 3. Chama o Gemini
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.7,
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

    def chat(self, user_message: str) -> str:
        """Conversa livre com o assistente."""
        if not self.model:
            return "O modelo de IA não está disponível no momento."
            
        try:
            # Configuração simples para chat
            response = self.model.generate_content(
                f"USUÁRIO: {user_message}\nASSISTENTE:",
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.7,
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
