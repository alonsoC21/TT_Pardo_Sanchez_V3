#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corrector ortográfico y gramatical para el Trabajo Terminal A083.

Extrae únicamente la prosa de los archivos .tex (excluye preámbulo, fórmulas,
listados, TikZ y argumentos técnicos como \\cite o \\label) y la revisa con:

  * reglas locales, siempre disponibles: palabras repetidas, acentuación
    frecuente y signos de apertura;
  * LanguageTool en español (https://api.languagetool.org), que aporta
    ortografía, gramática y tipografía. Requiere conexión a Internet.

Los términos técnicos y los nombres propios se leen de
``references/glosario.md`` para no reportarlos como errores.

Uso:
    python spellcheck_es.py main.tex
    python spellcheck_es.py main.tex --offline
    python spellcheck_es.py main.tex --glosario references/glosario.md
    python spellcheck_es.py main.tex --format json

Código de salida: 0 sin hallazgos, 1 con hallazgos, 2 si falla la API y se
usó --require-api.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

try:  # consola de Windows en UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

API_URL = "https://api.languagetool.org/v2/check"
MAX_CHUNK = 7000
SKIP_ENVS = {
    "tikzpicture", "pgfpicture", "lstlisting", "verbatim", "Verbatim",
    "minted", "comment", "filecontents", "filecontents*", "equation",
    "equation*", "align", "align*", "gather", "gather*", "multline",
    "multline*", "eqnarray", "eqnarray*", "displaymath", "math",
    "flalign", "flalign*", "alignat", "alignat*", "array", "matrix",
    "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix", "cases",
}
SKIP_ARG_CMDS = (
    r"includegraphics|includeonly|include|input|label|pageref|eqref|"
    r"autoref|nameref|Cref|cref|ref|parencite|Parencite|textcite|Textcite|"
    r"citep|Citet|Citep|citet|footcitetext|footcite|autocite|Autocite|"
    r"citeauthor|citeyear|citealp|citealt|smartcite|supercite|fullcite|"
    r"cite|url|href|addbibresource|bibliography|bibliographystyle|"
    r"lstinputlisting|usepackage|documentclass|newcommand|renewcommand|"
    r"providecommand|def|graphicspath|hypersetup|lstset|texttt|lstinline|"
    r"verb|begin|end|thispagestyle|pagestyle|pagenumbering|setcounter|"
    r"addtocounter|vspace|hspace|rule|fontsize|setlength|addtolength|"
    r"color|definecolor|printbibliography"
)
CMD_RE = re.compile(r"\\[A-Za-z@]+\*?")
MATH_INLINE_RE = re.compile(r"(?<!\\)\$[^$]*\$")
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:-[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*")

# Errores de acentuación frecuentes en textos académicos. Solo se incluyen
# formas que no son palabras válidas en español (se evitan "esta", "mas",
# "solo", "aun", etc., que dependen del contexto).
ACCENTS = {
    "computo": "cómputo",
    "analisis": "análisis",
    "metodologia": "metodología",
    "tecnologia": "tecnología",
    "tecnologias": "tecnologías",
    "informacion": "información",
    "deteccion": "detección",
    "vision": "visión",
    "aplicacion": "aplicación",
    "clasificacion": "clasificación",
    "evaluacion": "evaluación",
    "investigacion": "investigación",
    "caida": "caída",
    "caidas": "caídas",
    "imagenes": "imágenes",
    "medico": "médico",
    "medicos": "médicos",
    "publico": "público",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "estadistica": "estadística",
    "metricas": "métricas",
    "precision": "precisión",
    "exito": "éxito",
    "exitos": "éxitos",
    "tambien": "también",
    "ademas": "además",
    "despues": "después",
    "asi": "así",
    "traves": "través",
    "habian": "habían",
    "podria": "podría",
    "podrian": "podrían",
    "estan": "están",
    "estandar": "estándar",
    "caracter": "carácter",
    "limite": "límite",
    "limites": "límites",
    "maxima": "máxima",
    "maximo": "máximo",
    "minima": "mínima",
    "minimo": "mínimo",
    "numero": "número",
    "numeros": "números",
    "energia": "energía",
    "categoria": "categoría",
    "categorias": "categorías",
    "funcion": "función",
    "configuracion": "configuración",
    "comunicacion": "comunicación",
    "notificacion": "notificación",
    "autonomia": "autonomía",
    "depresion": "depresión",
    "inmovilizacion": "inmovilización",
    "acelerometro": "acelerómetro",
    "iluminacion": "iluminación",
    "oclusion": "oclusión",
    "camara": "cámara",
    "camaras": "cámaras",
    "suscripcion": "suscripción",
    "publicacion": "publicación",
    "recepcion": "recepción",
    "validacion": "validación",
    "confirmacion": "confirmación",
    "bitacora": "bitácora",
    "movil": "móvil",
    "moviles": "móviles",
    "practica": "práctica",
    "practicas": "prácticas",
    "diagnostico": "diagnóstico",
    "pronostico": "pronóstico",
    "analitica": "analítica",
    "analitico": "analítico",
    "geometrica": "geométrica",
    "geometrico": "geométrico",
    "estatica": "estática",
    "estatico": "estático",
    "dinamica": "dinámica",
    "dinamico": "dinámico",
    "grafica": "gráfica",
    "grafico": "gráfico",
    "graficas": "gráficas",
    "graficos": "gráficos",
    "logica": "lógica",
    "logico": "lógico",
    "matematica": "matemática",
    "matematico": "matemático",
    "economica": "económica",
    "economico": "económico",
    "clinica": "clínica",
    "clinico": "clínico",
    "etica": "ética",
    "etico": "ético",
    "rapida": "rápida",
    "rapido": "rápido",
    "rapidas": "rápidas",
    "rapidos": "rápidos",
    "unica": "única",
    "unico": "único",
    "ultima": "última",
    "ultimo": "último",
    "proximo": "próximo",
    "proxima": "próxima",
    "automatica": "automática",
    "automatico": "automático",
    "cronologica": "cronológica",
    "cronologico": "cronológico",
    "metrica": "métrica",
    "metrico": "métrico",
    "sintomas": "síntomas",
    "sintoma": "síntoma",
    "diagnosticos": "diagnósticos",
    "craneoencefalico": "craneoencefálico",
    "craneoencefalicos": "craneoencefálicos",
    "poscaida": "poscaída",
    "rehabilitacion": "rehabilitación",
    "telefono": "teléfono",
    "telefonos": "teléfonos",
    "instalacion": "instalación",
    "parametros": "parámetros",
    "parametro": "parámetro",
}


@dataclass
class Finding:
    file: str
    line: int
    severity: str
    category: str
    message: str
    suggestion: str = ""
    rule: str = ""


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def strip_comment(line: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line):
            out.append(line[i:i + 2])
            i += 2
            continue
        if line[i] == "%":
            break
        out.append(line[i])
        i += 1
    return "".join(out)


def remove_args(text: str, commands: str) -> str:
    """Elimina comandos y sus argumentos, con llaves anidadas."""
    pattern = re.compile(r"\\(?:" + commands + r")\*?")
    out: list[str] = []
    i = 0
    while True:
        match = pattern.search(text, i)
        if not match:
            out.append(text[i:])
            break
        out.append(text[i:match.start()])
        name = match.group(0).lstrip("\\").rstrip("*")
        j = match.end()

        def skip_bracket(position: int) -> int:
            depth = 0
            while position < len(text):
                if text[position] == "[":
                    depth += 1
                elif text[position] == "]":
                    depth -= 1
                    if depth == 0:
                        return position + 1
                position += 1
            return position

        def skip_brace(position: int) -> int:
            depth = 0
            while position < len(text):
                if text[position] == "{":
                    depth += 1
                elif text[position] == "}":
                    depth -= 1
                    if depth == 0:
                        return position + 1
                position += 1
            return position

        while j < len(text) and text[j] == "[":
            j = skip_bracket(j)
            while j < len(text) and text[j] == " ":
                j += 1
        if j < len(text) and text[j] == "{":
            j = skip_brace(j)
        if name == "begin":
            # \begin{env}[opciones]{argumentos} (tabular, minipage, etc.)
            for _ in range(3):
                while j < len(text) and text[j] == " ":
                    j += 1
                if j < len(text) and text[j] == "[":
                    j = skip_bracket(j)
                elif j < len(text) and text[j] == "{":
                    j = skip_brace(j)
                else:
                    break
        out.append(" … ")
        i = j
    return "".join(out)


def clean_line(line: str, keep_commands: bool = False) -> str:
    """Convierte una línea LaTeX en prosa aproximada; devuelve '' si no hay."""
    text = strip_comment(line)
    if re.match(r"\s*\\(newcommand|renewcommand|providecommand|def|"
                r"DeclareMathOperator|titleformat|titlespacing|markboth|"
                r"addcontentsline)\b", text):
        return ""
    text = remove_args(text, SKIP_ARG_CMDS)
    text = MATH_INLINE_RE.sub(" ", text)
    text = re.sub(r"(?<!\\)\\\[.*?(?<!\\)\\\]", " ", text)
    text = re.sub(r"\\\(.*?\\\)", " ", text)
    text = re.sub(r"\\([,;:! ]|quad|qquad|%)", " ", text)
    if keep_commands:
        text = re.sub(r"\\([A-Za-z@]+)\*?", r" \\1 ", text)
    else:
        text = CMD_RE.sub(" ", text)
    text = text.replace("~", " ").replace("{", " ").replace("}", " ")
    text = re.sub(r"\[\s*\]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,}", text):
        return ""
    return text


def extract_segments(path: Path) -> list[tuple[int, str, str]]:
    """Devuelve [(línea, prosa, línea original)] del cuerpo del documento."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"ERROR: no se pudo leer {path}: {exc}", file=sys.stderr)
        return []

    segments: list[tuple[int, str, str]] = []
    in_body = False
    skip_env: str | None = None
    in_display_math = False

    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = strip_comment(raw)

        if not in_body:
            if re.search(r"\\begin\{document\}", stripped):
                in_body = True
            continue

        if skip_env:
            if re.search(r"\\end\{" + re.escape(skip_env) + r"\}", stripped):
                skip_env = None
            continue

        # El resumen en inglés no se revisa con el diccionario español.
        if re.search(r"\\begin\{otherlanguage\}\s*\{english\}", stripped):
            skip_env = "otherlanguage"
            continue

        begin = re.search(r"\\begin\{([^}]*)\}", stripped)
        if begin and begin.group(1).strip() in SKIP_ENVS:
            skip_env = begin.group(1).strip()
            continue

        if in_display_math:
            if re.search(r"(?<!\\)\\\]", stripped):
                in_display_math = False
            continue
        if re.search(r"(?<!\\)\\\[", stripped) and not re.search(
                r"(?<!\\)\\\]", stripped):
            in_display_math = True
            continue

        prose = clean_line(raw)
        if prose:
            segments.append((number, prose, raw))
    return segments


def load_glossary(path: Path) -> list[str]:
    if not path.exists():
        return []
    terms: list[str] = []
    active = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"^##\s+Términos permitidos", line, re.IGNORECASE):
            active = True
            continue
        if active and line.startswith("##"):
            break
        if active:
            match = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
            if match:
                term = re.sub(r"\s+\(.*?\)\s*$", "", match.group(1)).strip()
                if term:
                    terms.append(term)
    return terms


def is_protected(token: str, terms: list[str]) -> bool:
    if not token:
        return True
    plain = strip_accents(token)
    if any(ch.isdigit() for ch in plain) or "/" in plain or "\\" in plain:
        return True
    if re.fullmatch(r"[A-ZÁÉÍÓÚÜÑ]{2,}\d*", token):
        return True
    if re.fullmatch(r"[A-Z][a-z]+[A-Z][A-Za-z]*", token):  # CamelCase
        return True
    low = plain.lower()
    for term in terms:
        for word in term.split():
            if strip_accents(word).lower() == low:
                return True
    if low in {strip_accents(term).lower() for term in terms}:
        return True
    return False


def local_findings(path: Path, segments: list[tuple[int, str, str]],
                   terms: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for number, text, raw in segments:
        markup = clean_line(raw, keep_commands=True)
        for match in re.finditer(
                r"\b([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,})\s+\1\b", markup,
                flags=re.IGNORECASE):
            findings.append(Finding(str(path), number, "warning", "repetición",
                                    f"palabra repetida: «{match.group(0)}»",
                                    rule="palabra-repetida"))

        if "¿" not in text and re.search(
                r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]\s*\?", text):
            findings.append(Finding(str(path), number, "info", "puntuación",
                                    "falta el signo de apertura '¿'",
                                    rule="signo-apertura"))

        if "¡" not in text and re.search(
                r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]\s*!", text):
            findings.append(Finding(str(path), number, "info", "puntuación",
                                    "falta el signo de apertura '¡'",
                                    rule="signo-apertura"))

        for match in WORD_RE.finditer(text):
            word = match.group(0)
            if is_protected(word, terms):
                continue
            key = strip_accents(word).lower()
            correction = ACCENTS.get(key)
            if not correction or word.lower() == correction.lower():
                continue
            if word.isupper():
                suggestion = correction.upper()
            elif word[:1].isupper():
                suggestion = correction[:1].upper() + correction[1:]
            else:
                suggestion = correction
            if suggestion.lower() == word.lower():
                continue
            findings.append(Finding(
                str(path), number, "error", "ortografía",
                f"«{word}» debería escribirse «{suggestion}»",
                suggestion, "acentuación"))
    return findings


def split_long(line: int, text: str, limit: int) -> list[tuple[int, str]]:
    if len(text) <= limit:
        return [(line, text)]
    parts: list[tuple[int, str]] = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            cut = text.rfind(". ", start, end)
            if cut > start + limit // 3:
                end = cut + 1
        parts.append((line, text[start:end].strip()))
        start = end
    return [part for part in parts if part[1]]


def build_chunks(segments: list[tuple[int, str, str]], limit: int) -> list[dict]:
    chunks: list[dict] = []
    current: list[tuple[int, str]] = []
    size = 0

    def flush() -> None:
        nonlocal current, size
        if not current:
            return
        text = "\n".join(part for _, part in current)
        mapping: list[tuple[int, int, int]] = []
        cursor = 0
        for line, part in current:
            mapping.append((cursor, cursor + len(part), line))
            cursor += len(part) + 1
        chunks.append({"text": text, "mapping": mapping, "lines": current})
        current, size = [], 0

    for line, text, _raw in segments:
        for piece in split_long(line, text, limit):
            if size + len(piece[1]) + 1 > limit:
                flush()
            current.append(piece)
            size += len(piece[1]) + 1
    flush()
    return chunks


def line_for_offset(mapping: list[tuple[int, int, int]], offset: int) -> int:
    for start, end, line in mapping:
        if start <= offset <= end:
            return line
    return mapping[-1][2] if mapping else 0


def check_api(chunk: dict, level: str) -> list[dict]:
    data = urllib.parse.urlencode({
        "text": chunk["text"],
        "language": "es",
        "level": level,
        "enabledOnly": "false",
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL, data=data,
        headers={"User-Agent": "TT-A083-spellcheck/1.0",
                 "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8")).get("matches", [])


def api_findings(path: Path, segments: list[tuple[int, str, str]],
                 terms: list[str], level: str, verbose: bool) -> tuple[list[Finding], bool]:
    findings: list[Finding] = []
    chunks = build_chunks(segments, MAX_CHUNK)
    ok = True
    accepted = {"misspelling", "grammar", "typography", "duplication",
                "punctuation", "style", "locale-violation"}
    # Reglas heurísticas que producen falsos positivos en prosa técnica.
    ignored_rules = {"EL_TILDE", "SINGLE_CHARACTER", "A_PARTICIPIO", "D_ELA"}
    seen: set[tuple[int, str, str]] = set()
    try:
        raw_lines = path.read_text(encoding="utf-8",
                                   errors="replace").splitlines()
    except OSError:
        raw_lines = []

    for index, chunk in enumerate(chunks, start=1):
        if verbose:
            print(f"  · LanguageTool: bloque {index}/{len(chunks)} "
                  f"({len(chunk['text'])} caracteres)", file=sys.stderr)
        matches: list[dict] = []
        for attempt in range(3):
            try:
                matches = check_api(chunk, level)
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < 2:
                    wait = int(exc.headers.get("Retry-After", "20") or 20)
                    print(f"  · Límite de la API alcanzado; espero {wait} s...",
                          file=sys.stderr)
                    time.sleep(wait)
                    continue
                print(f"ADVERTENCIA: LanguageTool respondió {exc.code}; "
                      "se omite la revisión en línea.", file=sys.stderr)
                ok = False
                break
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                print(f"ADVERTENCIA: sin conexión con LanguageTool ({exc}); "
                      "se omite la revisión en línea.", file=sys.stderr)
                ok = False
                break
        time.sleep(1.0)

        for match in matches:
            rule = match.get("rule", {})
            issue_type = rule.get("issueType", "")
            rule_id = rule.get("id", "")
            if issue_type not in accepted or rule_id in ignored_rules:
                continue
            offset = int(match.get("offset", 0))
            length = int(match.get("length", 0))
            token = chunk["text"][offset:offset + length]
            if not token.strip():
                continue
            if len(token.strip()) <= 1:
                continue
            if "\n" in token and issue_type == "duplication":
                continue
            line = line_for_offset(chunk["mapping"], offset)
            # Una palabra repetida puede ser un falso positivo si en el .tex
            # hay un comando de formato entre ambas (p. ej. «de \textit{de
            # pie}»).
            repeated = re.match(
                r"^\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)\s+\1\b", token,
                flags=re.IGNORECASE)
            if repeated and 0 < line <= len(raw_lines):
                word = repeated.group(1)
                pattern = (r"\b" + re.escape(word) +
                           r"\s+\\[A-Za-z@]+\*?(?:\[[^\]]*\])?\{?\s*" +
                           re.escape(word) + r"\b")
                if re.search(pattern, raw_lines[line - 1], re.IGNORECASE):
                    continue
            tokens = WORD_RE.findall(token)
            if tokens and all(is_protected(word, terms) for word in tokens):
                continue
            if is_protected(token.strip(), terms):
                continue
            message = match.get("message", "").strip()
            replacements = [rep.get("value", "") for rep
                            in match.get("replacements", [])[:3]
                            if rep.get("value")]
            suggestion = " / ".join(replacements)
            key = (line, token.strip().lower(), message)
            if key in seen:
                continue
            seen.add(key)
            severity = "error" if issue_type == "misspelling" else "warning"
            findings.append(Finding(
                str(path), line, severity, issue_type or "estilo",
                f"«{token.strip()}»: {message}", suggestion,
                rule.get("id", "")))
    return findings, ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Corrector ortográfico y gramatical del TF A083.")
    parser.add_argument("files", nargs="*", default=["main.tex"],
                        help="archivos .tex a revisar (por defecto main.tex)")
    parser.add_argument("--glosario",
                        default=".claude/skills/spellchecker-es/references/glosario.md",
                        help="ruta del glosario de términos permitidos")
    parser.add_argument("--offline", action="store_true",
                        help="solo reglas locales, sin LanguageTool")
    parser.add_argument("--level", default="default",
                        choices=("default", "picky"),
                        help="nivel de exigencia de LanguageTool")
    parser.add_argument("--require-api", action="store_true",
                        help="falla si LanguageTool no está disponible")
    parser.add_argument("--verbose", action="store_true",
                        help="muestra el progreso de la revisión en línea")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    base = Path.cwd()
    glossary = Path(args.glosario)
    if not glossary.is_absolute():
        glossary = base / glossary
    terms = load_glossary(glossary)
    if not terms:
        print(f"ADVERTENCIA: no se cargaron términos de {args.glosario}",
              file=sys.stderr)

    all_findings: list[Finding] = []
    api_ok = True
    for name in args.files:
        path = Path(name)
        if not path.is_absolute():
            path = base / path
        if not path.exists():
            print(f"ERROR: no existe el archivo {name}", file=sys.stderr)
            return 2
        segments = extract_segments(path)
        if args.verbose:
            print(f"  · {name}: {len(segments)} líneas de prosa",
                  file=sys.stderr)
        findings = local_findings(path, segments, terms)
        if not args.offline:
            online, ok = api_findings(path, segments, terms, args.level,
                                      args.verbose)
            findings.extend(online)
            api_ok = api_ok and ok
        all_findings.extend(findings)

    order = {"error": 0, "warning": 1, "info": 2}
    all_findings.sort(key=lambda item: (item.file, item.line,
                                        order.get(item.severity, 9),
                                        item.category))

    if args.format == "json":
        print(json.dumps([asdict(item) for item in all_findings],
                         ensure_ascii=False, indent=2))
    else:
        for item in all_findings:
            try:
                shown = str(Path(item.file).resolve().relative_to(
                    base.resolve())).replace("\\", "/")
            except ValueError:
                shown = item.file
            suggestion = f" → «{item.suggestion}»" if item.suggestion else ""
            rule = f" [{item.rule}]" if item.rule else ""
            print(f"{shown}:{item.line}: {item.severity}: "
                  f"[{item.category}] {item.message}{suggestion}{rule}")
        errors = sum(1 for item in all_findings if item.severity == "error")
        warnings = sum(1 for item in all_findings
                       if item.severity == "warning")
        print(f"\nResumen: {errors} error(es) ortográfico(s), "
              f"{warnings} advertencia(s) gramatical(es)/de estilo.")
        if args.offline:
            print("Modo sin conexión: no se revisó gramática con LanguageTool.")

    if args.require_api and not api_ok:
        return 2
    return 1 if all_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
