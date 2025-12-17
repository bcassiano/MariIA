# Script de Deploy Local (Docker Build -> Push -> Cloud Run)

# --- CONFIGURAÇÕES ---
$PROJECT_ID = "amazing-firefly-475113-p3"
$REGION = "us-central1"
$REPO_NAME = "mariia-repo-2"
$IMAGE_NAME = "mariia-backend"
$TAG = "latest"
$IMAGE_URI = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME`:$TAG"

# --- VARIÁVEIS DE AMBIENTE (Recuperadas) ---
$DB_SERVER = "192.168.1.85" 
$DB_DATABASE = "RUSTON_PRODUCAO"
$DB_USER = "powerbi"
$DB_PASSWORD = "P0w3rB1@25"
$DB_DRIVER = "ODBC Driver 18 for SQL Server"
$API_KEY = "mariia-secret-key-123"

# --- 1. Autenticação Docker ---
Write-Host "Configurando autenticação do Docker no GCP..."
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# --- 2. Build Local ---
Write-Host "Iniciando Build Local..."
docker build -t $IMAGE_URI .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no Build Local. Verifique se o Docker Desktop está rodando." -ForegroundColor Red
    exit
}

# --- 3. Push para Artifact Registry ---
Write-Host "Enviando imagem para o Google..."
docker push $IMAGE_URI

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no Push. Verifique sua internet ou permissões." -ForegroundColor Red
    exit
}

# --- 4. Deploy no Cloud Run ---
Write-Host "Iniciando Deploy no Cloud Run..."
gcloud run deploy $IMAGE_NAME `
    --image $IMAGE_URI `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --vpc-connector mariia-vpc-conn `
    --set-env-vars "DB_SERVER=$DB_SERVER" `
    --set-env-vars "DB_DATABASE=$DB_DATABASE" `
    --set-env-vars "DB_USER=$DB_USER" `
    --set-env-vars "DB_PASSWORD=$DB_PASSWORD" `
    --set-env-vars "DB_DRIVER=$DB_DRIVER" `
    --set-env-vars "PROJECT_ID=$PROJECT_ID" `
    --set-env-vars "LOCATION=$REGION" `
    --set-env-vars "MODEL_ID=gemini-1.5-pro-preview-0409" `
    --set-env-vars "API_KEY=$API_KEY"

Write-Host "Deploy concluído com sucesso!"
