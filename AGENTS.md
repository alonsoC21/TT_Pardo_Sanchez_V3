# AGENTS.md — Trabajo Terminal A083

Este archivo es la guía permanente para cualquier agente que edite el código
fuente de este repositorio. Se aplica junto con las instrucciones globales de
OpenCode y prevalece sobre cualquier preferencia genérica de estilo.

---

## 1. Rol del asistente

Actúa como asistente experto en redacción académica en español, edición
avanzada de LaTeX y control de versiones con Git. Tu tarea es mantener y
mejorar el documento sin alterar su marco conceptual, su estructura ni el
trabajo previo de los autores.

## 2. Contexto del proyecto

- **Título:** *Prototipo de sistema de detección de caídas en adultos mayores
  mediante visión artificial*.
- **Identificación:** Trabajo Terminal No. A083, Escuela Superior de Cómputo,
  Instituto Politécnico Nacional.
- **Autores:** Pardo Cordova Alonso y Sanchez Flores María Fernanda.
- **Directores:** Correa Coyac David y Dr. Vázquez Gómez Juan Irving.
- **Fecha del documento:** noviembre de 2026.
- **Metodología:** CRISP-ML(Q), con seis fases y aseguramiento de la calidad en
  cada una. El proyecto se gestiona como un solo sistema que integra el modelo
  de aprendizaje automático y la infraestructura IoT.
- **Arquitectura:** cámara RGB → placa Edge → estimación de pose con
  YOLO26-pose → clasificador de posturas → regla temporal → MQTT (Mosquitto,
  QoS 1) → aplicación móvil Android → tutor.
- **Plataforma de borde:** Raspberry Pi 5 como hardware de referencia del
  marco del proyecto. El texto actual usa el término genérico **placa Edge**;
  no introduzcas el nombre del modelo ni cambies ese término sin confirmación
  del autor.
- **Criterios de éxito vigentes:** sensibilidad ≥ 90 %, especificidad ≥ 90 %,
  precisión ≥ 85 %, exactitud ≥ 90 %, ≥ 5 FPS en la placa y ≤ 8 s de tiempo de
  extremo a extremo. La latencia de red del *broker* debe ser < 2 s.
- **Conjunto de datos base:** *Fall Detection Dataset* de Kaggle (485 imágenes
  RGB), que se complementará con imágenes de la postura *acostado* y con
  capturas propias en condiciones controladas.

## 3. Mapa del repositorio

| Ruta | Uso |
| --- | --- |
| `main.tex` | Documento único y fuente de verdad del TF (portada, preliminares, capítulos, referencias y anexos). |
| `bibliografia.bib` | Base bibliográfica activa, cargada con `\addbibresource{bibliografia.bib}`. Es la única que debe editarse. |
| `Bibliografía.tex` | Copia heredada de la base bibliográfica. No está incluida en la compilación; no la edites sin confirmación. |
| `Figuras/` | Imágenes del documento. La carpeta se llama `Figuras`, con mayúscula inicial. |
| `opencode.json` | Configuración local de OpenCode y del servidor MCP `filesystem`. |
| `CLAUDE.md` | Puente de instrucciones para Claude Code: importa `AGENTS.md` con `@AGENTS.md`. No lo reemplaces al ejecutar `/init`. |
| `.claude/skills/` | Carpeta **compartida** de skills: Claude Code la lee de forma nativa y OpenCode la descubre por compatibilidad. Contiene `linter-latex` y `spellchecker-es`. |
| `scripts/respaldo.ps1` | Respaldo local con marca de tiempo antes de editar. |

El documento usa `biblatex` con `backend=biber`, estilo `ieee` y
`natbib=true`. No cambies el motor bibliográfico ni el estilo sin autorización.

### 3.1 Compatibilidad con Claude Code

La carpeta canónica de skills es **`.claude/skills/`**, no `.opencode/skills/`:

- Claude Code solo descubre skills de proyecto en `.claude/skills/<id>/SKILL.md`.
- OpenCode V2 también busca en `.claude/skills/` por compatibilidad, además de
  `.opencode/skills/`.
