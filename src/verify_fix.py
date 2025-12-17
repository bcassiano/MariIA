import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.agents.telesales_agent import TelesalesAgent

def verify_fix():
    print("Inicializando agente...")
    agent = TelesalesAgent()
    card_code = "C013314"
    
    print(f"Buscando histórico para {card_code}...")
    df = agent.get_customer_history(card_code, limit=10)
    
    if df.empty:
        print("Nenhum dado encontrado.")
    else:
        print(df[['Numero_Documento', 'Data_Emissao', 'Valor_Liquido']].to_markdown(index=False))

if __name__ == "__main__":
    verify_fix()
