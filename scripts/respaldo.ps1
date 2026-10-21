# Respaldo local previo a cualquier edición del Trabajo Terminal A083.
#
# Copia los archivos indicados a una carpeta con marca de tiempo fuera del
# repositorio, de modo que Git no registre ruido y siempre exista un punto de
# retorno inmediato. No modifica ni elimina los originales.
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File scripts/respaldo.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/respaldo.ps1 -Archivos main.tex,bibliografia.bib
#
# Salida: ruta de la carpeta creada (se imprime al final).

[CmdletBinding()]
param(
    [string[]]$Archivos = @("main.tex", "bibliografia.bib", "Bibliograf*.tex"),
    [string]$Destino = (Join-Path $env:TEMP "opencode\tt_backups")
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$marca = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$carpeta = Join-Path $Destino $marca

New-Item -ItemType Directory -Path $carpeta -Force | Out-Null

$copiados = 0
foreach ($patron in $Archivos) {
    $ruta = if ([System.IO.Path]::IsPathRooted($patron)) {
        $patron
    } else {
        Join-Path $raiz $patron
    }

    $encontrados = @(Get-ChildItem -Path $ruta -File -ErrorAction SilentlyContinue)
    if ($encontrados.Count -eq 0) {
        Write-Warning "No existe y se omite: $patron"
        continue
    }

    foreach ($item in $encontrados) {
        Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $carpeta $item.Name) -Force
        $hash = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
        $copiados++
        Write-Host ("  - {0}  ({1} bytes, SHA256 {2})" -f $item.Name, $item.Length, $hash.Substring(0, 12))
    }
}

if ($copiados -eq 0) {
    Remove-Item -LiteralPath $carpeta -Force
    throw "No se copió ningún archivo: revisa las rutas."
}

Set-Content -LiteralPath (Join-Path $carpeta "LEEME.txt") -Encoding UTF8 -Value @(
    "Respaldo del Trabajo Terminal A083",
    "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "Archivos: $($Archivos -join ', ')",
    "",
    "Para restaurar, copia el archivo deseado sobre el original del repositorio."
)

Write-Host ""
Write-Host "Respaldo creado en: $carpeta"
Write-Host "Restaurar (ejemplo): Copy-Item -LiteralPath '$carpeta\main.tex' -Destination '$raiz\main.tex' -Force"