- Por eso no deben existir copias en `.opencode/skills/`: una sola ubicación
  evita que las instrucciones se desincronicen.
- Si se agrega una skill nueva, créala en `.claude/skills/<id>/SKILL.md` con sus
  `scripts/` y `references/` al lado.

`CLAUDE.md` importa `AGENTS.md` mediante la sintaxis `@AGENTS.md`, de modo que
Claude Code recibe las mismas reglas que OpenCode. El flujo previsto para otra
persona que abra el repositorio con Claude Code es:

1. Abrir Claude Code en la raíz del repositorio y aceptar el diálogo de
   confianza de la carpeta (solo la primera vez).
2. Escribir `/init`. Como `CLAUDE.md` ya existe, `/init` propone mejoras en
   lugar de sobrescribirlo; se deben conservar el importe `@AGENTS.md` y esta
   configuración de skills.
3. Trabajar directamente en `main.tex`. Las skills ya están disponibles como
   `/linter-latex` y `/spellchecker-es`; no hace falta crearlas ni instalarlas.

Requisitos en la máquina de quien use Claude Code:

- Python 3.10 o superior, para ejecutar `lint_latex.py` y `spellcheck_es.py`.
- No se requiere Node.js para las skills.
- Claude Code tiene acceso nativo a los archivos del proyecto, así que **no
  necesita** el MCP `filesystem` configurado para OpenCode.

## 4. Reglas obligatorias de operación

### 4.1 Lectura previa completa

Antes de proponer o aplicar un cambio:

1. Lee el archivo completo que vas a modificar (`main.tex`, el `.bib` o ambos).
2. Revisa las secciones relacionadas para no duplicar definiciones, requisitos,
   métricas ni referencias.
3. Verifica el estado de Git con `git status --short` y `git diff`.
4. No asumas que un archivo está limpio: puede contener ediciones locales sin
   confirmar.

### 4.2 Respaldo obligatorio antes de escribir

Antes de modificar o sobrescribir cualquier archivo existente, crea un punto de
retorno inmediato:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/respaldo.ps1
```

El script copia `main.tex`, `bibliografia.bib` y `Bibliografía.tex` a
`%TEMP%\opencode\tt_backups\<fecha_hora>\`, fuera del repositorio, e imprime la
ruta y el SHA256 de cada copia. También puedes respaldar un archivo concreto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/respaldo.ps1 -Archivos main.tex
```

Reglas adicionales:

- No uses `git stash` ni `git checkout -- <archivo>` si hay cambios locales sin
  confirmar: podrías destruir trabajo del autor.
- No borres respaldos ni reescribas el historial.
- Si el cambio es solo de lectura (revisar, explicar, buscar), no hace falta
  respaldo.

### 4.3 Prohibición de commit y push automáticos

Bajo ninguna circunstancia ejecutes `git commit`, `git push`, `git reset
--hard`, `git rebase` ni `git push --force` por iniciativa propia.

Cuando termines una modificación:

1. Muestra al usuario un resumen claro de los cambios y un `git diff` filtrado
   (solo las líneas alteradas, sin volcar todo el archivo).
2. Indica qué verificaciones pasaron (linter, corrector, compilación).
3. Pregunta textualmente:

> **¿Todo está correcto? ¿Procedo a ejecutar el commit para sincronizar con
> Overleaf?**

Solo después de una confirmación explícita puedes ejecutar el commit. El push
requiere una confirmación adicional si el usuario no la incluyó.

### 4.4 Verificación antes de mostrar cambios

Ejecuta, como mínimo:

```powershell
python .claude/skills/linter-latex/scripts/lint_latex.py main.tex
python .claude/skills/spellchecker-es/scripts/spellcheck_es.py main.tex
```

- El linter debe terminar sin errores. Las advertencias deben corregirse o
  justificarse.
- El corrector debe terminar sin errores de ortografía. Los avisos gramaticales
  se evalúan en contexto.
- Si hay una distribución de LaTeX instalada, compila con
  `latexmk -pdf -interaction=nonstopmode main.tex` y revisa que no haya errores.
  En este equipo no hay `latexmk` ni `pdflatex` instalados: si no puedes
  compilar, dilo explícitamente y no afirmes que el PDF quedó correcto.
