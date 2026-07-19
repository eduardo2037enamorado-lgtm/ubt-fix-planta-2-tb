# Despliegue automatico a GitHub + Render
$ErrorActionPreference = "Stop"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Set-Location $PSScriptRoot

Write-Host "=== UBT Fix Planta 2 TB - Despliegue en Render ===" -ForegroundColor Cyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando Git..." -ForegroundColor Yellow
    winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando GitHub CLI..." -ForegroundColor Yellow
    winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
}

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

if (-not (Test-Path .git)) {
    git init
    git add -A
    git commit -m "UBT Fix Planta 2 TB"
}

gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Inicia sesion en GitHub (se abrira el navegador)..." -ForegroundColor Yellow
    gh auth login -h github.com -p https -w
}

$repoName = "ubt-fix-planta-2-tb"
$owner = (gh api user -q .login)
$remote = "https://github.com/$owner/$repoName.git"

if (-not (gh repo view "$owner/$repoName" 2>$null)) {
    gh repo create $repoName --public --source=. --remote=origin --push
} else {
    git branch -M main 2>$null
    git remote add origin $remote 2>$null
    git push -u origin main
}

Write-Host ""
Write-Host "Repositorio listo: https://github.com/$owner/$repoName" -ForegroundColor Green
Write-Host ""
Write-Host "Siguiente paso en Render:" -ForegroundColor Cyan
Write-Host "1. Abre https://dashboard.render.com/select-repo?type=blueprint"
Write-Host "2. Conecta GitHub y selecciona el repo $repoName"
Write-Host "3. Render usara render.yaml automaticamente"
Write-Host "4. Cuando termine, abre https://$repoName.onrender.com/codigos"
Write-Host "5. Descarga el PDF y pega las etiquetas en las UBT"
Write-Host ""
Write-Host "Codigo de acceso en la nube: 1010" -ForegroundColor Yellow
