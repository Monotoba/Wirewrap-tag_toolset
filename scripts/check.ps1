$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Local environment not found. Run .\scripts\setup.ps1 first."
    exit 1
}

if (-not $env:QT_QPA_PLATFORM) { $env:QT_QPA_PLATFORM = "offscreen" }
Set-Location $ProjectRoot

& $VenvPython -m pytest
if ($LASTEXITCODE -ne 0) { throw "Tests failed." }

& $VenvPython -m compileall -q src tests
if ($LASTEXITCODE -ne 0) { throw "Byte-compilation failed." }

& $VenvPython -m wirewrap_tag_designer.cli --help *> $null
if ($LASTEXITCODE -ne 0) { throw "CLI smoke check failed." }

Write-Host "Tests, byte-compilation, and CLI smoke check passed."
