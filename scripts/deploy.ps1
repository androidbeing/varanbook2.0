################################################################################
# scripts/deploy.ps1
#
# Deploys Varanbook to AWS:
#   Backend  -> Lightsail Container Service (Gunicorn + FastAPI)
#   Frontend -> S3 + CloudFront (Vue.js SPA)
#
# Prerequisites (install once):
#   winget install Amazon.AWSCLI Hashicorp.Terraform
#   Docker Desktop must be RUNNING
#
# First-time bootstrap:
#   Copy-Item terraform\terraform.tfvars.example terraform\terraform.tfvars
#   # Fill in db_host, db_password, app_secret_key, etc.
#   .\scripts\deploy.ps1 -Bootstrap
#
# Subsequent deploys:
#   .\scripts\deploy.ps1                 # deploy backend + frontend
#   .\scripts\deploy.ps1 -SkipFrontend  # backend (API) only
#   .\scripts\deploy.ps1 -SkipBackend   # frontend only
################################################################################

[CmdletBinding()]
param(
    [switch]$Bootstrap,
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [string]$TfDir = ".\terraform"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-Step { param($msg) Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "    FAIL: $msg" -ForegroundColor Red ; exit 1 }

# -- Ensure lightsailctl is on PATH (required by 'aws lightsail push-container-image')
$lightsailctlPath = "$env:USERPROFILE\lightsailctl.exe"
if (Test-Path $lightsailctlPath) {
    $env:PATH = "$env:USERPROFILE;$env:PATH"
} elseif (-not (Get-Command lightsailctl -ErrorAction SilentlyContinue)) {
    Write-Step "Downloading lightsailctl plugin (required for Lightsail image push)"
    $prevEAP = $ErrorActionPreference; $ErrorActionPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri "https://s3.us-west-2.amazonaws.com/lightsailctl/latest/windows-amd64/lightsailctl.exe" -OutFile $lightsailctlPath
    $ErrorActionPreference = $prevEAP
    if (Test-Path $lightsailctlPath) {
        $env:PATH = "$env:USERPROFILE;$env:PATH"
        # Persist to user PATH
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($userPath -notlike "*$env:USERPROFILE*") {
            [Environment]::SetEnvironmentVariable("Path", "$env:USERPROFILE;$userPath", "User")
        }
        Write-OK "lightsailctl downloaded to $lightsailctlPath"
    } else {
        Write-Fail "Failed to download lightsailctl. Download manually from: https://lightsail.aws.amazon.com/ls/docs/en_us/articles/amazon-lightsail-install-software"
    }
}

# -- Verify prerequisites
Write-Step "Checking prerequisites"
foreach ($tool in @("aws", "terraform", "docker", "npm")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Fail "$tool not found. Install it and re-run."
    }
}
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
docker info 2>&1 | Out-Null
$dockerExit = $LASTEXITCODE
$ErrorActionPreference = $prevEAP
if ($dockerExit -ne 0) { Write-Fail "Docker Desktop is not running. Start it and re-run." }
Write-OK "All prerequisites present"

# -- Read tfvars
$tfVarsRaw     = Get-Content "$TfDir\terraform.tfvars" -Raw
$AWS_REGION    = if ($tfVarsRaw -match 'aws_region\s*=\s*"([^"]+)"')    { $Matches[1] } else { "ap-south-1" }
$DB_HOST       = if ($tfVarsRaw -match 'db_host\s*=\s*"([^"]+)"')       { $Matches[1] } else { "" }
$DB_PORT       = if ($tfVarsRaw -match 'db_port\s*=\s*(\d+)')           { $Matches[1] } else { "5432" }
$DB_NAME       = if ($tfVarsRaw -match 'db_name\s*=\s*"([^"]+)"')       { $Matches[1] } else { "varanbook" }
$DB_USER       = if ($tfVarsRaw -match 'db_username\s*=\s*"([^"]+)"')   { $Matches[1] } else { "" }
$DB_PASS       = if ($tfVarsRaw -match 'db_password\s*=\s*"([^"]+)"')   { $Matches[1] } else { "" }
$SECRET_KEY    = if ($tfVarsRaw -match 'app_secret_key\s*=\s*"([^"]+)"'){ $Matches[1] } else { "" }
$SMTP_HOST     = if ($tfVarsRaw -match 'smtp_host\s*=\s*"([^"]+)"')     { $Matches[1] } else { "" }
$SMTP_PORT     = if ($tfVarsRaw -match 'smtp_port\s*=\s*(\d+)')         { $Matches[1] } else { "587" }
$SMTP_USER     = if ($tfVarsRaw -match 'smtp_username\s*=\s*"([^"]+)"') { $Matches[1] } else { "" }
$SMTP_PASS     = if ($tfVarsRaw -match 'smtp_password\s*=\s*"([^"]+)"') { $Matches[1] } else { "" }
$SMTP_FROM     = if ($tfVarsRaw -match 'smtp_from\s*=\s*"([^"]+)"')     { $Matches[1] } else { "noreply@varanbook.in" }
$PROJECT       = if ($tfVarsRaw -match 'project_name\s*=\s*"([^"]+)"')  { $Matches[1] } else { "varanbook" }
$ENV           = if ($tfVarsRaw -match 'environment\s*=\s*"([^"]+)"')   { $Matches[1] } else { "production" }

