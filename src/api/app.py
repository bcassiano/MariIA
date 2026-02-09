from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
import hashlib

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.agents.telesales_agent import TelesalesAgent

app = FastAPI(title="MariIA API", description="API para Inteligência de Vendas")

# Configuração de CORS (Permite acesso do React Native Web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mariia-telesales.web.app",
        "https://mariia-telesales.firebaseapp.com",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8005",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Cache simples ---
_cache = {}
CACHE_TTL = 60  # segundos

# --- Middleware de Segurança ---
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # HSTS (1 ano)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # CSP (Básico para proteção contra XSS e injeção)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://mariia-telesales.web.app"
        # Prevenção de Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevenção de Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# --- Segurança (API Key) ---
from fastapi import Security, Depends
from fastapi.security.api_key import APIKeyHeader

# --- Configurações ---
from src.core.config import get_settings
settings = get_settings()

API_KEY = settings.API_KEY
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Acesso Negado: API Key inválida ou ausente.")

# Instância global do agente (para reuso de conexão)
# Instância global do agente (para reuso de conexão)
agent = TelesalesAgent()

# Configuração de Vendedor Atual (Dinâmico via Header)
# CURRENT_VENDOR removed

from fastapi import Header

async def get_current_vendor(x_user_id: Optional[str] = Header(None, alias="x-user-id")):
    if x_user_id:
        return x_user_id
    # Segurança: Não permitir acesso sem ID explícito em produção
    raise HTTPException(status_code=403, detail="Acesso Negado: ID do Vendedor não fornecido. Use ?user_id=SEU_CODIGO")

# --- Modelos de Dados (Pydantic) ---


class ChatRequest(BaseModel):
    message: str
    history: list = [] # Lista de mensagens anteriores

class CustomerHistoryItem(BaseModel):
    Data_Emissao: str
    Numero_Documento: int
    Status_Documento: str
    SKU: str
    Nome_Produto: str
    Quantidade: float
    Valor_Liquido: float
    Margem_Valor: float

# --- Helper Functions ---
def clean_data(df):
    # Converte Decimal para float
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    
    # Substitui Infinito por None
    df = df.replace([np.inf, -np.inf], None)

    # Garante que colunas com NaN virem object para aceitar None
    for col in df.columns:
        if df[col].isnull().any():
            df[col] = df[col].astype(object)

    # Substitui NaN por None
    df = df.where(pd.notnull(df), None)
    return df

# --- Endpoints ---

@app.get("/", dependencies=[Depends(get_api_key)])
def health_check():
    return {"status": "online", "agent": "TelesalesAgent"}

@app.get("/auth/sap-id", dependencies=[Depends(get_api_key)])
def get_sap_id(email: str):
    """Retorna o SlpCode (SAP ID) vinculado ao email corporativo."""
    try:
        if not email:
            raise HTTPException(status_code=400, detail="E-mail é obrigatório.")
        
        # 🛡️ SECURITY: Use safe parameterization (already implemented in get_dataframe)
        query = "SELECT SlpCode FROM OSLP WHERE Email = :email"
        df = agent.db.get_dataframe(query, params={"email": email.strip().lower()})
        
        if df.empty:
            return {"slpCode": None, "message": f"Nenhum vendedor encontrado para o e-mail: {email}"}
        
        # O SlpCode pode ser retornado como int
        slp_code = int(df.iloc[0]['SlpCode'])
        return {"slpCode": slp_code}
    except Exception as e:
        sys.stderr.write(f"ERRO /auth/sap-id: {str(e)}\n")
        raise HTTPException(status_code=500, detail="Erro interno ao consultar SAP.")

