# Script para rodar o Backend Localmente (Exposto na Rede)
# Uso: .\run_backend.ps1

Write-Host "Iniciando MariIA Backend em modo DEV (LAN)..." -ForegroundColor Green
Write-Host "A API estará disponível em: http://0.0.0.0:8000" -ForegroundColor Cyan

# Carrega ambiente se necessário (mas uvicorn carrega .env se usar python-dotenv no app)
# Executa uvicorn com host 0.0.0.0 para permitir acesso do celular
uvicorn src.api.app:app --host 0.0.0.0 --port 8005 --reload