$SERVICE_NAME = "$PROJECT-api-$ENV"

# -- Step 1: Terraform
Write-Step "Initialising Terraform"
Push-Location $TfDir
terraform init -input=false
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Fail "terraform init failed" }

Write-Step "Applying Terraform"
terraform apply -input=false -auto-approve
if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Fail "terraform apply failed" }

$TF_API_URL      = (terraform output -raw api_url 2>$null).Trim()
$TF_LS_SERVICE   = (terraform output -raw lightsail_service_name 2>$null).Trim()
$TF_CF_DIST      = (terraform output -raw cloudfront_distribution_id 2>$null).Trim()
$TF_FE_BUCKET    = (terraform output -raw frontend_bucket_name 2>$null).Trim()
$TF_FRONTEND_URL = (terraform output -raw frontend_url 2>$null).Trim()
Pop-Location

if ($TF_LS_SERVICE) { $SERVICE_NAME = $TF_LS_SERVICE }
if (-not $TF_API_URL) { $TF_API_URL = "https://${SERVICE_NAME}.ap-south-1.cs.amazonlightsail.com" }

Write-OK "Lightsail service : $SERVICE_NAME"
Write-OK "API URL           : $TF_API_URL"
Write-OK "Frontend bucket   : $TF_FE_BUCKET"
Write-OK "CloudFront dist   : $TF_CF_DIST"

