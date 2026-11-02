# Shotokan AI en Windows: ejecutarlo y empaquetarlo

**Versión del 2-nov-2026.** El sistema se desarrolló en macOS (M1) y se verifica
en Linux; **en Windows todavía no se ha ejecutado nunca**. Esta guía es el orden
de pasos para hacerlo por primera vez y saber, en cada uno, qué tiene que salir.
Si un paso no da lo esperado, no sigas al siguiente: anota el mensaje exacto.

Las órdenes son para **PowerShell**. En Windows, a diferencia de tu Mac, el
comando es `python` (o `py`), no `python3`.

---

## 1. Requisitos del equipo

| | Mínimo | Comentario |
|---|---|---|
| Windows | 10 u 11 de **64 bits** | MediaPipe no tiene versión de 32 bits |
| Procesador | 4 núcleos | No necesita tarjeta gráfica |
| Memoria | 4 GB | El análisis usa ~250 MB (medido sin interfaz) |
| Disco | 1 GB libre, más los videos | Librerías ~300 MB y modelo 9,4 MB |
| Pantalla | 1280×720 | La ventana mide 1000×680 |
| Cámara | Webcam USB o integrada, 720p | O un teléfono como cámara IP |

---

## 2. Instalar Python

1. Descarga **Python 3.11 de 64 bits** de python.org (*Windows installer
   (64-bit)*). La 3.11 es la que usa tu Mac; la 3.12 también está verificada.
2. En la primera pantalla del instalador marca **«Add python.exe to PATH»**.
3. Deja marcada la opción **tcl/tk and IDLE** (viene por omisión): sin ella no
   hay interfaz gráfica.

Comprueba:

```powershell
py -3.11 --version
```

Tiene que decir `Python 3.11.x`.

**Lo que pasó la primera vez (2-nov-2026), para no repetirlo.** El equipo ya
tenía Python 3.14 en `C:\Python314`, y `py -3.11` respondía «No suitable
Python runtime found». La 3.11 **no estaba instalada**: lo que se había
instalado desde Microsoft Store (`9NQ7512CXL7T`) es el *Python Install
Manager*, un administrador de versiones, no Python 3.11; y sus órdenes
(`py install`, `py list`) no funcionan mientras siga presente el `py` antiguo.
No hace falta tocar nada de eso. Lo que funcionó, sin permisos de
administrador:

```powershell
Invoke-WebRequest "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$HOME\Downloads\python-3.11.9-amd64.exe"
Start-Process -Wait "$HOME\Downloads\python-3.11.9-amd64.exe" -ArgumentList "/passive InstallAllUsers=0 PrependPath=0 Include_tcltk=1"
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" --version
```

La 3.11.9 es la última 3.11 con instalador para Windows. Con esa ruta
completa se crea el entorno del paso 4 aunque `py` no la vea. **No uses la
3.14**: el sistema no se ha probado en ella y pip le trae versiones mayores
nuevas de OpenCV, NumPy y CustomTkinter.

---

## 3. Traer el código

Con Git instalado:

```powershell
cd $HOME\Desktop
git clone https://github.com/SHolweger/karate_biomecanica.git
cd karate_biomecanica
```

Sin Git: en GitHub, *Code → Download ZIP*, descomprimir y abrir PowerShell en
esa carpeta. El modelo `pose_landmarker_full.task` viene en el repositorio:
comprueba que está en la carpeta.

---

## 4. Entorno e instalación

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -c "import sys, tkinter; print(sys.version, tkinter.TkVersion)"
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

La tercera orden tiene que decir `3.11.x` y un número de Tk (`8.6`); si dice
otra versión, el entorno se creó con otro Python y hay que borrarlo y
rehacerlo. Un entorno ya existente se reconoce por su `pyvenv.cfg`, y la línea
`version =` dice con qué Python se creó:

```powershell
Get-ChildItem -Recurse -Depth 2 -Force -Filter pyvenv.cfg | Select-Object FullName
```

Si PowerShell no deja activar el entorno («la ejecución de scripts está
deshabilitada»), corre una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a activarlo.

---

## 5. Las pruebas

```powershell
python -m pytest -q
```

En tu Mac salen **1090** (1088 más las 2 del lote `vivo2nov`). En Windows deberían ser las mismas.
**Anota la cifra exacta y si falla alguna**: es la primera evidencia de que el
sistema corre en Windows, y va a la tesis tal cual.

**Primera corrida en Windows (2-nov-2026, Python 3.11.9): 1071 passed, 6
failed, 17 errors de 1094.** Ninguno era del sistema en uso:

