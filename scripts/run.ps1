param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Local environment not found. Run .\scripts\setup.ps1 first."
    exit 1
}

Set-Location $ProjectRoot
& $VenvPython -m wirewrap_tag_designer @AppArgs
exit $LASTEXITCODE