# -- Step 2: Build and deploy backend
if (-not $SkipBackend) {
    Write-Step "Building Docker image (Gunicorn + FastAPI)"
    docker build -f Dockerfile -t "varanbook-api:latest" .
    if ($LASTEXITCODE -ne 0) { Write-Fail "Docker build failed" }
    Write-OK "Docker image built"

    Write-Step "Pushing image to Lightsail container service: $SERVICE_NAME"
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $pushOutput = aws lightsail push-container-image `
        --region $AWS_REGION `
        --service-name $SERVICE_NAME `
        --label api `
        --image "varanbook-api:latest" 2>&1
    $pushExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEAP

    Write-Host $pushOutput
    if ($pushExit -ne 0) { Write-Fail "Lightsail image push failed" }

    # Parse image reference e.g. ":varanbook-api-production.api.1"
    $imageRef = ($pushOutput | Select-String '":([^"]+)"').Matches.Value -replace '"',''
    if (-not $imageRef) {
        $imageRef = ":${SERVICE_NAME}.api.1"
        Write-Host "    Could not parse image ref, defaulting to: $imageRef"
    }
    Write-OK "Image pushed: $imageRef"

    $DB_URL = "postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

    $envVars = @{
        APP_ENV               = $ENV
        DEBUG                 = "false"
        SECRET_KEY            = $SECRET_KEY
        DATABASE_URL          = $DB_URL
        DATABASE_POOL_SIZE    = "10"
        DATABASE_MAX_OVERFLOW = "20"
        AWS_REGION            = $AWS_REGION
        ALLOWED_ORIGINS       = "[`"$TF_FRONTEND_URL`",`"http://localhost:5173`"]"
        APP_FRONTEND_URL      = $TF_FRONTEND_URL
        SMTP_HOST             = $SMTP_HOST
        SMTP_PORT             = $SMTP_PORT
        SMTP_USERNAME         = $SMTP_USER
        SMTP_PASSWORD         = $SMTP_PASS
        SMTP_FROM             = $SMTP_FROM
    }

    $containersJson = @{
        api = @{
            image       = $imageRef
            ports       = @{ "8000" = "HTTP" }
            environment = $envVars
        }
    } | ConvertTo-Json -Depth 5 -Compress

    $publicEndpointJson = @{
        containerName = "api"
        containerPort = 8000
        healthCheck   = @{
            healthyThreshold   = 2
            unhealthyThreshold = 2
            timeoutSeconds     = 5
            intervalSeconds    = 10
            path               = "/health"
            successCodes       = "200-299"
        }
    } | ConvertTo-Json -Depth 5 -Compress

    Write-Step "Creating Lightsail deployment"
    aws lightsail create-container-service-deployment `
        --region $AWS_REGION `
        --service-name $SERVICE_NAME `
        --containers $containersJson `
        --public-endpoint $publicEndpointJson | Out-Null

    if ($LASTEXITCODE -ne 0) { Write-Fail "Lightsail deployment creation failed" }
    Write-OK "Deployment created - waiting for it to become active (1-3 min)..."

    # Poll until ACTIVE or FAILED
    $attempts = 0
    do {
        Start-Sleep 15
        $attempts++
        $state = (aws lightsail get-container-service-deployments `
            --service-name $SERVICE_NAME `
            --region $AWS_REGION `
            --query 'deployments[0].state' `
            --output text 2>$null).Trim()
        $elapsed = $attempts * 15
        Write-Host "    Deployment state: $state (${elapsed}s)"
    } while ($state -eq "ACTIVATING" -and $attempts -lt 20)

    if ($state -eq "ACTIVE") {
        Write-OK "Deployment ACTIVE - backend is live at $TF_API_URL"
    } elseif ($state -eq "FAILED") {
        Write-Fail "Lightsail deployment FAILED. Check AWS Console -> Lightsail -> $SERVICE_NAME -> Deployments"
    } else {
        Write-Host "    Deployment state: $state (check console if not ACTIVE soon)" -ForegroundColor Yellow
    }
}

# -- Step 3: Build frontend and deploy to S3 + CloudFront
if (-not $SkipFrontend -and $TF_FE_BUCKET) {
    Write-Step "Building Vue.js frontend (VITE_API_BASE_URL=$TF_API_URL)"
    Push-Location ".\frontend"
    try {
        Set-Content ".env.production" "VITE_API_BASE_URL=$TF_API_URL"
        npm ci
        if ($LASTEXITCODE -ne 0) { Write-Fail "npm ci failed" }
        npm run build
        if ($LASTEXITCODE -ne 0) { Write-Fail "npm build failed" }
    } finally {
        Pop-Location
    }
    Write-OK "Frontend built"

    Write-Step "Syncing frontend to s3://$TF_FE_BUCKET"
    aws s3 sync ".\frontend\dist\" "s3://$TF_FE_BUCKET/" `
        --delete `
        --cache-control "public, max-age=31536000, immutable" `
        --exclude "index.html" `
        --region $AWS_REGION
    aws s3 cp ".\frontend\dist\index.html" "s3://$TF_FE_BUCKET/index.html" `
        --cache-control "no-cache, no-store, must-revalidate" `
        --content-type "text/html" `
        --region $AWS_REGION
    if ($LASTEXITCODE -ne 0) { Write-Fail "S3 sync failed" }
    Write-OK "Frontend synced"

    if ($TF_CF_DIST) {
        Write-Step "Invalidating CloudFront cache"
        aws cloudfront create-invalidation `
            --distribution-id $TF_CF_DIST `
            --paths "/*" | Out-Null
        Write-OK "CloudFront invalidation created (~60s to propagate)"
    }
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host " Deployment complete!" -ForegroundColor Yellow
Write-Host "  Backend  : $TF_API_URL" -ForegroundColor Yellow
Write-Host "  Frontend : $TF_FRONTEND_URL" -ForegroundColor Yellow
Write-Host "  API Docs : $TF_API_URL/docs" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Next step: add the above URLs to cors_origins in terraform.tfvars" -ForegroundColor DarkGray
Write-Host "  then re-run: .\scripts\deploy.ps1 -SkipFrontend" -ForegroundColor DarkGray