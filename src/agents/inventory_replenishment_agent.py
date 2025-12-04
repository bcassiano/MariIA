# --- CONFIGURAÇÃO ---
PROJECT_ID = "amazing-firefly-475113-p3"

# MUDANÇA: Tentando Oregon para fugir do bloqueio da Central
LOCATION = "us-west1" 

# ... (resto do código de init) ...

# MUDANÇA: Lista reordenada para priorizar o que funciona
modelos_para_tentar = [
    "gemini-1.0-pro",       # Mais antigo e estável (provável que funcione)
    "gemini-1.5-flash-001", # Mais novo (pode ter fila)
    "gemini-1.5-pro-001"
]