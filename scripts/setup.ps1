param(
    [ValidateSet("dev", "runtime")]
    [string]$Mode = "dev"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvDir = Join-Path $ProjectRoot ".venv"

if ($env:PYTHON) {
    $PythonExe = $env:PYTHON
    $PythonArgs = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonExe = "py"
    $PythonArgs = @("-3")
} else {
    $PythonExe = "python"
    $PythonArgs = @()
}

& $PythonExe @PythonArgs -c "import sys; raise SystemExit(sys.version_info < (3, 10))"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.10 or newer is required."
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating local environment at $VenvDir"
    & $PythonExe @PythonArgs -m venv --system-site-packages $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "Could not create the local environment." }
}

$InstallTarget = $ProjectRoot
if ($Mode -eq "dev") {
    $InstallTarget = "${ProjectRoot}[test]"
}

Write-Host "Installing Wire-Wrap Tag Designer ($Mode)"
& $VenvPython -m pip install --no-build-isolation --editable $InstallTarget
if ($LASTEXITCODE -ne 0) { throw "Package installation failed." }

Write-Host ""
Write-Host "Setup complete."
Write-Host "  Run:  .\scripts\run.ps1"
Write-Host "  Test: .\scripts\test.ps1"
Write-Host "  Venv: .\.venv\Scripts\Activate.ps1"
