param(
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$reviewRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $Python) {
    $bundled = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    $candidates = @($bundled, "py", "python")
    foreach ($candidate in $candidates) {
        try {
            & $candidate --version *> $null
            if ($LASTEXITCODE -eq 0) {
                $Python = $candidate
                break
            }
        } catch {
            continue
        }
    }
}

if (-not $Python) {
    throw "No working Python interpreter found. Pass one with -Python C:\path\to\python.exe"
}

$inspection = Join-Path $reviewRoot "material_products\CONSEQUENCE_AWARE_INSPECTION_PLANNER"
$trigger = Join-Path $reviewRoot "material_products\TRIGGER_POLICY_DESIGNER"

Push-Location $inspection
try {
    & $Python -m unittest -v test_planner.py
    if ($LASTEXITCODE -ne 0) { throw "Inspection planner tests failed" }
    & $Python planner.py example_maintenance.json --output example_output.json --report example_report.md
    if ($LASTEXITCODE -ne 0) { throw "Inspection planner example failed" }
} finally {
    Pop-Location
}

Push-Location $trigger
try {
    & $Python -m unittest -v test_trigger_designer.py
    if ($LASTEXITCODE -ne 0) { throw "Trigger designer tests failed" }
    & $Python trigger_designer.py example_config.json example_machine_history.csv --output example_output.json --report example_report.md
    if ($LASTEXITCODE -ne 0) { throw "Trigger designer example failed" }
} finally {
    Pop-Location
}

Write-Host "All 14 material-product tests and both examples completed."
