# Fuente editable de los mockups

Estas pantallas son el origen de `Figuras/mockup1.png` y `Figuras/mockup_2.png`
a `Figuras/mockup_6.png`, incluidas en `main.tex` en la sección
«Diseño de interfaces de la aplicación móvil Android».

| Archivo | Figura | Contenido |
| --- | --- | --- |
| `01_privacidad.html` | `fig:mockup1` | Aviso de privacidad y consentimiento |
| `02_etiqueta.html` | `fig:mockup2` | Escaneo de la etiqueta QR del dispositivo |
| `03_perfil.html` | `fig:mockup3` | Asignación del perfil de cuidado |
| `04_panel.html` | `fig:mockup4` | Panel de dispositivos conectados |
| `05_alerta.html` | `fig:mockup5` | Notificación crítica de posible caída |
| `06_historial.html` | `fig:mockup6` | Historial de eventos |

## Regenerar las capturas

```powershell
powershell -ExecutionPolicy Bypass -File Figuras\mockups_fuente\render.ps1
```

El script usa Chrome o Edge en modo `--headless` y sobrescribe los seis PNG de
`Figuras/`. Cada pantalla mide 360 x 780 px CSS y se captura a 3x, de modo que
todas las imágenes resultan de 1080 x 2340 px.

## Convenciones de diseño

- Fondo `#FBFAF6`, verde institucional `#0F6B4F`, botón oscuro `#33291F` y
  alerta `#D2413A`.
- Tipografía del sistema (Segoe UI); no hay dependencias externas salvo
  `qrcode.js`, que solo se emplea para dibujar el código QR de la etiqueta.
- Los textos de las pantallas deben mantenerse alineados con el cuerpo del
  documento: la aplicación no crea cuentas, no solicita correo ni contraseña,
  no permite el ingreso manual de datos y no transmite video. Cualquier cambio
  de interfaz debe reflejarse también en `main.tex`.
