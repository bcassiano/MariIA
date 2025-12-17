# Script de Configuração GCP para MariIA
# Este script configura a infraestrutura base para o Cloud Run e conectividade com SQL Server.

# --- CONFIGURAÇÕES (Preencha antes de rodar) ---
$PROJECT_ID = "amazing-firefly-475113-p3"
$REGION = "us-central1"
$REPO_NAME = "mariia-repo"
$VPC_NAME = "mariia-vpc"
$CONNECTOR_NAME = "mariia-vpc-conn"

# --- 1. Configuração Inicial ---
Write-Host "Configurando projeto $PROJECT_ID..."
gcloud config set project $PROJECT_ID

Write-Host "Habilitando APIs necessárias..."
gcloud services enable artifactregistry.googleapis.com run.googleapis.com vpcaccess.googleapis.com compute.googleapis.com

# --- 2. Artifact Registry (Para Docker) ---
Write-Host "Criando repositório no Artifact Registry..."
gcloud artifacts repositories create $REPO_NAME `
    --repository-format=docker `
    --location=$REGION `
    --description="Repositorio Docker MariIA"

# --- 3. Rede (VPC + Connector) ---
Write-Host "Criando VPC Network..."
gcloud compute networks create $VPC_NAME --subnet-mode=custom

Write-Host "Criando Subnet para o Conector..."
gcloud compute networks subnets create $CONNECTOR_NAME-subnet `
    --network=$VPC_NAME `
    --range=10.8.0.0/28 `
    --region=$REGION

Write-Host "Criando Serverless VPC Access Connector..."
gcloud compute networks vpc-access connectors create $CONNECTOR_NAME `
    --region=$REGION `
    --subnet=$CONNECTOR_NAME-subnet `
    --min-instances=2 `
    --max-instances=3 `
    --machine-type=e2-micro

# --- 4. VPN (Instruções) ---
Write-Host "`n--- PRÓXIMOS PASSOS: VPN ---"
Write-Host "A infraestrutura base está pronta."
Write-Host "Para conectar ao SQL Server On-Premise, você precisa configurar a VPN."
Write-Host "Execute os comandos abaixo manualmente com os dados da sua rede:"
Write-Host ""
Write-Host "1. Criar IP Reservado:"
Write-Host "   gcloud compute addresses create vpn-ip --region=$REGION"
Write-Host ""
Write-Host "2. Criar Gateway VPN:"
Write-Host "   gcloud compute target-vpn-gateways create mariia-vpn-gw --network=$VPC_NAME --region=$REGION"
Write-Host ""
Write-Host "3. Configurar Túnel (Necessita do IP Público da Empresa):"
Write-Host "   gcloud compute forwarding-rules create vpn-rule-esp --address=vpn-ip --target-vpn-gateway=mariia-vpn-gw --ip-protocol=ESP ..."
Write-Host ""
Write-Host "Consulte o DEPLOY_PLAN.md ou seu administrador de rede para finalizar a VPN."
