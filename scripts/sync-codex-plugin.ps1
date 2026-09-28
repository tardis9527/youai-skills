$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = Join-Path $repoRoot 'skills'
$pluginRoot = Join-Path $repoRoot 'plugins\youai-skills'
$destination = Join-Path $pluginRoot 'skills'

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Skill source directory not found: $source"
}
if (-not (Test-Path -LiteralPath (Join-Path $pluginRoot '.codex-plugin\plugin.json') -PathType Leaf)) {
    throw "Codex plugin manifest not found: $pluginRoot"
}

$pluginPath = [IO.Path]::GetFullPath($pluginRoot).TrimEnd('\', '/')
$destinationPath = [IO.Path]::GetFullPath($destination)
if (-not $destinationPath.StartsWith($pluginPath + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to sync outside the plugin directory: $destinationPath"
}

New-Item -ItemType Directory -Force -Path $destinationPath | Out-Null
robocopy $source $destinationPath /MIR /NFL /NDL /NJH /NJS /NC /NS | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "Skill sync failed (robocopy exit code $LASTEXITCODE)."
}

# Codex plugins require this frontmatter flag to be absent or false.
Get-ChildItem -LiteralPath $destinationPath -Directory | ForEach-Object {
    $skillPath = Join-Path $_.FullName 'SKILL.md'
    if (Test-Path -LiteralPath $skillPath -PathType Leaf) {
        $contents = [IO.File]::ReadAllText($skillPath)
        $updated = [regex]::Replace($contents, '(?m)^disable-model-invocation: true\r?\n', '')
        if ($updated -ne $contents) {
            [IO.File]::WriteAllText($skillPath, $updated, [Text.UTF8Encoding]::new($false))
        }
    }
}

Write-Output "Synced skills to $destinationPath"
