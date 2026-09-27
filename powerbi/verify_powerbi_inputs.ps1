param(
    [Parameter(Mandatory = $true)]
    [string] $RepoPath
)

$ErrorActionPreference = 'Stop'
$dataPath = Join-Path $RepoPath 'powerbi/data'
$manifest = Get-Content -LiteralPath (Join-Path $dataPath 'manifest.json') -Raw | ConvertFrom-Json
$names = @('dim_date', 'dim_region', 'daily_price_metrics', 'daily_demand_metrics', 'hourly_price_patterns', 'scenario_daily')
$tables = @{}

function Assert-Equal($actual, $expected, [string] $label) {
    if ($actual -ne $expected) { throw "$label`: expected $expected; got $actual" }
    Write-Host "PASS $label`: $actual"
}

function Assert-Unique($rows, [string[]] $columns, [string] $label) {
    $keys = @{}
    foreach ($row in $rows) {
        $key = ($columns | ForEach-Object { [string]$row.$_ }) -join '|'
        if ($keys.ContainsKey($key)) { throw "Duplicate $label key: $key" }
        $keys[$key] = $true
    }
    Write-Host "PASS $label unique keys: $($rows.Count)"
}

function Decimal-Value([string] $value) {
    return [decimal]::Parse($value, [System.Globalization.CultureInfo]::InvariantCulture)
}

foreach ($name in $names) {
    $file = "$name.csv"
    $path = Join-Path $dataPath $file
    $entry = $manifest.files.PSObject.Properties[$file].Value
    if ($null -eq $entry) { throw "Manifest entry missing: $file" }
    $raw = [System.IO.File]::ReadAllBytes($path)
    $content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
    $normalised = $content.Replace("`r`n", "`n").Replace("`r", "`n")
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($normalised)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $hash = ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
    Assert-Equal $bytes.Length ([int]$entry.bytes) "$file LF-normalised bytes"
    Assert-Equal $hash ([string]$entry.sha256) "$file LF-normalised SHA-256"
    if ($raw.Length -ne $bytes.Length) { Write-Host "INFO $file`: checkout line endings differ from manifest (CRLF is expected on some Windows setups)" }
    $tables[$name] = @(Import-Csv -LiteralPath $path)
}

Assert-Equal $tables.dim_date.Count 364 'dim_date rows'
Assert-Equal $tables.dim_region.Count 1 'dim_region rows'
Assert-Equal $tables.daily_price_metrics.Count 364 'daily_price_metrics rows'
Assert-Equal $tables.daily_demand_metrics.Count 364 'daily_demand_metrics rows'
Assert-Equal $tables.hourly_price_patterns.Count 168 'hourly_price_patterns rows'
Assert-Equal $tables.scenario_daily.Count 75 'scenario_daily rows'
Assert-Unique $tables.dim_date @('local_date') 'dim_date'
Assert-Unique $tables.dim_region @('region_id') 'dim_region'
Assert-Unique $tables.daily_price_metrics @('region_id', 'local_date') 'daily_price_metrics'
Assert-Unique $tables.daily_demand_metrics @('region_id', 'local_date') 'daily_demand_metrics'
Assert-Unique $tables.hourly_price_patterns @('region_id', 'day_of_week', 'local_hour') 'hourly_price_patterns'
Assert-Unique $tables.scenario_daily @('date') 'scenario_daily'

$dates = @{}
foreach ($row in $tables.dim_date) { $dates[$row.local_date] = $true }
$regions = @{}
foreach ($row in $tables.dim_region) { $regions[$row.region_id] = $true }
Assert-Equal ($dates.ContainsKey('2025-09-14')) $true 'first date present'
Assert-Equal ($dates.ContainsKey('2026-09-12')) $true 'last date present'
for ($day = [datetime]'2025-09-14'; $day -le [datetime]'2026-09-12'; $day = $day.AddDays(1)) {
    $key = $day.ToString('yyyy-MM-dd')
    if (-not $dates.ContainsKey($key)) { throw "Calendar date missing: $key" }
}
Write-Host 'PASS dim_date is contiguous'
foreach ($table in @('daily_price_metrics', 'daily_demand_metrics')) {
    foreach ($row in $tables[$table]) {
        if (-not $dates.ContainsKey($row.local_date)) { throw "$table has orphan date $($row.local_date)" }
        if (-not $regions.ContainsKey($row.region_id)) { throw "$table has orphan region $($row.region_id)" }
    }
}
foreach ($row in $tables.scenario_daily) {
    if (-not $dates.ContainsKey($row.date)) { throw "scenario_daily has orphan date $($row.date)" }
}
foreach ($row in $tables.hourly_price_patterns) {
    if (-not $regions.ContainsKey($row.region_id)) { throw "hourly_price_patterns has orphan region $($row.region_id)" }
}
Write-Host 'PASS relationship keys have no orphans'

