# Renderiza los mockups HTML a PNG de 1080 x 2340 px (360 x 780 px a 3x).
# Uso: powershell -ExecutionPolicy Bypass -File Figuras\mockups_fuente\render.ps1
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) {
    $chrome = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
}

$src = $PSScriptRoot
$out = Split-Path $PSScriptRoot -Parent

$map = @(
    @{ f = "01_privacidad.html"; o = "mockup1.png" },
    @{ f = "02_etiqueta.html";   o = "mockup_2.png" },
    @{ f = "03_perfil.html";     o = "mockup_3.png" },
    @{ f = "04_panel.html";      o = "mockup_4.png" },
    @{ f = "05_alerta.html";     o = "mockup_5.png" },
    @{ f = "06_historial.html";  o = "mockup_6.png" }
)

foreach ($m in $map) {
    $html = Join-Path $src $m.f
    $png = Join-Path $out $m.o
    $url = "file:///" + ($html -replace '\\', '/')
    & $chrome --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=3 `
        --window-size=360,780 --user-data-dir="$env:TEMP\opencode\chrome-profile" `
        --screenshot="$png" $url 2>$null | Out-Null
    if (Test-Path $png) { Write-Host ("OK  {0}" -f $m.o) } else { Write-Host ("FALLO {0}" -f $m.o) }
}
