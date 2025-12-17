# Script de Deploy de Teste
$PROJECT_ID = "amazing-firefly-475113-p3"
$REGION = "us-central1"
$SERVICE_NAME = "mariia-test"

Write-Host "Iniciando Deploy de Teste..."
gcloud run deploy $SERVICE_NAME `
    --source . `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --project $PROJECT_ID