$priceIntervals = 0
$completePriceDays = 0
$priceByDate = @{}
foreach ($row in $tables.daily_price_metrics) {
    $count = [int]$row.observed_intervals
    $priceIntervals += $count
    if ($count -eq 288) { $completePriceDays++ }
    $priceByDate[$row.local_date] = $count
}
Assert-Equal $priceIntervals 99463 'price intervals'
Assert-Equal $completePriceDays 225 'complete firm price days'
$hourlyIntervals = 0
foreach ($row in $tables.hourly_price_patterns) { $hourlyIntervals += [int]$row.observed_intervals }
Assert-Equal $hourlyIntervals $priceIntervals 'hourly vs daily price intervals'
foreach ($row in $tables.daily_demand_metrics) {
    if ([int]$row.observed_intervals -ne 48) { throw "Incomplete demand date: $($row.local_date)" }
}
Write-Host 'PASS all 364 demand dates have 48 intervals'

$original = [decimal]0
$alternative = [decimal]0
$sourceReduction = [decimal]0
$scenarioDates = @{}
$daysBetter = 0
foreach ($row in $tables.scenario_daily) {
    $scenarioDates[$row.date] = $true
    if ($priceByDate[$row.date] -ne 288) { throw "Incomplete scenario price date: $($row.date)" }
    $original += Decimal-Value $row.original_aud
    $alternative += Decimal-Value $row.alternative_aud
    $sourceReduction += Decimal-Value $row.reduction_aud
    if ((Decimal-Value $row.reduction_aud) -gt 0) { $daysBetter++ }
}
Assert-Equal $original ([decimal]'291.737715') 'original unrounded AUD'
Assert-Equal $alternative ([decimal]'236.432281') 'alternative unrounded AUD'
Assert-Equal $sourceReduction ([decimal]'55.305432') 'source reduction unrounded AUD'
Assert-Equal ($original - $alternative) ([decimal]'55.305434') 'difference from exposure totals AUD'
Assert-Equal $daysBetter 75 'days better'
Write-Host 'PASS all 75 scenario dates have 288 FIRM price intervals'

$holdout = Get-Content -LiteralPath (Join-Path $RepoPath 'reports/holdout_result.json') -Raw | ConvertFrom-Json
Assert-Equal $holdout.complete_days 75 'holdout JSON complete days'
$dailyByDate = @{}
foreach ($row in $holdout.daily) { $dailyByDate[$row.date] = $row }
Assert-Equal $dailyByDate.Count 75 'holdout JSON daily rows'
foreach ($row in $tables.scenario_daily) {
    if (-not $dailyByDate.ContainsKey($row.date)) { throw "Scenario date missing from JSON: $($row.date)" }
    $source = $dailyByDate[$row.date]
    foreach ($field in @('original_aud', 'alternative_aud', 'reduction_aud')) {
        if ((Decimal-Value $row.$field) -ne [decimal]$source.$field) {
            throw "CSV/JSON mismatch: $($row.date) $field"
        }
    }
}
Write-Host 'PASS all scenario CSV rows match holdout JSON'

$holdoutStart = [datetime]'2026-06-14'
$holdoutEnd = [datetime]'2026-09-12'
$excluded = 0
$excludedDates = @{}
for ($day = $holdoutStart; $day -le $holdoutEnd; $day = $day.AddDays(1)) {
    $key = $day.ToString('yyyy-MM-dd')
    if (-not $scenarioDates.ContainsKey($key)) { $excluded++; $excludedDates[$key] = $true }
}
Assert-Equal $excluded 16 'excluded holdout days'
Assert-Equal $holdout.excluded_days.Count 16 'holdout JSON excluded dates'
foreach ($date in $holdout.excluded_days) {
    if (-not $excludedDates.ContainsKey($date)) { throw "Excluded date mismatch: $date" }
}
Write-Host 'PASS excluded dates match holdout JSON'
Write-Host 'PASS Power BI input preflight complete. Desktop model and visuals still require verification.'
