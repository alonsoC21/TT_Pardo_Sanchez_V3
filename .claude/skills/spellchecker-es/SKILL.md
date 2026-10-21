---
name: spellchecker-es
description: Revisa ortografía, gramática y puntuación en español de los archivos .tex del Trabajo Terminal A083, respetando el glosario técnico y sin modificar los archivos.
---

# Corrector ortográfico del TF A083

## Cuándo usar esta skill

Úsala después de redactar o editar prosa en `main.tex` y antes de mostrar el
cambio al autor. Revisa únicamente español: el `Abstract` en inglés se excluye
automáticamente.

## Requisitos

- Python 3.10 o superior.
- Conexión a Internet para la revisión gramatical con LanguageTool.
  Sin conexión, usa `--offline` (solo reglas locales).
- No requiere instalar diccionarios ni paquetes de Python.

## Comandos

Desde la raíz del repositorio:

```powershell
# Revisión completa (reglas locales + LanguageTool)
python .claude/skills/spellchecker-es/scripts/spellcheck_es.py main.tex

# Solo reglas locales, sin enviar texto a Internet
python .claude/skills/spellchecker-es/scripts/spellcheck_es.py main.tex --offline

# Nivel más exigente y salida JSON
python .claude/skills/spellchecker-es/scripts/spellcheck_es.py main.tex --level picky --format json

# Usar otro glosario
python .claude/skills/spellchecker-es/scripts/spellcheck_es.py main.tex --glosario ruta/al/glosario.md
```

Códigos de salida: `0` sin hallazgos, `1` con hallazgos, `2` si se pidió
`--require-api` y LanguageTool no respondió.

## Qué revisa

- **Reglas locales (siempre):** palabras repetidas, faltas de `¿`/`¡` y una
  lista de errores de acentuación frecuentes en textos académicos.
- **LanguageTool (en línea):** ortografía, gramática, puntuación, duplicados
  y tipografía en español.

El script extrae solo la prosa: excluye preámbulo, fórmulas, `lstlisting`,
`tikzpicture`, rutas, claves de cita y comandos de formato. El texto se divide
en bloques de 7 000 caracteres y se respeta el límite de peticiones del servicio
gratuito.

## Privacidad

La revisión en línea envía fragmentos de la prosa a `api.languagetool.org`.
Si el autor prefiere no enviar texto a un servicio externo, ejecuta
`--offline`; en ese caso no se revisan gramática ni puntuación compleja.

## Glosario

Los términos que el diccionario no reconoce (YOLO26, MQTT, Mosquitto, CRISP-ML(Q),
nombres de autores, etc.) se declaran en
`references/glosario.md`, sección **Términos permitidos**. Para agregar uno:

1. Confirma que es un nombre propio, sigla, modelo o anglicismo técnico
   admitido por el documento.
2. Agrégalo como una línea `- Término`.
3. No agregues palabras comunes del español: ocultarían errores reales de
   acentuación.
4. Vuelve a ejecutar el corrector.

## Cómo interpretar los hallazgos

- **error de ortografía:** corrige si la sugerencia es inequívoca.
- **warning gramatical o de estilo:** lee la oración completa antes de aceptar
  la sugerencia; LanguageTool no conoce el contexto del proyecto.
- **falsos positivos conocidos:** el script silencia `EL_TILDE`,
  `SINGLE_CHARACTER`, `A_PARTICIPIO` y `D_ELA`, y no reporta repeticiones
  separadas por un comando de formato (por ejemplo, `de \textit{de pie}`).

## Flujo obligatorio

1. Ejecuta `scripts/respaldo.ps1` antes de editar.
2. Aplica el corrector al archivo modificado.
3. Corrige solo lo que no altere el sentido; si hay duda, pregunta al autor.
4. Vuelve a ejecutar hasta que no queden errores.
5. Pasa el linter LaTeX y muestra el diff.
6. No ejecutes `git commit` ni `git push` sin confirmación explícita.

## Limitaciones

- No revisa el `Abstract` en inglés ni los campos del `.bib`.
- No detecta errores semánticos ni terminología incorrecta (por ejemplo, un
  término médico mal formado que el diccionario acepte).
- Nunca modifica archivos: solo informa.
