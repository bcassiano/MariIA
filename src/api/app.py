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

# Instância global do agente (para reuso de conexão)
agent = TelesalesAgent()

# --- Modelos de Dados (Pydantic) ---
class PitchRequest(BaseModel):
    card_code: str
    target_sku: Optional[str] = ""

class ChatRequest(BaseModel):
    message: str

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
    
    # Substitui NaN por None
    df = df.replace({np.nan: None})
    return df

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "online", "agent": "TelesalesAgent"}

@app.get("/insights")
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

@app.get("/customer/{card_code}")
def get_customer(card_code: str):
    """Retorna o histórico de um cliente."""
    try:
        df = agent.get_customer_history(card_code, limit=20)
        # Converte datas para string
        if not df.empty:
            df['Data_Emissao'] = df['Data_Emissao'].astype(str)
        
        df = clean_data(df)
        data = df.to_dict(orient="records")
        return {"card_code": card_code, "history": data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pitch")
def generate_pitch(request: PitchRequest):
    """Gera um pitch de vendas usando IA."""
    try:
        pitch = agent.generate_pitch(request.card_code, request.target_sku)
        return {"pitch": pitch}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_with_agent(request: ChatRequest):
    """Conversa com o assistente."""
    try:
        response = agent.chat(request.message)
        return {"response": response}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