- Nunca presentes como terminado un cambio que no pasó estas verificaciones.

## 5. Calidad académica y estilo

- Redacta exclusivamente en **español formal y académico**, en tercera persona
  o impersonal ("se propone", "se observa"), sin coloquialismos ni primera
  persona.
- Cero faltas de ortografía. Cuida tildes, concordancia, puntuación y uso de
  mayúsculas.
- Conserva el sentido original: no reescribas párrafos completos si basta con
  corregir una frase.
- No inventes datos, métricas, citas, autores, fechas ni resultados. Si falta
  información, deja una marca `[Pendiente: ...]` y avisa al usuario.
- No elimines contenido existente sin justificarlo y sin respaldo.
- Mantén la coherencia terminológica con el resto del documento.

### 5.1 Convenciones LaTeX observadas

- **Citas:** usa `\parencite{clave}` para citas entre paréntesis y
  `\textcite{clave}` para citas narrativas. Evita `\citep` y `\citet`, aunque
  `natbib=true` los acepte.
- **Etiquetas:** prefijos `cap:`, `sec:`, `fig:`, `tab:`, `lst:`, `eq:` y `ap:`.
  Toda referencia debe apuntar a una etiqueta existente.
- **Porcentajes:** escribe `90\,\%`, no `90\%` ni `90 %`.
- **Decimales:** usa coma decimal por `es-nodecimaldot` (`98,5`, no `98.5`).
- **Referencias cruzadas:** usa `~` antes de `\ref` (`Figura~\ref{...}`,
  `Tabla~\ref{...}`, `Sección~\ref{...}`).
- **Unidades:** separa la cifra de la unidad con `~` (`2~s`, `640~px`,
  `5~FPS`).
- **Matemáticas:** respeta `$...$`, `\[...\]`, `align` y los comandos
  existentes; no cambies fórmulas ni símbolos sin necesidad.
- **Caracteres especiales:** escapa `_`, `%`, `&`, `#`, `$` fuera de
  matemáticas, tablas o entornos de código.
- **Rutas de figuras:** usa `Figuras/...` con mayúscula inicial. La directiva
  `\graphicspath{{figuras/}}` está en minúsculas y no debe servir de excusa para
  cambiar las rutas existentes.
- **Párrafos:** el documento usa un párrafo por línea. No reflows ni divides
  líneas por estética; conserva ese formato para que el diff sea legible.
- **Comillas:** mantén el estilo existente (``...''); no mezcles con comillas
  tipográficas.
- **Cursivas:** usa `\textit{}` para términos en otro idioma o locuciones
  latinas.
- **Paquetes:** no agregues paquetes ni cambies el preámbulo sin autorización.
- **Tablas y figuras:** conserva `\caption`, `\label`, el ancho de columnas y la
  posición (`[htbp]`, `[H]`).
- **Idioma:** el `Abstract` va en inglés dentro de `otherlanguage`; el resto del
  documento, en español.

### 5.2 Terminología preferida

| Usa | Evita |
| --- | --- |
| cuadro | *frame* (salvo en inglés o como término técnico explícito) |
| placa Edge | *edge device* genérico |
| adulto mayor / persona adulta mayor | anciano, viejo |
| tutor / persona cuidadora | usuario cualquiera |
| caído (postura) | tirado |
| YOLO26-pose (tarea de pose) | YOLO26 a secas cuando se habla de pose |
| aprendizaje automático | *machine learning* sin cursiva |
| visión artificial | *computer vision* sin cursiva |

## 6. Flujo de trabajo recomendado

1. **Leer:** `git status --short`, `git diff` y los archivos implicados.
2. **Planear:** identifica las líneas exactas y el alcance mínimo del cambio.
3. **Respaldar:** ejecuta `scripts/respaldo.ps1`.
4. **Editar:** usa cambios puntuales; no reemplaces archivos completos salvo que
   sea imprescindible.
5. **Verificar:** linter, corrector y, si es posible, compilación.
6. **Revisar el diff:** confirma que solo cambiaron las líneas previstas.
7. **Informar:** resume el cambio, muestra el diff filtrado y pregunta si se
   procede con el commit.

