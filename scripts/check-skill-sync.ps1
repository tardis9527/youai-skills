$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourceRoot = Join-Path $repoRoot 'skills'
$pluginRoot = Join-Path $repoRoot 'plugins\youai-skills\skills'
$errors = [System.Collections.Generic.List[string]]::new()

function Get-NormalizedText {
    param([string]$Path)

    $text = [IO.File]::ReadAllText($Path)
    if ([IO.Path]::GetFileName($Path) -eq 'SKILL.md') {
        $text = [regex]::Replace($text, '(?m)^disable-model-invocation: true\r?\n', '')
    }
    return $text
}

$sourceFiles = Get-ChildItem -LiteralPath $sourceRoot -Recurse -File
foreach ($sourceFile in $sourceFiles) {
    $relative = $sourceFile.FullName.Substring($sourceRoot.Length).TrimStart('\', '/')
    $pluginFile = Join-Path $pluginRoot $relative
    if (-not (Test-Path -LiteralPath $pluginFile -PathType Leaf)) {
        $errors.Add("插件缺少文件：$relative")
        continue
    }
    if ((Get-NormalizedText $sourceFile.FullName) -cne (Get-NormalizedText $pluginFile)) {
        $errors.Add("文件内容不一致：$relative")
    }
}

$pluginFiles = Get-ChildItem -LiteralPath $pluginRoot -Recurse -File
foreach ($pluginFile in $pluginFiles) {
    $relative = $pluginFile.FullName.Substring($pluginRoot.Length).TrimStart('\', '/')
    if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $relative) -PathType Leaf)) {
        $errors.Add("源目录缺少文件：$relative")
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { "ERROR: $_" }
    exit 1
}

"PASS: source skills and Codex plugin skills are synchronized"
