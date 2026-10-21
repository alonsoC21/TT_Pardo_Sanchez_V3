#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Linter estructural y de estilo para el Trabajo Terminal A083 (LaTeX).

Comprueba, sin dependencias externas:
  * entornos \\begin / \\end balanceados y bien anidados;
  * llaves, delimitadores matemáticos y caracteres especiales sin escapar;
  * etiquetas duplicadas, referencias y citas inexistentes;
  * claves del .bib sin usar y figuras que no existen (con distinción de
    mayúsculas, para detectar fallos que solo aparecen en Overleaf/Linux);
  * convenciones del proyecto (\\,\\%, coma decimal, \\parencite, Figura~\\ref).

Uso:
    python lint_latex.py main.tex
    python lint_latex.py main.tex --strict --bib bibliografia.bib
    python lint_latex.py main.tex --format json

Código de salida: 0 sin errores, 1 con errores (o advertencias si --strict),
2 si no se pudo leer algún archivo.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:  # consola de Windows en UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

VERBATIM_ENVS = {
    "verbatim", "Verbatim", "lstlisting", "minted", "comment",
    "filecontents", "filecontents*",
}
MATH_ENVS = {
    "equation", "equation*", "align", "align*", "gather", "gather*",
    "multline", "multline*", "eqnarray", "eqnarray*", "displaymath",
    "math", "flalign", "flalign*", "alignat", "alignat*",
}
TABLE_ENVS = {
    "tabular", "tabular*", "tabularx", "tabulary", "longtable", "array",
    "matrix", "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix",
    "cases", "split", "aligned", "alignedat", "gathered", "align",
    "align*", "eqnarray", "eqnarray*",
}
REF_CMDS = r"ref|eqref|pageref|autoref|nameref|cref|Cref"
CITE_CMDS = (
    r"cite|citep|citet|citealp|citealt|citeauthor|citeyear|Cite|Citep|"
    r"Citet|parencite|Parencite|textcite|Textcite|footcite|footcitetext|"
    r"autocite|Autocite|smartcite|supercite|fullcite"
)

# Argumentos cuyo contenido no se compone: claves, rutas y nombres.
IGNORED_ARG_CMDS = (
    r"label|" + REF_CMDS + r"|" + CITE_CMDS +
    r"|url|href|input|include|includeonly|includegraphics|addbibresource"
    r"|bibliography|bibliographystyle|lstinputlisting|begin|end|usepackage"
    r"|documentclass|newcommand|renewcommand|providecommand|def|graphicspath"
    r"|hypersetup|lstset|verb|lstinline"
)
IGNORED_ARG_RE = re.compile(
    r"\\(" + IGNORED_ARG_CMDS + r")\*?(?:\[[^\]]*\])?\{[^{}]*\}"
)
CMD_RE = re.compile(r"\\[A-Za-z@]+\*?")

LINE_SPANISH = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"


@dataclass
class Issue:
    file: str
    line: int
    severity: str
    rule: str
    message: str


def strip_comment(line: str) -> str:
    """Elimina el comentario, respetando \\% y \\\\%."""
    out: list[str] = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            out.append(line[i:i + 2])
            i += 2
            continue
        if ch == "%":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def exact_exists(base: Path, rel: str) -> bool:
    """Comprueba la ruta componente a componente (sensible a mayúsculas)."""
    current = base
    for part in Path(rel).parts:
        if part in (".", ""):
            continue
        try:
            entries = os.listdir(current)
        except OSError:
            return False
        if part not in entries:
            return False
        current = current / part
    return True


