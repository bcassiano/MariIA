# Script de Deploy do Backend MariIA para Cloud Run

# --- CONFIGURAÇÕES ---
$PROJECT_ID = "amazing-firefly-475113-p3"
$REGION = "us-central1"
$REPO_NAME = "mariia-repo-2"
$IMAGE_NAME = "mariia-backend"
$TAG = "latest"
$IMAGE_URI = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME`:$TAG"

# --- VARIÁVEIS DE AMBIENTE (Preencha/Verifique) ---
# O DB_SERVER deve ser o IP interno, acessível via VPN
$DB_SERVER = "192.168.1.85" 
$DB_DATABASE = "RUSTON_PRODUCAO" # Confirme o nome do banco
$DB_USER = "powerbi"            # Confirme o usuário
$DB_PASSWORD = "P0w3rB1@25" # <--- ALTERE AQUI
$DB_DRIVER = "ODBC Driver 18 for SQL Server"
$API_KEY = "mariia-secret-key-123" # <--- Defina uma chave forte para produção

# --- 1. Deploy via Source (Dockerfile detectado automaticamente) ---
Write-Host "Iniciando Deploy via Source..."
# Executa diretamente sem Start-Process para evitar erros de Win32 shim
cmd /c "gcloud run deploy $IMAGE_NAME --source . --region $REGION --platform managed --allow-unauthenticated --vpc-connector mariia-vpc-conn --set-env-vars ""DB_SERVER=$DB_SERVER"" --set-env-vars ""DB_DATABASE=$DB_DATABASE"" --set-env-vars ""DB_USER=$DB_USER"" --set-env-vars ""DB_PASSWORD=$DB_PASSWORD"" --set-env-vars ""DB_DRIVER=$DB_DRIVER"" --set-env-vars ""PROJECT_ID=$PROJECT_ID"" --set-env-vars ""LOCATION=$REGION"" --set-env-vars ""MODEL_ID=gemini-3-pro-preview"" --set-env-vars ""API_KEY=$API_KEY"""

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no Deploy. Verifique os logs." -ForegroundColor Red
    exit 1
}

Write-Host "Deploy concluído!"
