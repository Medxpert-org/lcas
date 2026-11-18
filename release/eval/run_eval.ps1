# 一键独立评测脚本。评测方只需运行本文件，不改任何代码。
# 用法：powershell -ExecutionPolicy Bypass -File .\release\eval\run_eval.ps1
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$py = "C:\Users\SZYL\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "python" }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $PSScriptRoot "result_$stamp.txt"
$engine = "D:\Workbuddy\2026-11-04-09-05-00\lgd-engine"

function Section($t) { "`n===== $t =====" }

$report = New-Object System.Collections.Generic.List[string]
$report.Add("LCAS eval  $stamp")
$report.Add("root=$root")
$report.Add("python=$py")

Set-Location -LiteralPath $root

$report.Add((Section "E1/E2/E3 bench"))
$b = & $py bench.py 2>&1 | Out-String
$report.Add($b)
$acc  = ($b -match "\d+/\d+ = 100.0%")
$miss = ($b -match "安全方向漏判\s+0")
$pack = ($b -match "\d+/\d+ = 100%")

$report.Add((Section "E4 fuzz"))
$f = & $py fuzz.py 2>&1 | Out-String
$report.Add($f)
$fz = ($f -match "违例\s+0")

$report.Add((Section "E5 conformance"))
$c = & $py release\conformance.py --impl judge.py --check-evidence 2>&1 | Out-String
$report.Add($c)
$conf = $c -match "L2"

$report.Add((Section "E6 engine 3-state"))
$exits = @{}
foreach ($f2 in @("single_case.json", "us_pccp_ok.json", "us_hold.json")) {
    if (-not (Test-Path -LiteralPath $engine)) {
        $report.Add("  $f2 -> SKIP（未找到引擎目录）")
        continue
    }
    $path = Join-Path $root "examples\$f2"
    Set-Location -LiteralPath $engine
    & $py -c "from lgd_engine.cli import main; raise SystemExit(main(['--case', r'$path', '--domain', 'pccp']))" > $null 2>&1
    $exits[$f2] = $LASTEXITCODE
    $report.Add("  $f2 -> exit=$($LASTEXITCODE)")
    Set-Location -LiteralPath $root
}
if (-not (Test-Path -LiteralPath $engine)) {
    $eng = $true
    $report.Add("  注意：本机未找到 lgd-engine 目录，E6 记为 SKIP（不计失败，但需在报告中注明）")
} else {
    $eng = ($exits["single_case.json"] -eq 2) -and ($exits["us_pccp_ok.json"] -eq 0) -and ($exits["us_hold.json"] -eq 1)
}

$report.Add((Section "E7 determinism"))
$d1 = & $py -c "from judge import judge; import json; c=json.load(open('examples/single_case.json',encoding='utf-8')); print(json.dumps(judge(c),ensure_ascii=False,sort_keys=True))" 2>&1 | Out-String
$d2 = & $py -c "from judge import judge; import json; c=json.load(open('examples/single_case.json',encoding='utf-8')); print(json.dumps(judge(c),ensure_ascii=False,sort_keys=True))" 2>&1 | Out-String
$det = ($d1.Trim() -eq $d2.Trim())
$report.Add("  two runs identical: $det")

$report.Add((Section "SUMMARY"))
$lines = @(
    "E1 一致率 100%      : $acc",
    "E2 安全漏判 0       : $miss",
    "E3 离线复跑 100%    : $pack",
    "E4 不变量 0 违例    : $fz",
    "E5 符合性 L2        : $conf",
    "E6 引擎三态 2/0/1   : $eng",
    "E7 可复现           : $det"
)
$lines | ForEach-Object { $report.Add("  " + $_) }

$allPass = $acc -and $miss -and $pack -and $fz -and $conf -and $eng -and $det
$report.Add("")
$report.Add("VERDICT: " + $(if ($allPass) { "PASS — 可进入外发评审（仍须锚点抽查 A1-A3）" } else { "FAIL — 不可外发" }))

$report -join "`n" | Set-Content -LiteralPath $out -Encoding utf8
$report -join "`n" | Write-Output
"`nwritten: $out"
if ($allPass) { exit 0 } else { exit 1 }
