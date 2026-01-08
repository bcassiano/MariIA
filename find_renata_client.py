
import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from agents.telesales_agent import TelesalesAgent

agent = TelesalesAgent()
vendor_name = "Renata Rodrigues"

print(f"--- Buscando clientes para: {vendor_name} ---")

# Usa o método existente que já filtra por vendedor
try:
    df = agent.get_customers_by_vendor(vendor_name)
    if not df.empty:
        print(df.head(20).to_markdown(index=False))
    else:
        print("Nenhum cliente encontrado.")
except Exception as e:
    print(f"Erro: {e}")
