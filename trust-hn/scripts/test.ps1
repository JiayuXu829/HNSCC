$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonCandidates = @(
    (Join-Path $ProjectRoot '.venv\Scripts\python.exe'),
    (Join-Path (Split-Path -Parent $ProjectRoot) 'tools\python\python.exe'),
    'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe',
    'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\VC\SecurityIssueAnalysis\python\python.exe',
    'python.exe'
)
$Python = $null
foreach ($Candidate in $PythonCandidates) {
    if (Test-Path -LiteralPath $Candidate) {
        try {
            & $Candidate -c "import sys; assert sys.version_info[:2] == (3, 11)" 2>$null
            if ($LASTEXITCODE -eq 0) { $Python = $Candidate; break }
        } catch { }
    }
}
if (-not $Python) {
    throw 'Python 3.11 is not available. Install it locally, then rerun scripts/test.ps1.'
}
$env:PYTHONPATH = Join-Path $ProjectRoot 'src'
Push-Location $ProjectRoot
try {
    & $Python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}