@app.get("/insights")
def get_insights(min_days: int = 0, max_days: int = 30, vendor_filter: str = Depends(get_current_vendor)):
    """Retorna o ranking de vendas dos últimos N dias."""
    try:
        # Gera chave de cache
        cache_key = f"insights_{vendor_filter}_{min_days}_{max_days}"
        
        # Verifica cache
        if cache_key in _cache:
            cached_data, cached_time = _cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=CACHE_TTL):
                sys.stderr.write(f"DEBUG: Cache HIT para {cache_key}\n")
                return cached_data
                
        sys.stderr.write(f"DEBUG: Cache MISS - get_insights REQUEST - min={min_days} max={max_days} vendor={vendor_filter}\n")
        df = agent.get_sales_insights(min_days=min_days, max_days=max_days, vendor_filter=vendor_filter)
        sys.stderr.write(f"DEBUG: get_insights RESULT from Agent - Lines={len(df)}\n")
        
        if not df.empty:
            sys.stderr.write(f"DEBUG: Sample Data:\n{df.head(2).to_markdown()}\n")
        
        df = clean_data(df)
        sys.stderr.write(f"DEBUG: get_insights AFTER CLEAN - Lines={len(df)}\n")
        
        data = df.to_dict(orient="records")
        sys.stderr.write(f"DEBUG: Final JSON Items: {len(data)}\n")
        
        result = {"data": data}
        
        # Salva no cache
        _cache[cache_key] = (result, datetime.now())
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inactive")
def get_inactive(min_days: int = 30, max_days: int = 365, vendor_filter: str = Depends(get_current_vendor)):
    """Retorna clientes inativos (sem compras) há X dias."""
    try:
        df = agent.get_inactive_customers(min_days=min_days, max_days=max_days, vendor_filter=vendor_filter)
        # Converte datas para string
        if not df.empty and 'Ultima_Compra' in df.columns:
            df['Ultima_Compra'] = df['Ultima_Compra'].astype(str)
            
        df = clean_data(df)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/customer/{card_code}/bales_breakdown", dependencies=[Depends(get_api_key)])
def get_bales_breakdown(card_code: str, days: int = 180):
    """Retorna a média de fardos por SKU para um cliente."""
    try:
        df = agent.get_bales_breakdown(card_code=card_code, days=days)
        if df.empty:
            return []
        return clean_data(df).to_dict(orient="records")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/customer/{card_code}", dependencies=[Depends(get_api_key)])
