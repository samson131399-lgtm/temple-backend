$ErrorActionPreference = 'Stop'

$projectDir = $PSScriptRoot
$python = Join-Path $projectDir '.venv\Scripts\python.exe'
$manage = Join-Path $projectDir 'manage.py'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python executable was not found: $python"
}

if (-not (Test-Path -LiteralPath $manage)) {
    throw "Django manage.py was not found: $manage"
}

Push-Location $projectDir
try {
    & $python $manage backup_database --keep-days 30
    if ($LASTEXITCODE -ne 0) {
        throw 'Database backup failed. Review the error output above.'
    }
}
finally {
    Pop-Location
}
