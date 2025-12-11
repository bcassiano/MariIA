from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import pandas as pd
import numpy as np
from decimal import Decimal

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.agents.telesales_agent import TelesalesAgent

app = FastAPI(title="MariIA API", description="API para Inteligência de Vendas")

# Configuração de CORS (Permite acesso do React Native Web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Segurança (API Key) ---
from fastapi import Security, Depends
from fastapi.security.api_key import APIKeyHeader

API_KEY = os.getenv("API_KEY", "mariia-secret-key-123") # Em produção, use .env forte
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Acesso Negado: API Key inválida ou ausente.")

# Instância global do agente (para reuso de conexão)
agent = TelesalesAgent()

# --- Modelos de Dados (Pydantic) ---
class PitchRequest(BaseModel):
    card_code: str
    target_sku: Optional[str] = ""

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

@app.get("/insights", dependencies=[Depends(get_api_key)])
def get_insights(days: int = 30):
    """Retorna o ranking de vendas dos últimos N dias."""
    try:
        df = agent.get_sales_insights(days=days)
        df = clean_data(df)
        data = df.to_dict(orient="records")
        return {"data": data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inactive", dependencies=[Depends(get_api_key)])
def get_inactive(days: int = 30):
    """Retorna clientes inativos (sem compras) há X dias."""
    try:
        df = agent.get_inactive_customers(days)
        # Converte datas para string
        if not df.empty and 'Ultima_Compra' in df.columns:
            df['Ultima_Compra'] = df['Ultima_Compra'].astype(str)
            
        df = clean_data(df)
        return {"data": df.to_dict(orient="records")}
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
            
            # Agrupa usando Pandas
            for doc_num, group in df.groupby('Numero_Documento'):
                first_row = group.iloc[0]
                total_val = group['Valor_Liquido'].sum()
                
                doc_obj = {
                    "document_number": int(doc_num),
                    "type": first_row['Tipo_Documento'],
                    "date": first_row['Data_Emissao'],
                    "status": first_row['Status_Documento'],
                    "total_value": float(total_val),
                    "items": group.to_dict(orient="records")
                }
                grouped_history.append(doc_obj)
                
            # Ordena por data decrescente
            grouped_history.sort(key=lambda x: x['date'], reverse=True)

        return {"card_code": card_code, "customer_name": customer_name, "history": grouped_history}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pitch", dependencies=[Depends(get_api_key)])
def generate_pitch(request: PitchRequest):
    """Gera um pitch de vendas usando IA."""
    try:
        pitch = agent.generate_pitch(request.card_code, request.target_sku)
        return {"pitch": pitch}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", dependencies=[Depends(get_api_key)])
def chat_with_agent(request: ChatRequest):
    """Conversa com o assistente."""
    try:
        response = agent.chat(request.message, request.history)
        return {"response": response}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
