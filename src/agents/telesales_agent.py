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
                1. Adote uma postura PROFISSIONAL e EXECUTIVA. Evite gírias ou informalidade excessiva.
                2. SEJA EXTREMAMENTE CONCISO. Responda em no máximo 3 parágrafos curtos. Vendedores têm pressa.
                3. Foque no LUCRO, na MARGEM e no FECHAMENTO DA VENDA.
                4. Identifique oportunidades de Cross-Selling (venda cruzada) usando APENAS produtos do catálogo.
                5. Se o cliente parou de comprar, sugira uma abordagem de reativação estratégica.
                6. Sempre forneça argumentos concretos baseados nos dados.
                7. Sempre que possível, forneça informações sobre otimização de frete.
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
            COALESCE(Valor_Liquido, Valor_Total_Linha) as Valor_Liquido,
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
    def get_sales_insights(self, min_days: int = 0, max_days: int = 30, vendor_filter: str = None) -> pd.DataFrame:
        """Busca insights gerais de vendas recentes (Query Parametrizada)."""
        # Filtro de vendedor opcional
        vendor_condition = "AND Vendedor_Atual LIKE :vendor" if vendor_filter else ""

        # Nota: DATEADD aceita parâmetros numéricos, mas para garantir, passamos via params
        query = f"""
        SELECT TOP 50
            Codigo_Cliente,
            Nome_Cliente,
            Cidade,
            Estado,
            SUM(COALESCE(Valor_Liquido, Valor_Total_Linha)) as Total_Venda,
            SUM(Margem_Valor) as Total_Margem
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Data_Emissao BETWEEN DATEADD(day, -:max_days, GETDATE()) AND DATEADD(day, -:min_days, GETDATE())
          AND Nome_Cliente NOT LIKE '%FANTASTICO ALIMENTOS LTDA%'
          {vendor_condition}
        GROUP BY Codigo_Cliente, Nome_Cliente, Cidade, Estado
        ORDER BY Total_Venda DESC
        """
        params = {"min_days": min_days, "max_days": max_days}
        if vendor_filter:
            params["vendor"] = f"%{vendor_filter}%"
            
        return self.db.get_dataframe(query, params=params)

    @cached(cache=TTLCache(maxsize=100, ttl=600))
    def get_inactive_customers(self, min_days: int = 30, max_days: int = 365, vendor_filter: str = None) -> pd.DataFrame:
        """
        Busca clientes sem compras há mais de 'days' dias (Risco de Churn).
        Opcionalmente filtra pela carteira do vendedor atual.
        """
        
        # Filtro de vendedor opcional usando a nova coluna Vendedor_Atual
        vendor_condition = "AND Vendedor_Atual LIKE :vendor" if vendor_filter else ""
        
        # Otimização: Agrupa apenas pelo Código (mais rápido) e pega o MAX dos textos
        query = f"""
        SELECT TOP 50
            Codigo_Cliente,
            MAX(Nome_Cliente) as Nome_Cliente,
            MAX(Cidade) as Cidade,
            MAX(Estado) as Estado,
            MAX(Data_Emissao) as Ultima_Compra,
            SUM(COALESCE(Valor_Liquido, Valor_Total_Linha)) as Total_Historico
        FROM FAL_IA_Dados_Vendas_Televendas WITH (NOLOCK)
        WHERE Nome_Cliente NOT LIKE '%FANTASTICO ALIMENTOS LTDA%'
        {vendor_condition}
        GROUP BY Codigo_Cliente
        HAVING MAX(Data_Emissao) BETWEEN DATEADD(day, -:max_days, GETDATE()) AND DATEADD(day, -:min_days, GETDATE())
        ORDER BY Ultima_Compra DESC
        """
        
        params = {"min_days": min_days, "max_days": max_days}
        if vendor_filter:
            params["vendor"] = f"%{vendor_filter}%"
            
        return self.db.get_dataframe(query, params=params)

    def get_customers_by_vendor(self, vendor_name: str) -> pd.DataFrame:
        """
        Busca clientes da carteira ATUAL do vendedor.
        ATUALIZADO: Agora usa a coluna 'Vendedor_Atual' da View.
        """
        query = """
        SELECT DISTINCT
            Codigo_Cliente,
            Nome_Cliente,
            Cidade,
            Estado
        FROM FAL_IA_Dados_Vendas_Televendas WITH (NOLOCK)
        WHERE Vendedor_Atual LIKE :vendor
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
            SUM(COALESCE(Valor_Liquido, Valor_Total_Linha)) as Total_Vendas
        FROM FAL_IA_Dados_Vendas_Televendas WITH (NOLOCK)
        WHERE Data_Emissao >= DATEADD(day, -:days, GETDATE())
        GROUP BY SKU
        ORDER BY Total_Vendas DESC
        """
        return self.db.get_dataframe(query, params={"days": days})

    def generate_pitch(self, card_code: str, target_sku: str = "", vendor_filter: str = None) -> str:
        """Gera um pitch de vendas personalizado com persona de Consultor de Sucesso."""
        
        # 0. Validação de Carteira (Se filtro estiver ativo)
        if vendor_filter:
            # Verifica se o cliente pertence ao vendedor
            check_query = "SELECT 1 FROM FAL_IA_Dados_Vendas_Televendas WHERE Codigo_Cliente = :card_code AND Vendedor_Atual LIKE :vendor"
            check_df = self.db.get_dataframe(check_query, params={"card_code": card_code, "vendor": f"%{vendor_filter}%"})
            if check_df.empty:
                return f"⛔ ERRO: O cliente {card_code} não pertence à carteira de {vendor_filter}."

        # 1. Coleta dados do cliente
        history_df = self.get_customer_history(card_code, limit=20)
        
        if history_df.empty:
            return f"Não encontrei dados para o cliente {card_code}."

        # Extrai dados básicos para o template
        try:
            # Pega o nome do cliente da primeira linha
            customer_name = history_df.iloc[0]['Nome_Cliente']
            # Pega a data da última compra
            last_purchase = history_df.iloc[0]['Data_Emissao']
        except:
            customer_name = "Cliente"
            last_purchase = "Desconhecida"

        # Resume os dados para o prompt
        history_summary = history_df.to_markdown(index=False)
        
        # 2. Monta o prompt com DATA CONTEXTUALIZADA
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""
        <contexto_dados>
            <cliente>
                <nome>{customer_name}</nome>
                <data_atual>{current_date}</data_atual>
                <data_ultima_compra>{last_purchase}</data_ultima_compra>
            </cliente>
            <historico_compras>
                {history_summary}
            </historico_compras>
            <produtos_foco>
                <item>Arroz Branco 1kg</item>
                <item>Arroz Branco 2kg</item>
                {f'<item>{target_sku}</item>' if target_sku else ''}
            </produtos_foco>
        </contexto_dados>

        <system_instructions>
        Você é um Consultor de Sucesso do Cliente Sênior, não um vendedor agressivo. Seu objetivo primário é a retenção e reativação de clientes inativos (Churn).

        **DIRETRIZES DE PERSONA:**
        1.  **Tom de Voz:** Empático, investigativo e "suave". Nunca culpe o cliente pela ausência. Use uma abordagem de "sentimos sua falta e queremos entender".
        2.  **Análise Temporal:** Antes de responder, analise a tag <data_ultima_compra> e compare com a <data_atual>. Classifique o cliente como:
            * *Risco Baixo:* 15-30 dias sem compra.
            * *Risco Médio:* 31-60 dias sem compra.
            * *Churn:* >60 dias.
            Adapte a urgência do discurso baseada nessa classificação.
        3.  **Imperativo de Venda (Non-negotiable):** Independente do histórico, você DEVE oferecer Arroz 1kg e 2kg. Enquadre isso como uma "oportunidade exclusiva" ou "reposição estratégica", nunca como algo aleatório.
        4.  **O Pedido Ideal:** Ao final, sugira um pedido concreto. A lógica deve ser: (Itens mais comprados do histórico) + (Arroz 1kg/2kg).

        **ESTRUTURA DE RESPOSTA (Chain of Thought):**
        Não responda imediatamente. Pense passo a passo (mas não mostre o pensamento ao usuário final, apenas a resposta estruturada):
        1.  Calcule os dias inativos.
        2.  Identifique os produtos favoritos no <historico_compras>.
        3.  Formule a pergunta de sondagem sobre o motivo da ausência (preço? concorrência? estoque cheio?).
        4.  Crie o gancho para o Arroz.
        5.  Monte o Pedido Ideal.
        
        **SAÍDA FINAL (O SCRIPT):**
        Gere apenas o script de abordagem para este cliente via WhatsApp/Telefone.

        O script deve conter:
        1.  **Abertura:** Saudação quente reconhecendo o tempo específico (semanas/meses) que não nos falamos.
        2.  **Investigação:** Uma pergunta aberta e não ameaçadora para entender o motivo da não compra recorrente (Ex: "Houve alguma mudança na sua operação?").
        3.  **Pitch do Arroz:** Uma transição natural oferecendo o Arroz 1kg e 2kg, citando condições especiais.
        4.  **Fechamento (Pedido Ideal):** Apresente uma lista pronta sugerida contendo os itens que ele costuma comprar + o Arroz, perguntando se podemos faturar essa grade.
        </system_instructions>
        """

        if not self.model:
            return "Modelo de IA não disponível. Apenas dados carregados."

        # 3. Chama o Gemini
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.4, # Um pouco mais alto para permitir a empatia/criatividade da persona
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

    def chat(self, user_message: str, history: list = [], vendor_filter: str = None) -> str:
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

        # Cenário 2: Carteira de Vendedor (Atualizado para usar Vendedor_Atual)
        elif "carteira" in user_message.lower():
            # Se o usuário pedir "minha carteira", usa o filtro do vendedor atual
            target_vendor = vendor_filter if "minha" in user_message.lower() and vendor_filter else None
            
            # Se não, tenta extrair o nome da mensagem
            if not target_vendor:
                vendor_match = re.search(r'carteira (?:de|da|do)?\s*([A-Za-zÀ-ÿ]+)', user_message, re.IGNORECASE)
                if vendor_match:
                    target_vendor = vendor_match.group(1)
            
            if target_vendor:
                try:
                    customers_df = self.get_customers_by_vendor(target_vendor)
                    if not customers_df.empty:
                        # Limita a 50 para não estourar tokens
                        context_data = f"\n\n[DADOS DO SISTEMA - CARTEIRA ATUAL DE {target_vendor.upper()}]:\n{customers_df.head(50).to_markdown(index=False)}"
                    else:
                        context_data = f"\n\n[SISTEMA]: Não encontrei clientes na carteira atual de {target_vendor}."
                except Exception as e:
                    print(f"Erro ao buscar carteira: {e}")
        
        # Cenário 3: Perguntas Gerais sobre Vendas/Clientes
        elif any(term in user_message.lower() for term in ["venda", "ligar", "cliente", "melhor", "top", "inativo", "parado", "comprou", "ranking", "faturamento", "data", "quando", "ultimo", "ultima", "lista", "tabela", "analise", "sugestao", "estrategia", "potencial"]):
            try:
                # Busca Top 20 Clientes Ativos (COM FILTRO SE HOUVER)
                active_df = self.get_sales_insights(max_days=30, vendor_filter=vendor_filter).head(20)
                
                # Busca Top 20 Clientes Inativos (COM FILTRO SE HOUVER)
                inactive_df = self.get_inactive_customers(max_days=30, vendor_filter=vendor_filter).head(20)
                
                context_data = f"""
                \n\n[DADOS DO SISTEMA - TOP CLIENTES ATIVOS (30 DIAS) - CARTEIRA: {vendor_filter or 'TODOS'}]:
                {active_df.to_markdown(index=False) if not active_df.empty else "Sem dados."}
                
                \n[DADOS DO SISTEMA - CLIENTES INATIVOS/RISCO (30 DIAS) - CARTEIRA: {vendor_filter or 'TODOS'}]:
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
            
            CONTEXTO ATUAL (DADOS REAIS):
            {context_data}
            
            USUÁRIO: {user_message}
            
            REGRAS DE OURO (ANTI-ALUCINAÇÃO):
            - Baseie-se ESTRITAMENTE nos dados de contexto fornecidos acima.
            - NÃO invente produtos, datas ou valores que não estejam na tabela.
            - Se não houver dados suficientes para uma conclusão, diga "Não há dados suficientes".

            TRANSPARÊNCIA (OBRIGATÓRIO):
            Ao final da resposta, adicione uma seção "🔍 Por que sugeri isso?":
            - Cite a fonte dos dados (ex: "Baseado no histórico de compras").
            - Explique o cálculo ou lógica usada.

            ASSISTENTE:"""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.2,
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
            return f"Erro ao processar mensagem: {e}"

# --- CLI para Teste ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente de Televendas MariIA")
    parser.add_argument("--customer", type=str, help="Código do Cliente (CardCode)")
    parser.add_argument("--sku", type=str, help="SKU Alvo para venda (Opcional)", default="")
    parser.add_argument("--vendor", type=str, help="Simular Vendedor Específico (Filtro de Carteira)", default=None)
    parser.add_argument("--insights", action="store_true", help="Gerar insights gerais de vendas")

    args = parser.parse_args()
    agent = TelesalesAgent()

    if args.customer:
        print(f"\n--- Analisando Cliente: {args.customer} ---")
        if args.vendor:
            print(f"--- Simulando Vendedor: {args.vendor} ---")
            
        print("Gerando Pitch de Vendas...\n")
        print(agent.generate_pitch(args.customer, args.sku, vendor_filter=args.vendor))
        
    elif args.insights:
        print("\n--- Insights de Vendas (Top 50 - 30 dias) ---")
        df = agent.get_sales_insights(vendor_filter=args.vendor)
        print(df.to_markdown(index=False))
    else:
        parser.print_help()
