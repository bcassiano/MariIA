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
from src.core.config import get_settings
settings = get_settings()

GLOBAL_ENDPOINT = "aiplatform.googleapis.com"
 

class TelesalesAgent:
    def __init__(self):
        print("DEBUG: Iniciando Vertex AI...", flush=True)
        try:
            # FIX: Força o endpoint global para evitar 404 em modelos preview/novos
            vertexai.init(project=settings.PROJECT_ID, location=settings.LOCATION, api_endpoint=GLOBAL_ENDPOINT)
            self.model = GenerativeModel(
                model_name=settings.MODEL_ID,
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

    def get_customer_details(self, card_code: str) -> dict:
        """Busca detalhes básicos do cliente (View Otimizada)."""
        # Usando a View Segura conforme solicitado pelo usuário
        query = """
        SELECT TOP 1
            CardCode,
            CardName,
            AtivoDesde,
            Telefone,
            Email,
            Endereco
        FROM VW_MariIA_ClientDetails
        WHERE CardCode = :card_code
        """
        # Retorna dict vazio se não achar
        try:
            df = self.db.get_dataframe(query, params={"card_code": card_code})
            if not df.empty:
                # Converte para dict e trata valores nulos
                record = df.iloc[0].to_dict()
                return {k: (v if pd.notnull(v) else None) for k, v in record.items()}
            return {"debug_message": f"Cliente {card_code} não encontrado na View."}
        except Exception as e:
            print(f"Erro ao buscar detalhes do cliente: {e}")
            return {"debug_error": str(e)}

    @cached(cache=TTLCache(maxsize=100, ttl=600))
    def get_sales_insights(self, min_days: int = 0, max_days: int = 30, vendor_filter: str = None) -> pd.DataFrame:
        """Busca insights gerais de vendas recentes (Query Parametrizada)."""
        # Filtro de vendedor opcional
        vendor_condition = ""
        if vendor_filter:
            clean_vendor = vendor_filter.replace("'", "''")
            vendor_condition = f"AND Vendedor_Atual LIKE '%{clean_vendor}%'"

        # Calcula datas no Python (apenas data, sem hora, para evitar colons)
        from datetime import datetime, timedelta
        
        # Datas formatadas como YYYY-MM-DD (seguro para SQL Server e sem colons)
        end_date_dt = datetime.now() - timedelta(days=min_days)
        start_date_dt = datetime.now() - timedelta(days=max_days)
        
        end_date = end_date_dt.strftime('%Y-%m-%d')
        start_date = start_date_dt.strftime('%Y-%m-%d')

        # Otimização: Agrupa apenas pelo Código (mais rápido) e pega o MAX dos textos
        # Lógica: >= DataInicio AND < DataFim + 1 dia (para pegar o dia todo até 23:59:59.999 sem usar colons)
        query = f"""
        SELECT TOP 50
            Codigo_Cliente,
            MAX(Nome_Cliente) as Nome_Cliente,
            MAX(Cidade) as Cidade,
            MAX(Estado) as Estado,
            MAX(Data_Emissao) as Ultima_Compra,
            SUM(COALESCE(Valor_Liquido, Valor_Total_Linha)) as Total_Venda
        FROM FAL_IA_Dados_Vendas_Televendas WITH (NOLOCK)
        WHERE Nome_Cliente NOT LIKE '%FANTASTICO ALIMENTOS LTDA%'
        {vendor_condition}
        GROUP BY Codigo_Cliente
        HAVING MAX(Data_Emissao) >= '{start_date}' 
           AND MAX(Data_Emissao) < DATEADD(day, 1, '{end_date}')
        ORDER BY Ultima_Compra DESC
        """
        
        # DEBUG QUERY
        sys.stderr.write(f"DEBUG SQL QUERY:\n{query}\n")
            
        return self.db.get_dataframe(query)

    @cached(cache=TTLCache(maxsize=100, ttl=600))
    def get_inactive_customers(self, min_days: int = 30, max_days: int = 365, vendor_filter: str = None) -> pd.DataFrame:
        """
        Busca clientes sem compras há mais de 'days' dias (Risco de Churn).
        Opcionalmente filtra pela carteira do vendedor atual.
        """
        
        # Filtro de vendedor opcional usando a nova coluna Vendedor_Atual
        vendor_condition = ""
        if vendor_filter:
            # Sanitização básica para evitar injection grosseiro
            clean_vendor = vendor_filter.replace("'", "''") 
            vendor_condition = f"AND Vendedor_Atual LIKE '%{clean_vendor}%'"
        
        # Calcula datas no Python
        from datetime import datetime, timedelta
        # Usando lógica sem colons (YYYY-MM-DD)
        end_date_dt = datetime.now() - timedelta(days=min_days)
        start_date_dt = datetime.now() - timedelta(days=max_days)
        
        end_date = end_date_dt.strftime('%Y-%m-%d')
        start_date = start_date_dt.strftime('%Y-%m-%d')

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
        HAVING MAX(Data_Emissao) >= '{start_date}' 
           AND MAX(Data_Emissao) < DATEADD(day, 1, '{end_date}')
        ORDER BY Ultima_Compra DESC
        """
        
        return self.db.get_dataframe(query)

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

    def get_sales_trend(self, card_code: str, months: int = 6) -> Dict[str, List[float]]:
        """
        Retorna tendência de vendas (Valor Líquido) dos últimos X meses,
        agrupado por categorias chave: Arroz, Feijão e Massas.
        """
        query = f"""
        SELECT
            FORMAT(Data_Emissao, 'yyyy-MM') as Mes,
            CASE 
                WHEN Nome_Produto LIKE '%ARROZ%' THEN 'Arroz'
                WHEN Nome_Produto LIKE '%FEIJAO%' THEN 'Feijão'
                WHEN Nome_Produto LIKE '%MACARRAO%' OR Nome_Produto LIKE '%ESPAGUETE%' OR Nome_Produto LIKE '%LASANHA%' THEN 'Massas'
                ELSE 'Outros'
            END as Categoria,
            SUM(COALESCE(Valor_Liquido, Valor_Total_Linha)) as Total
        FROM FAL_IA_Dados_Vendas_Televendas WITH (NOLOCK)
        WHERE Codigo_Cliente = :card_code
          AND Data_Emissao >= DATEADD(month, -:months, GETDATE())
          AND (
              Nome_Produto LIKE '%ARROZ%' OR 
              Nome_Produto LIKE '%FEIJAO%' OR 
              Nome_Produto LIKE '%MACARRAO%' OR 
              Nome_Produto LIKE '%ESPAGUETE%' OR 
              Nome_Produto LIKE '%LASANHA%'
          )
        GROUP BY 
            FORMAT(Data_Emissao, 'yyyy-MM'),
            CASE 
                WHEN Nome_Produto LIKE '%ARROZ%' THEN 'Arroz'
                WHEN Nome_Produto LIKE '%FEIJAO%' THEN 'Feijão'
                WHEN Nome_Produto LIKE '%MACARRAO%' OR Nome_Produto LIKE '%ESPAGUETE%' OR Nome_Produto LIKE '%LASANHA%' THEN 'Massas'
                ELSE 'Outros'
            END
        ORDER BY Mes
        """
        
        try:
            df = self.db.get_dataframe(query, params={"card_code": card_code, "months": months})
            
            if df.empty:
                return {"labels": [], "datasets": []}

            # Pivotar os dados para o formato do gráfico
            # Meses únicos ordenados
            months_list = sorted(df['Mes'].unique().tolist())
            
            # Inicializa estrutura
            result = {
                "labels": [m.split('-')[1] for m in months_list], # Apenas o número do mês
                "datasets": []
            }
            
            categories = ['Arroz', 'Feijão', 'Massas']
            colors = {
                'Arroz': 'rgba(255, 255, 255, 1)',      # Branco (será ajustado no front) ou Azul
                'Feijão': 'rgba(139, 69, 19, 1)',      # Marrom
                'Massas': 'rgba(255, 215, 0, 1)'       # Amarelo
            }
            
            for cat in categories:
                data = []
                for m in months_list:
                    # Filtra valor para aquele mês e categoria
                    val = df[(df['Mes'] == m) & (df['Categoria'] == cat)]['Total'].sum()
                    data.append(float(val))
                
                result["datasets"].append({
                    "name": cat,
                    "data": data,
                    "color": colors.get(cat, 'rgba(0,0,0,1)')
                })
                
            return result

        except Exception as e:
            print(f"Erro ao gerar tendência: {e}")
            return {"error": str(e)}

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

    async def generate_pitch(self, card_code: str, target_sku: str = "", vendor_filter: str = None) -> dict:
        """Gera um pitch de vendas personalizado com persona de Consultor de Sucesso (Async)."""
        
        # 0. Validação de Carteira (Se filtro estiver ativo)
        if vendor_filter:
            # Verifica se o cliente pertence ao vendedor
            check_query = "SELECT 1 FROM FAL_IA_Dados_Vendas_Televendas WHERE Codigo_Cliente = :card_code AND Vendedor_Atual LIKE :vendor"
            check_df = self.db.get_dataframe(check_query, params={"card_code": card_code, "vendor": f"%{vendor_filter}%"})
            if check_df.empty:
                return {"pitch_text": f"⛔ ERRO: O cliente {card_code} não pertence à carteira de {vendor_filter}.", "profile_summary": "Erro de Permissão", "frequency_assessment": "N/A", "reasons": []}

        # 1. Coleta dados do cliente
        history_df = self.get_customer_history(card_code, limit=20)
        
        if history_df.empty:
            return {"pitch_text": f"Não encontrei dados para o cliente {card_code}.", "profile_summary": "Sem dados", "frequency_assessment": "N/A", "reasons": []}

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
        Você é um Consultor de Sucesso do Cliente Sênior.
        
        OBJETIVO: Analisar os dados do cliente e gerar uma sugestão de venda PRÁTICA e DIRETA.
        
        **ESTRUTURA DE RESPOSTA (JSON OBRIGATÓRIO):**
        Você DEVE responder APENAS com um JSON válido seguindo exatamente este formato (sem markdown, sem ```json):
        {{
            "profile_summary": "Uma frase resumindo o perfil de compra (ex: 'Cliente Commodities - Foco Arroz/Feijão').",
            "frequency_assessment": "Status: 'Em dia', 'Atrasado' ou 'Risco' (Seja breve).",
            "pitch_text": "Script curto para WhatsApp. Sem saudações longas. Vá direto ao ponto: 'Vi que seu estoque de X está baixo. Sugiro repor Y tb'.",
            "suggested_order": [
                {{
                    "sku": "A001 (Exemplo)",
                    "product_name": "Nome do Produto",
                    "quantity": "Quantidade (APENAS NÚMEROS, ex: 10)",
                    "unit_price": "Preço Unitário (floater)",
                    "total": "Total (floater)"
                }}
            ],
            "motivation": "Frase curta para motivar o vendedor (máx 15 palavras).",
            "reasons": [
                {{
                    "icon": "history",
                    "title": "Fonte",
                    "text": "Baseado na média de compras."
                }}
            ]
        }}

        DIRETRIZES:
        1. SEJA MÍNIMALISTA. O vendedor está na rua e tem pouco tempo.
        2. Force a venda de ARROZ (1kg ou 2kg).
        3. Se não tiver preço exato, use o do último pedido ou deixe indicativo.
        4. O 'suggested_order' deve ser técnico. 'quantity' DEVE SER APENAS O NÚMERO (Ex: 10, e NÃO "10 Fardos").
        </system_instructions>
        """

        if not self.model:
            print("ERROR: Modelo Gemini não inicializado.")
            return {"pitch_text": "Modelo de IA não disponível.", "profile_summary": "Erro", "frequency_assessment": "Erro", "reasons": []}

        # 3. Chama o Gemini
        try:
            print(f"DEBUG: Enviando prompt para AI (Tamanho: {len(prompt)} chars)")
            # ASYNC CALL
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.2, # Baixa temperatura para garantir JSON válido
                    "response_mime_type": "application/json" # Força JSON Nativo do Gemini 1.5
                },
                safety_settings=[
                    SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH),
                    SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH),
                    SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH),
                    SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH),
                ]
            )
            
            # Parse do JSON
            try:
                import json
                cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
                print(f"DEBUG: Resposta Raw da IA: {cleaned_text[:100]}...") # Loga inicio da resposta
                pitch_data = json.loads(cleaned_text)
                
                # Validação Extra: Se a IA devolveu string JSON ("..."), transforma em dict
                if isinstance(pitch_data, str):
                    print("AVISO: IA retornou string JSON válida, mas não objeto. Ajustando.")
                    default_keys = {
                        "pitch_text": "Texto indisponível.",
                        "profile_summary": "Análise não disponível.",
                        "frequency_assessment": "Verificar histórico.",
                        "suggested_order": [],
                        "motivation": "Vamos pra cima!",
                        "reasons": []
                    }
                    return {**default_keys, "pitch_text": pitch_data}
                    
                return pitch_data
            except json.JSONDecodeError as je:
                print(f"ERRO JSON: {je}")
                print(f"Conteúdo recebido: {response.text}")
                # Fallbback
                return {
                    "pitch_text": response.text, 
                    "profile_summary": "Não foi possível estruturar o perfil.",
                    "frequency_assessment": "Análise indisponível.",
                    "reasons": []
                }

        except Exception as e:
            return {"pitch_text": f"Erro técnico ao gerar pitch: {e}", "profile_summary": "Erro", "frequency_assessment": "Erro", "reasons": []}

    async def chat(self, user_message: str, history: list = [], vendor_filter: str = None) -> str:
        """Conversa livre com o assistente, com capacidade de buscar dados de clientes (Async)."""
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
            
            response = await self.model.generate_content_async(
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
    import asyncio
    
    parser = argparse.ArgumentParser(description="Agente de Televendas MariIA")
    parser.add_argument("--customer", type=str, help="Código do Cliente (CardCode)")
    parser.add_argument("--sku", type=str, help="SKU Alvo para venda (Opcional)", default="")
    parser.add_argument("--vendor", type=str, help="Simular Vendedor Específico (Filtro de Carteira)", default=None)
    parser.add_argument("--insights", action="store_true", help="Gerar insights gerais de vendas")
    parser.add_argument("--min_days", type=int, default=0, help="Dias mínimos para filtro")
    parser.add_argument("--max_days", type=int, default=30, help="Dias máximos para filtro")

    args = parser.parse_args()
    agent = TelesalesAgent()

    if args.customer:
        print(f"\n--- Analisando Cliente: {args.customer} ---")
        if args.vendor:
            print(f"--- Simulando Vendedor: {args.vendor} ---")
            
        print("Gerando Pitch de Vendas...\n")
        # Run async method
        print(asyncio.run(agent.generate_pitch(args.customer, args.sku, vendor_filter=args.vendor)))
        
    elif args.insights:
        print(f"\n--- Insights de Vendas (Top 50 - {args.min_days} a {args.max_days} dias) ---")
        df = agent.get_sales_insights(min_days=args.min_days, max_days=args.max_days, vendor_filter=args.vendor)
        print(df.to_markdown(index=False))
    else:
        parser.print_help()
