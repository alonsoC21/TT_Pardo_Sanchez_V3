---
name: linter-latex
description: Revisa la estructura y el estilo del código LaTeX del Trabajo Terminal A083 (entornos, llaves, referencias, citas, figuras y convenciones) antes de compilar o de proponer cambios.
---

# Linter LaTeX del TF A083

## Cuándo usar esta skill

Úsala siempre que se vaya a:

- modificar `main.tex`, `bibliografia.bib` o cualquier archivo `.tex`;
- revisar un cambio antes de mostrarlo al usuario;
- comprobar que una referencia, cita, figura o etiqueta sigue existiendo.

No sustituye a la compilación: detecta problemas de estructura y de
convenciones, no errores de tipografía que solo aparecen al generar el PDF.

## Requisitos

- Python 3.10 o superior (en este equipo: `python`).
- No requiere `chktex` ni conexión a Internet.
- Si algún día se instala `chktex`, puede complementarse con
  `chktex -q main.tex`, pero el script del proyecto ya cubre las reglas
  acordadas.

## Comandos

Desde la raíz del repositorio:

```powershell
# Revisión normal del documento principal
python .claude/skills/linter-latex/scripts/lint_latex.py main.tex

# Tratar las advertencias como errores (para una revisión estricta)
python .claude/skills/linter-latex/scripts/lint_latex.py main.tex --strict

# Ocultar avisos informativos y usar otro .bib
python .claude/skills/linter-latex/scripts/lint_latex.py main.tex --no-info --bib bibliografia.bib

# Salida legible por máquina
python .claude/skills/linter-latex/scripts/lint_latex.py main.tex --format json
```

Códigos de salida: `0` sin errores, `1` con errores (o advertencias con
`--strict`), `2` si no se pudo leer un archivo.

## Qué revisa

| Grupo | Ejemplos |
| --- | --- |
| Estructura | `\begin`/`\end` desbalanceados, llaves y `$` sin cerrar |
| Caracteres | `_`, `^`, `&` y `#` sin escapar fuera de matemáticas o tablas |
| Referencias | `\ref` a etiquetas inexistentes, etiquetas duplicadas o sin uso |
| Bibliografía | citas sin entrada en el `.bib`, claves duplicadas y entradas sin citar |
| Figuras | rutas inexistentes, distinguiendo mayúsculas (fallos que solo aparecen en Overleaf) |
| Convenciones | `90\,\%` en lugar de `90\%`, coma decimal, `Figura~\ref`, `\parencite` en lugar de `\citep` |
| Edición | líneas con un solo carácter suelto, palabras repetidas y falta de `¿` |

## Cómo interpretar los hallazgos

- **error**: rompe la compilación o deja una referencia rota. Corrígelo antes
  de continuar.
- **warning**: incumple una convención del documento. Corrígelo si el cambio
  es inequívoco; si altera el sentido, consulta al autor.
- **info**: sugerencia (etiqueta sin uso, entrada del `.bib` sin citar). No
  requiere acción inmediata.

Los avisos `matematica-impar` pueden ser falsos positivos cuando una fórmula
`$...$` continúa en la línea siguiente; verifica el contexto antes de editar.

## Flujo obligatorio

1. Ejecuta `scripts/respaldo.ps1` (ver `AGENTS.md`).
2. Corre el linter sobre el archivo que vas a tocar.
3. Corrige únicamente los errores; para las advertencias, aplica solo cambios
   que no alteren el significado.
4. Vuelve a ejecutar el linter hasta que no queden errores.
5. Si hay una distribución de LaTeX instalada, compila con
   `latexmk -pdf -interaction=nonstopmode main.tex`; si no, indícalo.
6. Muestra el diff y pide confirmación antes de cualquier `git commit`.

## Reglas de edición

- No reflowes párrafos ni cambies el estilo de una línea por otra.
- No inventes etiquetas ni claves bibliográficas para silenciar avisos.
- No borres una entrada del `.bib` solo porque el linter diga que no se cita:
  puede ser material de consulta del autor.
- Mantén las mayúsculas reales de las rutas (`Figuras/`, no `figuras/`).
- El linter nunca modifica archivos por sí mismo.