| Cuántas | Qué era | Arreglo |
|---|---|---|
| 16 errores | `test_navegacion_rnf04.py` enlazaba el modelo con `symlink_to`, y Windows solo crea enlaces con modo de desarrollador o como administrador (`WinError 1314`) | Si el enlace falla, se copia |
| 2 fallos | `plan_de_pruebas.py` guardaba la ruta de cada caso con `\`, así que no reconocía ningún caso de `tests/e2e/`: el plan generado en Windows salía **sin los casos de interfaz** | La ruta se guarda con `/` (`as_posix`) |
| 1 fallo | El mismo generador escribía el `.md` con CRLF | `newline="\n"` |
| 3 fallos | Pruebas que comparaban rutas escritas con `/` contra lo que Windows devuelve con `\` | La prueba compara contra la ruta del sistema |
| 1 error | Tk no encontró `ttk/cursors.tcl` al crear la ventana, en una sola prueba; las otras ~110 de interfaz crearon la suya sin problema | Ninguno todavía: parece intermitente, causa sin identificar. Si se repite al correr esa prueba sola, es un problema de la instalación de Tk |

Los dos del generador sí eran defectos reales, aunque de una herramienta y no
de la aplicación. La cifra con los arreglos se cuenta en la siguiente corrida.

---

## 6. El programa

```powershell
python main.py
```

La primera vez pide crear la cuenta del sensei. Los datos van a
`%APPDATA%\ShotokanAI\`: la base `karate_sistema.db` y la carpeta
`grabaciones`. **Es una base nueva y vacía**: tus alumnos de la Mac no están.
Para traerlos, cierra el programa y copia tu `karate_sistema.db` a esa carpeta.

Si la lista de cámaras sale vacía: *Configuración → Privacidad y seguridad →
Cámara*, y activa **«Permitir que las aplicaciones de escritorio accedan a la
cámara»**. En Windows las cámaras aparecen por número y no por nombre; es
esperable.

Qué mirar, en este orden:

1. Elegir la cámara en «Cámara» y ver la vista previa.
2. «Análisis en vivo» con un alumno: esqueleto, grados y panel de correcciones.
3. Terminar la sesión y abrir su reporte.
4. Re-analizar un video grabado desde «Cámara».

---

## 7. Empaquetar: el `.exe`

Con el entorno activado y desde la carpeta del proyecto:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name ShotokanAI `
  --add-data "pose_landmarker_full.task;." `
  --collect-data mediapipe --collect-binaries mediapipe `
  --collect-data customtkinter `
  main.py
```

(Las comillas invertidas al final de cada línea son las de PowerShell para
seguir el comando en la siguiente.)

El resultado es la carpeta **`dist\ShotokanAI\`**, con `ShotokanAI.exe` dentro.
**Se reparte la carpeta entera**, no solo el `.exe`: a su lado van MediaPipe,
OpenCV y el modelo. Se eligió carpeta y no un único archivo (`--onefile`) a
propósito: arranca mucho más rápido y los antivirus lo marcan menos.

Por qué cada opción:

| Opción | Sin ella |
|---|---|
| `--add-data "pose_landmarker_full.task;."` | El programa no encuentra el modelo y lo dice (`ModeloNoEncontrado`) |
| `--collect-data/--collect-binaries mediapipe` | MediaPipe no encuentra sus propias bibliotecas al estimar la pose |
| `--collect-data customtkinter` | Faltan los temas de la interfaz y no abre |
| `--windowed` | Se abre además una consola negra detrás de la ventana |

**Probado el 2-nov-2026 en Linux**, que es lo que el contenedor de desarrollo
puede hacer: el mismo comando —con `:` en lugar de `;` en `--add-data`, que es
el separador de Linux y Mac— arma la carpeta, la interfaz empaquetada abre en la
pantalla de acceso y `ShotokanAI --consola --fuente video.mp4` encuentra el
modelo, estima la pose y registra la sesión en la base. Lo que no se pudo
probar es Windows mismo.

Probar, en este orden:

1. Doble clic en `dist\ShotokanAI\ShotokanAI.exe` **en el mismo equipo**.
2. Copiar la carpeta a **otro equipo sin Python** y repetir. Es la prueba que
   vale: en el primer equipo, lo que falte en el paquete lo puede tapar lo que
   ya está instalado.

Si en el otro equipo falla con «DLL load failed» o «no se encontró
MSVCP140.dll», instala el **Microsoft Visual C++ Redistributable 2015–2022
(x64)**: MediaPipe y OpenCV lo necesitan y algunos Windows no lo traen.

**No instales la carpeta en `Archivos de programa`.** «Generar reporte» del
perfil del alumno todavía guarda la gráfica en una carpeta `evidencias`
relativa a donde se abrió el programa, y ahí Windows no deja escribir. En el
Escritorio o en Documentos funciona.

---

## 8. En la Mac: el lanzador `.command`

Para abrir el programa con doble clic sin escribir comandos, crea en la carpeta
del proyecto un archivo `ShotokanAI.command` con:

```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py
```

y dale permiso de ejecución una vez: `chmod +x ShotokanAI.command`.

---

## 9. Qué anotar para la tesis

- Versión de Windows, procesador y memoria del equipo.
- Cuántas pruebas pasaron (paso 5).
- Si la interfaz, la cámara y el reporte funcionaron (paso 6).
- Si el `.exe` abrió en un equipo sin Python (paso 7).

Hasta tener eso, la tesis puede decir que el sistema es **multiplataforma por
diseño** (las rutas de datos de Windows están resueltas en `rutas.py` y las
dependencias tienen versión para Windows), pero **no** que esté verificado en
Windows.
