# CLAUDE.md — Trabajo Terminal A083

@AGENTS.md

## Claude Code

Este archivo ya contiene la configuración del proyecto. Si se ejecuta `/init`,
conserva el importe `@AGENTS.md` y esta sección; no reemplaces el archivo con
una propuesta genérica.

- **Skills compartidas:** viven en `.claude/skills/` y también las usa OpenCode.
  Invócalas como `/linter-latex` y `/spellchecker-es`. No crees skills
  equivalentes ni copies carpetas a `.opencode/skills/`.
- **Respaldo obligatorio:** antes de editar `main.tex` o `bibliografia.bib`,
  ejecuta `powershell -ExecutionPolicy Bypass -File scripts/respaldo.ps1`.
- **Verificación mínima:**
  - `python .claude/skills/linter-latex/scripts/lint_latex.py main.tex`
  - `python .claude/skills/spellchecker-es/scripts/spellcheck_es.py main.tex`
- **Commits:** no ejecutes `git commit` ni `git push` sin confirmación explícita
  del autor.
- **MCP:** Claude Code usa sus herramientas nativas de archivos; no necesita el
  servidor MCP `filesystem` configurado para OpenCode.
- **Requisito:** Python 3.10 o superior para los scripts de las skills.

Las reglas completas de redacción, LaTeX, respaldo y verificación están en
`AGENTS.md`, importado al inicio de este archivo.
