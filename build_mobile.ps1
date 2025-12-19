# Script de Build Mobile (Android APK) - VERSÃO DEEP CLEAN

Write-Host "--- Iniciando Build Mobile (Android) - MODO DEEP CLEAN ---"

# 1. Entrar na pasta mobile
Set-Location "$PSScriptRoot/mobile"

# 2. Limpeza Profunda (Deep Clean)
Write-Host "Executando limpeza profunda de caches e pastas temporárias..."
Remove-Item -Recurse -Force .expo, .eas, .firebase, node_modules, dist, web-build -ErrorAction SilentlyContinue
Write-Host "Limpeza concluída."

# 3. Correção de Atributos (Windows Native)
Write-Host "Removendo atributos de Somente Leitura (Read-Only), Sistema e Oculto..."
# attrib: -r (remove ReadOnly), -s (remove System), -h (remove Hidden)
# /s (subpastas), /d (pastas também)
cmd /c "attrib -r -s -h /s /d *.*"
Write-Host "Atributos resetados."

# 4. Reinstalar Dependências
Write-Host "Reinstalando dependências..."
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no npm install." -ForegroundColor Red
    exit
}

# 5. Verificar Login EAS
Write-Host "Verificando login no EAS..."
eas whoami
if ($LASTEXITCODE -ne 0) {
    Write-Host "Você não está logado no EAS. Rodando 'eas login'..."
    eas login
}

# 6. Configurar Git para ignorar permissões (Reforço)
git config core.fileMode false

# 6.1 Remover arquivos duplicados/problemáticos
Remove-Item "package-lock (1).json" -ErrorAction SilentlyContinue

# 7. Iniciar Build (Profile Preview -> APK)
Write-Host "Iniciando EAS Build (Profile: preview)..."
# Pula a verificação de fingerprint que está falhando (erro 'isexe')
$env:EAS_SKIP_AUTO_FINGERPRINT = "1"

# --non-interactive para não travar
eas build --platform android --profile preview --non-interactive --clear-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no Build Mobile." -ForegroundColor Red
    exit
}

Write-Host "Build iniciado com sucesso! Acompanhe o link acima."
