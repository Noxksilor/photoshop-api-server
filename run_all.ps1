# Configuration
$ProjectRoot = $PSScriptRoot
$ConfigPath = Join-Path $ProjectRoot "config.json"
$TestClientPath = Join-Path $ProjectRoot "test_client.py"
$ServerPath = Join-Path $ProjectRoot "server.py"
$ApiTestsDir = "C:\ps_jobs\api_tests"

# Check config.json exists
if (-not (Test-Path -Path $ConfigPath -PathType Leaf)) {
    Write-Host "ERROR: Missing config.json. Please copy config.example.json to config.json" -ForegroundColor Red
    exit 1
}

# Load config and check input file
try {
    $Config = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
    $DefaultInput = $Config.default_input
    if (-not (Test-Path -Path $DefaultInput -PathType Leaf)) {
        Write-Host "ERROR: Input file not found at $DefaultInput, please put a PNG there." -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "ERROR: Invalid config.json: $_" -ForegroundColor Red
    exit 1
}

# Create api_tests directory if needed
if (-not (Test-Path -Path $ApiTestsDir -PathType Container)) {
    try {
        New-Item -Path $ApiTestsDir -ItemType Directory -Force | Out-Null
    }
    catch {
        Write-Host "ERROR: Failed to create directory $ApiTestsDir : $_" -ForegroundColor Red
        exit 1
    }
}

# Run server
Write-Host "Starting server..." -ForegroundColor Green
try {
    $ServerProcess = Start-Process -FilePath "python" -ArgumentList $ServerPath -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Minimized
    # Wait for server to start
    Write-Host "Waiting for server to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 8
}
catch {
    Write-Host "ERROR: Failed to start server: $_" -ForegroundColor Red
    exit 1
}

# Run test client
Write-Host "Running test client..." -ForegroundColor Green
try {
    $TestResult = Start-Process -FilePath "python" -ArgumentList $TestClientPath -WorkingDirectory $ProjectRoot -NoNewWindow -Wait -PassThru
    $ExitCode = $TestResult.ExitCode
}
catch {
    Write-Host "ERROR: Failed to run test client: $_" -ForegroundColor Red
    $ExitCode = 1
}

# Optional: Stop server
try {
    if ($null -ne $ServerProcess -and -not $ServerProcess.HasExited) {
        $ServerProcess.Kill()
        Write-Host "Server stopped" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Warning: Failed to stop server: $_" -ForegroundColor Yellow
}

# Exit with test client's exit code
exit $ExitCode
