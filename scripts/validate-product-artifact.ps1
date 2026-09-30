param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [ValidateSet('Auto', 'PRD', 'Prototype')]
    [string]$Type = 'Auto'
)

$ErrorActionPreference = 'Stop'
$resolvedPath = (Resolve-Path -LiteralPath $Path).Path
$content = [IO.File]::ReadAllText($resolvedPath)
$errors = [System.Collections.Generic.List[string]]::new()

if ($Type -eq 'Auto') {
    $Type = if ($content -match '需求追踪矩阵|PRD文档生成') { 'PRD' } else { 'Prototype' }
}

if ($content -match 'X(?:ms|s|人天)|模块[A-Z]|____|\[same description|\[复用[^\]]*\]|\[待填写\]') {
    $errors.Add('发现未解释的模板占位符（X、____、模块A或提示词占位符）。')
}

if ($Type -eq 'PRD') {
    foreach ($required in @('证据与假设台账', '需求追踪矩阵', '自检清单', '风险与开放问题')) {
        if ($content -notmatch [regex]::Escape($required)) {
            $errors.Add("缺少 PRD 必需章节或标记：$required")
        }
    }
}
else {
    foreach ($required in @('Style Anchor ID', '页面状态矩阵', '功能 → 页面 → 状态覆盖矩阵')) {
        if ($content -notmatch [regex]::Escape($required)) {
            $errors.Add("缺少原型设计必需章节或标记：$required")
        }
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { "ERROR: $_" }
    exit 1
}

"PASS: $Type artifact validated: $resolvedPath"