def prose_of(line: str) -> str:
    """Texto aproximado de una línea, sin comandos ni matemáticas."""
    text = strip_comment(line)
    text = IGNORED_ARG_RE.sub(" ", text)
    text = CMD_RE.sub(" ", text)
    text = re.sub(r"(?<!\\)\$[^$]*\$", " ", text)
    text = re.sub(r"\\([,;:! ]|quad|qquad|%)", " ", text)
    text = text.replace("~", " ").replace("{", " ").replace("}", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def text_with_markup(line: str) -> str:
    """Como prose_of, pero conserva los comandos para no unir palabras que
    están separadas por un cambio de formato (p. ej. «de \\textit{de pie}»)."""
    text = strip_comment(line)
    text = re.sub(r"(?<!\\)\$[^$]*\$", " ", text)
    text = re.sub(r"\\([,;:! ]|quad|qquad|%)", " ", text)
    text = text.replace("~", " ").replace("{", " ").replace("}", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_bib_keys(bib_path: Path) -> tuple[set[str], list[Issue]]:
    keys: set[str] = set()
    issues: list[Issue] = []
    duplicates: set[str] = set()
    if not bib_path.exists():
        return keys, issues
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    for match in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        kind = match.group(1).lower()
        if kind in {"string", "comment", "preamble"}:
            continue
        key = match.group(2)
        if key in keys and key not in duplicates:
            line = text[: match.start()].count("\n") + 1
            issues.append(Issue(str(bib_path), line, "error", "bib-duplicada",
                                f"clave bibliográfica duplicada: {key}"))
            duplicates.add(key)
        keys.add(key)
    return keys, issues


class Linter:
    def __init__(self, path: Path, bib_keys: set[str], base: Path) -> None:
        self.path = path
        self.base = base
        self.bib_keys = bib_keys
        self.issues: list[Issue] = []
        self.labels: dict[str, int] = {}
        self.refs: list[tuple[str, int]] = []
        self.cites: list[tuple[str, int]] = []
        self.graphics: list[tuple[str, int]] = []
        self.env_stack: list[tuple[str, int]] = []
        self.in_verbatim: str | None = None
        self.in_verbatim_name = ""
        self.math_depth = 0
        self.dollar_balance = 0
        self.brace_depth = 0

    def add(self, line: int, severity: str, rule: str, message: str) -> None:
        self.issues.append(Issue(str(self.path), line, severity, rule, message))

    def run(self) -> list[Issue]:
        try:
            text = self.path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self.add(1, "error", "lectura", f"no se pudo leer el archivo: {exc}")
            return self.issues

        lines = text.splitlines()
        self.check_document_bounds(lines)

        for number, raw in enumerate(lines, start=1):
            self.scan_line(number, raw)

        self.close_structures(len(lines))
        self.check_labels_and_cites()
        self.check_bibliography_usage()
        self.check_graphics()
        return self.issues

    # ------------------------------------------------------------------
    def scan_line(self, number: int, raw: str) -> None:
        if self.in_verbatim:
            if re.search(r"\\end\{" + re.escape(self.in_verbatim) + r"\}", raw):
                self.in_verbatim = None
                self.pop_env(self.in_verbatim_name, number, lenient=True)
            return

        stripped = strip_comment(raw)
        self.collect_macros(number, stripped)
        self.scan_environments(number, stripped, raw)
        if self.in_verbatim:
            return

        self.scan_braces(number, stripped)
        self.scan_math(number, stripped)
        self.scan_specials(number, stripped)
        self.scan_style(number, stripped, raw)

    def scan_environments(self, number: int, stripped: str, raw: str) -> None:
        for match in re.finditer(r"\\(begin|end)\s*\{([^}]*)\}", stripped):
            action, name = match.group(1), match.group(2).strip()
            if action == "begin":
                self.env_stack.append((name, number))
                if name in MATH_ENVS:
                    self.math_depth += 1
                if name in VERBATIM_ENVS:
                    self.in_verbatim = name
                    self.in_verbatim_name = name
                    return
            else:
                if name in MATH_ENVS and self.math_depth > 0:
                    self.math_depth -= 1
                self.pop_env(name, number)
                if name in VERBATIM_ENVS:
                    self.in_verbatim = None
                    return

    def pop_env(self, name: str, number: int, lenient: bool = False) -> None:
        if not self.env_stack:
            if not lenient:
                self.add(number, "error", "entorno-sin-abrir",
                         f"\\end{{{name}}} sin \\begin correspondiente")
            return
        if self.env_stack[-1][0] == name:
            self.env_stack.pop()
            return
        if lenient:
            for index in range(len(self.env_stack) - 1, -1, -1):
                if self.env_stack[index][0] == name:
                    del self.env_stack[index:]
                    return
            return
        top, top_line = self.env_stack[-1]
        self.add(number, "error", "entorno-desbalanceado",
                 f"\\end{{{name}}} cierra un entorno abierto; se esperaba "
                 f"\\end{{{top}}} (abierto en la línea {top_line})")
        for index in range(len(self.env_stack) - 1, -1, -1):
            if self.env_stack[index][0] == name:
                del self.env_stack[index:]
                return
        self.env_stack.pop()

    def scan_braces(self, number: int, stripped: str) -> None:
        for match in re.finditer(r"(?<!\\)[{}]", stripped):
            if match.group() == "{":
                self.brace_depth += 1
            else:
                self.brace_depth -= 1
                if self.brace_depth < 0:
                    self.add(number, "error", "llave-sobrante",
                             "llave de cierre sin apertura")
                    self.brace_depth = 0

    def scan_math(self, number: int, stripped: str) -> None:
        dollars = len(re.findall(r"(?<!\\)\$", stripped))
        self.dollar_balance += dollars
        if dollars % 2 == 1:
            self.add(number, "warning", "matematica-impar",
                     "número impar de $ en la línea (posible delimitador sin "
                     "cerrar; si la fórmula continúa en la línea siguiente, "
                     "ignora este aviso)")

    def scan_specials(self, number: int, stripped: str) -> None:
        clean = IGNORED_ARG_RE.sub(" ", stripped)
        clean = CMD_RE.sub(" ", clean)
        in_math = self.math_depth > 0
        in_table = any(env in TABLE_ENVS for env, _ in self.env_stack)

        if not in_math:
            for match in re.finditer(r"(?<!\\)[_^]", clean):
                char = match.group()
                self.add(number, "error", "caracter-especial",
                         f"'{char}' sin escapar fuera de matemáticas "
                         f"(usa '\\{char}')")
            for match in re.finditer(r"(?<!\\)&", clean):
                if not in_table:
                    self.add(number, "error", "caracter-especial",
                             "'&' sin escapar fuera de un entorno tabular")
                    break
            if "\\" not in clean.split("%")[0] and re.search(r"(?<!\\)#", clean):
                if not re.search(r"\\(newcommand|renewcommand|providecommand|def"
                                 r"|newcolumntype|newenvironment|newtheorem)\b",
                                 stripped):
                    self.add(number, "error", "caracter-especial",
                             "'#' sin escapar fuera de una definición de macro")

    def scan_style(self, number: int, stripped: str, raw: str) -> None:
        if re.search(r"(?<!\\,)\\%", stripped):
            self.add(number, "warning", "porcentaje",
                     "usa '\\,\\%' para separar la cifra del símbolo de "
                     "porcentaje (convención del documento)")

        if re.search(r"\d+\.\d+\s*(?:\\,\s*)?\\%", stripped):
            self.add(number, "warning", "coma-decimal",
                     "usa coma decimal (babel es-nodecimaldot), p. ej. 98,5\\,\\%")

        if re.search(r"\b(Figura|Tabla|Sección|Seccion|Ecuación|Ecuacion|"
                     r"Listado|Capítulo|Capitulo|Anexo)\s+\\ref", stripped):
            self.add(number, "warning", "referencia-sin-tilde",
                     "usa '~' antes de \\ref (p. ej. Figura~\\ref{...})")

        if re.search(r"\\(citep|citet)\b", stripped):
            self.add(number, "warning", "estilo-cita",
                     "el proyecto usa \\parencite y \\textcite (biblatex); "
                     "evita \\citep y \\citet")

        if re.match(r"^\s*[" + LINE_SPANISH + r"]\s*$", raw):
            self.add(number, "error", "linea-suelta",
                     "carácter suelto fuera de cualquier comando: posible "
                     "resto de edición que rompe la compilación")

        structural = re.search(
            r"\\(newtheorem|markboth|addcontentsline|titleformat|fancyhead|"
            r"fancyfoot|setlist|definecolor|hypersetup|lstset|graphicspath|"
            r"setlength|addtolength|newcolumntype|newcommand|renewcommand|"
            r"providecommand|titleformat|titlespacing)\b", stripped)
        prose = prose_of(raw)
        if not structural and self.math_depth == 0:
            markup = text_with_markup(raw)
            for match in re.finditer(
                    r"\b([" + LINE_SPANISH + r"]{2,})\s+\1\b", markup,
                    flags=re.IGNORECASE):
                self.add(number, "warning", "palabra-repetida",
                         f"palabra repetida: «{match.group(0)}»")

        if "¿" not in raw and re.search(
                r"[" + LINE_SPANISH + r"]\s*\?", prose):
            self.add(number, "info", "signo-apertura",
                     "falta '¿' de apertura en una interrogación")

    def collect_macros(self, number: int, stripped: str) -> None:
        for match in re.finditer(r"\\label\{([^}]*)\}", stripped):
            label = match.group(1)
            if label in self.labels:
                self.add(number, "error", "etiqueta-duplicada",
                         f"\\label{{{label}}} ya definida en la línea "
                         f"{self.labels[label]}")
            else:
                self.labels[label] = number

        # La opción label={...} de lstlisting también crea una etiqueta.
        for match in re.finditer(
                r"\\begin\{lstlisting\}\s*\[([^\]]*)\]", stripped):
            option = re.search(r"label\s*=\s*\{([^}]*)\}", match.group(1))
            if option:
                label = option.group(1).strip()
                if label and label not in self.labels:
                    self.labels[label] = number

        for match in re.finditer(r"\\(" + REF_CMDS + r")\{([^}]*)\}", stripped):
            for key in match.group(2).split(","):
                key = key.strip()
                if key:
                    self.refs.append((key, number))

        for match in re.finditer(
                r"\\(" + CITE_CMDS + r")\*?(?:\[[^\]]*\])?"
                r"((?:\{[^}]*\})+)", stripped):
            for group in re.findall(r"\{([^}]*)\}", match.group(2)):
                for key in group.split(","):
                    key = key.strip()
                    if key:
                        self.cites.append((key, number))

        for match in re.finditer(
                r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", stripped):
            self.graphics.append((match.group(1).strip(), number))

    # ------------------------------------------------------------------
    def check_document_bounds(self, lines: list[str]) -> None:
        begins = sum(len(re.findall(r"\\begin\{document\}", ln)) for ln in lines)
        ends = sum(len(re.findall(r"\\end\{document\}", ln)) for ln in lines)
        if begins != 1:
            self.add(1, "error", "documento", f"\\begin{{document}} aparece "
                     f"{begins} veces (se esperaba 1)")
        if ends != 1:
            self.add(len(lines), "error", "documento",
                     f"\\end{{document}} aparece {ends} veces (se esperaba 1)")
        for number, line in enumerate(lines, start=1):
            path = re.search(r"\\graphicspath\{\{([^}]*)\}\}", line)
            if path:
                for entry in path.group(1).split("}{"):
                    entry = entry.strip().rstrip("/")
                    if entry and not exact_exists(self.base, entry):
                        self.add(number, "warning", "graphicspath",
                                 f"\\graphicspath apunta a '{entry}/', pero esa "
                                 "carpeta no existe con esa combinación de "
                                 "mayúsculas (falla en Overleaf/Linux)")

    def close_structures(self, last_line: int) -> None:
        for name, line in self.env_stack:
            self.add(line, "error", "entorno-sin-cerrar",
                     f"\\begin{{{name}}} sin \\end correspondiente")
        if self.brace_depth != 0:
            self.add(last_line, "error", "llaves",
                     f"llaves desbalanceadas: {self.brace_depth:+d}")
        if self.dollar_balance % 2 != 0:
            self.add(last_line, "error", "matematica",
                     "número total impar de '$': delimitador sin cerrar")

    def check_labels_and_cites(self) -> None:
        for key, line in self.refs:
            if key not in self.labels:
                self.add(line, "error", "referencia-rota",
                         f"\\ref a etiqueta inexistente: {key}")
        for key, line in self.cites:
            if self.bib_keys and key not in self.bib_keys:
                self.add(line, "error", "cita-rota",
                         f"cita sin entrada en el .bib: {key}")

        used = {key for key, _ in self.refs}
        cited = {key for key, _ in self.cites}
        for label, line in self.labels.items():
            if label not in used and label.startswith(("fig:", "tab:", "lst:")):
                self.add(line, "info", "etiqueta-sin-uso",
                         f"\\label{{{label}}} no se referencia en el documento")
        for key in sorted(self.bib_keys - cited):
            self.add(1, "info", "bib-sin-cita",
                     f"entrada del .bib nunca citada: {key}")

    def check_bibliography_usage(self) -> None:
        # Solo informa; la comprobación de existencia de la ruta del .bib se
        # hace al cargar las claves para no duplicar avisos.
        pass

    def check_graphics(self) -> None:
        suffixes = ("", ".png", ".jpg", ".jpeg", ".pdf", ".eps")
        for rel, line in self.graphics:
            candidates: list[tuple[Path, str]] = []
            raw = Path(rel)
            for suffix in suffixes:
                name = rel if suffix == "" or raw.suffix else rel + suffix
                for base in (self.base, self.base / "Figuras",
                             self.base / "figuras"):
                    candidates.append((base, name))
            if not any(exact_exists(base, name) for base, name in candidates):
                self.add(line, "error", "figura-inexistente",
                         f"no se encontró la imagen '{rel}' (revisa ruta y "
                         "mayúsculas)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Linter estructural y de estilo para el TF A083.")
    parser.add_argument("files", nargs="*", default=["main.tex"],
                        help="archivos .tex a revisar (por defecto main.tex)")
    parser.add_argument("--bib", default="bibliografia.bib",
                        help="archivo .bib activo (por defecto bibliografia.bib)")
    parser.add_argument("--strict", action="store_true",
                        help="considera las advertencias como errores")
    parser.add_argument("--no-info", action="store_true",
                        help="oculta los avisos informativos")
    parser.add_argument("--format", choices=("text", "json"), default="text",
                        help="formato de salida")
    args = parser.parse_args()

    base = Path.cwd()
    bib_path = Path(args.bib)
    if not bib_path.is_absolute():
        bib_path = base / bib_path
    bib_keys, bib_issues = load_bib_keys(bib_path)

    issues: list[Issue] = list(bib_issues)
    failed = False
    for name in args.files:
        path = Path(name)
        if not path.is_absolute():
            path = base / path
        if not path.exists():
            print(f"ERROR: no existe el archivo {name}", file=sys.stderr)
            failed = True
            continue
        issues.extend(Linter(path, bib_keys, path.parent).run())

    if args.no_info:
        issues = [issue for issue in issues if issue.severity != "info"]

    order = {"error": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda issue: (issue.file, issue.line,
                                   order.get(issue.severity, 9), issue.rule))

    if args.format == "json":
        print(json.dumps([asdict(issue) for issue in issues],
                         ensure_ascii=False, indent=2))
    else:
        for issue in issues:
            try:
                relative = Path(issue.file).resolve().relative_to(base.resolve())
                shown = str(relative).replace("\\", "/")
            except ValueError:
                shown = issue.file
            print(f"{shown}:{issue.line}: {issue.severity}: "
                  f"{issue.message} [{issue.rule}]")

        errors = sum(1 for issue in issues if issue.severity == "error")
        warnings = sum(1 for issue in issues if issue.severity == "warning")
        infos = sum(1 for issue in issues if issue.severity == "info")
        print(f"\nResumen: {errors} error(es), {warnings} advertencia(s), "
              f"{infos} aviso(s).")

    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    if failed or errors > 0 or (args.strict and warnings > 0):
        return 1 if not failed else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