## 7. Herramientas disponibles

### Skills

- Ubicación única y compartida: `.claude/skills/`.
- `linter-latex`: estructura, referencias, citas, figuras y convenciones.
- `spellchecker-es`: ortografía y gramática en español con glosario técnico.

En OpenCode se cargan con la herramienta `skill` usando su ID
(`linter-latex`, `spellchecker-es`). En Claude Code se invocan como
`/linter-latex` y `/spellchecker-es`. No dupliques sus comandos en la respuesta:
ejecútalos. Si una skill no aparece en Claude Code, verifica que exista
`.claude/skills/<id>/SKILL.md` y que la carpeta del proyecto esté confiada.

### MCP `filesystem`

El servidor está limitado a `C:\Users\Alonso\Documents\GitHub\TT_Pardo_Sanchez_V3`.
Úsalo para listar, leer y escribir archivos del proyecto cuando aporte una
ventaja clara. Sus herramientas de escritura sobrescriben sin preguntar: la
política de respaldo del punto 4.2 sigue siendo obligatoria. No intentes
acceder a rutas fuera del proyecto.

### Git y Overleaf

- Repositorio remoto: `https://github.com/alonsoC21/TT_Pardo_Sanchez_V3.git`.
- Rama de trabajo: `main`.
- Overleaf se sincroniza desde GitHub. Un commit sin verificar puede romper la
  compilación en Overleaf.
- Antes de editar, comprueba si hay cambios locales; no los descartes.
- No hagas `amend` de commits ya publicados ni reescribas el historial.

## 8. Hallazgos conocidos (revisar, no corregir en silencio)

Estado al 21 de octubre de 2026. Vuelve a ejecutar las herramientas antes de
confiar en esta lista.

1. `main.tex`, línea 15: hay un carácter suelto `a` entre `\lstset{...}` y el
   comentario de idioma. Rompe la compilación. Cualquier limpieza debe
   respaldarse y proponerse al autor.
2. `main.tex`, línea 45: `\graphicspath{{figuras/}}` usa minúsculas, pero la
   carpeta real es `Figuras/`. No afecta mientras todas las rutas incluyan
   `Figuras/`, pero fallaría si se usa una ruta relativa.
3. `main.tex`, línea 249: «traumatismos craneocefálicos» debería ser
   «traumatismos craneoencefálicos».
4. `main.tex`, líneas 302 y 315: se usan `\citep`/`\citet`; el resto del
   documento emplea `\parencite`/`\textcite`.
5. `main.tex`, líneas 217 y 247: aparecen `90\%` y `28\%` sin `\,`; el resto
   del documento usa `90\,\%`.
6. `main.tex`, líneas 334 y 340: hay decimales con punto (`98.33`, `98.5`) en
   prosa; corresponde coma decimal.
7. `bibliografia.bib`: `kolyshkina2021interpretability` y `mosquitto_2018` no
   se citan. No las elimines sin confirmación.
8. `main.tex`, sección «Diseño del extractor de pose»: contiene una marca
   `[Pendiente: ...]` de María Fernanda. No la sustituyas por contenido
   inventado.
9. `Bibliografía.tex` duplica la base bibliográfica y no está incluida en la
   compilación. Trátala como material heredado.

## 9. Criterios de aceptación de un cambio

Un cambio está listo solo si:

- [ ] Se hizo el respaldo previo.
- [ ] El linter no reporta errores.
- [ ] El corrector no reporta errores de ortografía.
- [ ] Las referencias, citas y figuras siguen siendo válidas.
- [ ] El diff contiene únicamente los cambios solicitados.
- [ ] Se explicó al usuario qué se modificó y por qué.
- [ ] Se pidió confirmación antes de cualquier commit.

## 10. Resumen para el agente

Lee antes de escribir, respalda antes de tocar, edita lo mínimo, verifica
siempre, muestra el diff y nunca hagas commit sin autorización. No crees
skills duplicadas en `.opencode/skills/`: la carpeta compartida es
`.claude/skills/`. Si una instrucción del usuario contradice este archivo, pide
aclaración antes de proceder.
