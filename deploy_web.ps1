# Script de Deploy Web (Firebase Hosting)

Write-Host "--- Iniciando Deploy Web ---"

# 1. Entrar na pasta mobile
Set-Location "$PSScriptRoot/mobile"

# 2. Build do Expo para Web
Write-Host "Gerando versão estática do site..."
npx expo export --platform web

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no Build Web." -ForegroundColor Red
    exit
}

# 3. Deploy no Firebase
Write-Host "Enviando para o Firebase Hosting..."
# O --non-interactive evita que ele trave pedindo input, mas requer login prévio
npx firebase deploy --only hosting --project amazing-firefly-475113-p3

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no Deploy. Tente rodar 'npx firebase login' antes." -ForegroundColor Red
    exit
}

Write-Host "Deploy Web Concluído! 🚀"
