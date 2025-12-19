# Script de Build Mobile (Android APK) - VERSÃO DEEP CLEAN

Write-Host "--- Iniciando Build Mobile (Android) - MODO DEEP CLEAN ---"

# 1. Manter na raiz (não entrar em mobile)
# Set-Location "$PSScriptRoot/mobile" 

# ... (limpeza e attrib mantidos)

# 7. Iniciar Build (Profile Preview -> APK)
Write-Host "Iniciando EAS Build (Profile: preview) a partir da RAIZ..."
# Pula a verificação de fingerprint que está falhando (erro 'isexe')
$env:EAS_SKIP_AUTO_FINGERPRINT = "1"

# --non-interactive para não travar
# Importante: O eas.json deve estar na raiz agora.
eas build --platform android --profile preview --non-interactive --clear-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no Build Mobile." -ForegroundColor Red
    exit
}

Write-Host "Build iniciado com sucesso! Acompanhe o link acima."
