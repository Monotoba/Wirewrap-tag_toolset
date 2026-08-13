param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Local environment not found. Run .\scripts\setup.ps1 first."
    exit 1
}

if (-not $env:QT_QPA_PLATFORM) { $env:QT_QPA_PLATFORM = "offscreen" }
Set-Location $ProjectRoot
& $VenvPython -m pytest @PytestArgs
exit $LASTEXITCODE