def get_customer(card_code: str):
    """Retorna o histórico de um cliente."""
    try:
        df = agent.get_customer_history(card_code, limit=20)
        # Agrupa por Documento
        grouped_history = []
        customer_name = "Cliente Desconhecido"
        
        if not df.empty:
            df['Data_Emissao'] = df['Data_Emissao'].astype(str)
            df = clean_data(df)
            
            # Pega o nome do primeiro registro
            if 'Nome_Cliente' in df.columns:
                customer_name = df.iloc[0]['Nome_Cliente']
            
            # Limpeza CRÍTICA: Garante que doc number seja int para agrupar corretamente
            # Remove possíveis duplicatas por espaços ou tipos diferentes
            df['Numero_Documento'] = pd.to_numeric(df['Numero_Documento'], errors='coerce').fillna(0).astype(int)

            # Agrupa usando um dicionário para GARANTIR unicidade por Numero_Documento
            grouped_docs_map = {}

            for doc_num, group in df.groupby('Numero_Documento'):

                first_row = group.iloc[0]
                # Calcula total do pedido
                def get_row_val(row):
                    vl = row.get('Valor_Liquido') or 0
                    vtl = row.get('Valor_Total_Linha') or 0
                    vu = row.get('Valor_Unitario') or 0
                    qty = row.get('Quantidade') or 0
                    
                    if vl > 0: return float(vl)
                    if vtl > 0: return float(vtl)
                    return float(vu * qty)

                total_val = sum(get_row_val(row) for _, row in group.iterrows())
                
                doc_obj = {
                    "document_number": int(doc_num),
                    "type": first_row['Tipo_Documento'],
                    "date": first_row['Data_Emissao'],
                    "status": first_row['Status_Documento'],
                    "total_value": float(total_val),
                    "items": group.to_dict(orient="records")
                }
                
                # Sobrescreve se já existir (embora groupby não deva repetir chaves)
                grouped_docs_map[int(doc_num)] = doc_obj
            
            # Converte mapa para lista
            grouped_history = list(grouped_docs_map.values())
            
            grouped_history.sort(key=lambda x: x['date'], reverse=True)
            grouped_history.sort(key=lambda x: x['date'], reverse=True)

        # 2. Busca Detalhes Básicos (Novo)
        details = agent.get_customer_details(card_code)
        
        # Se achou detalhes e o nome no history estava generico, usa o do cadastro
        if details and 'CardName' in details and details['CardName']:
            customer_name = details['CardName']

        return {
            "card_code": card_code, 
            "customer_name": customer_name, 
            "details": details, # Novo campo
            "history": grouped_history
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends/{card_code}", dependencies=[Depends(get_api_key)])
def get_customer_trends_alias(card_code: str):
    """Alias para retornar tendência de vendas (evita conflito de rota)."""
    return get_customer_trends(card_code)

@app.get("/customer/{card_code}/trends", dependencies=[Depends(get_api_key)])
def get_customer_trends(card_code: str):
    """Retorna tendência de vendas para o gráfico."""
    try:
        # Busca tendência de 6 meses
        trends = agent.get_sales_trend(card_code, months=6)
        return trends
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from src.utils.logger import log_pitch_usage, log_pitch_feedback
import uuid

class PitchRequest(BaseModel):
    card_code: str
    target_sku: str
    user_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    pitch_id: str
    feedback_type: str # 'useful' | 'sold'
    user_id: Optional[str] = None

@app.post("/pitch")
async def generate_pitch(request: PitchRequest, vendor_filter: str = Depends(get_current_vendor)):
    """Gera um pitch de vendas usando IA."""
    try:
        pitch = await agent.generate_pitch(request.card_code, request.target_sku, vendor_filter=vendor_filter)
        pitch_id = str(uuid.uuid4())
        
        if not isinstance(pitch, dict):
            pitch = {
                "pitch_text": str(pitch),
                "profile_summary": "Análise não disponível (Texto bruto).",
                "frequency_assessment": "Verificar histórico.",
                "reasons": []
            }
        
        # Ensure all keys exist
        default_keys = {
            "pitch_text": "Texto indisponível.",
            "profile_summary": "Análise não disponível.",
            "frequency_assessment": "Verificar histórico.",
            "suggested_order": [],
            "reasons": []
        }
        for k, v in default_keys.items():
            if k not in pitch:
                pitch[k] = v

        # Log de Uso para Analytics
        try:
            log_pitch_usage(
                card_code=request.card_code,
                target_sku=request.target_sku,
                pitch_generated=pitch.get("pitch_text", ""),
                pitch_id=pitch_id,
                user_id=request.user_id
            )
        except Exception as log_err:
            print(f"Erro ao logar uso do pitch: {log_err}")
        
        # Retorna dicionário aninhado conforme esperado pelo PitchCard.jsx (result.pitch)
        # Retorna dicionário aninhado conforme esperado pelo PitchCard.jsx (result.pitch)
        return {"pitch": pitch, "pitch_id": pitch_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pitch/feedback", dependencies=[Depends(get_api_key)])
def pitch_feedback(request: FeedbackRequest):
    """Registra feedback do usuário sobre o pitch."""
    try:
        log_pitch_feedback(
            pitch_id=request.pitch_id,
            feedback_type=request.feedback_type,
            user_id=request.user_id
        )
        return {"status": "ok"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_agent(request: ChatRequest, vendor_filter: str = Depends(get_current_vendor)):
    """Conversa com o assistente."""
    try:
        response = await agent.chat(request.message, request.history, vendor_filter=vendor_filter)
        return {"response": response}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, vendor_filter: str = Depends(get_current_vendor)):
    """Conversa com o assistente via Streaming (Server-Sent Events style)."""
    async def event_generator():
        try:
            async for chunk in agent.chat_stream(request.message, request.history, vendor_filter=vendor_filter):
                yield chunk
        except Exception as e:
            yield f"Erro no stream: {e}"

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.get("/portfolio")
def get_portfolio(vendor_filter: str = Depends(get_current_vendor)):
    """Retorna análise completa da carteira do vendedor."""
    try:
        result = agent.get_portfolio_analysis(vendor_filter=vendor_filter)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
