# -*- coding: utf-8 -*-
"""Arma la página de referencia (Artifact) con las 4 láminas embebidas."""
import re, os, sys

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laminas_37.html")
if len(sys.argv) > 1:          # ruta de salida alterna: python3 _construir_pagina.py <ruta>
    SALIDA = sys.argv[1]


def svg_responsivo(ruta):
    s = open(ruta, encoding="utf-8").read()
    s = re.sub(r'<svg([^>]*?)\swidth="\d+"\sheight="\d+"', r'<svg\1', s, count=1)
    return s.strip()


LAMINAS = [
    dict(
        num="3.7.1", titulo="Diagrama de casos de uso", script="d1_casos_uso.py",
        archivo="3.7.1_diagrama_casos_uso.svg", estado="4 actores · 13 casos de uso",
        lee=[
            ("El deportista es actor <em>secundario</em>",
             "Es medido, no opera el sistema. Esa distinción es la que justifica que el perfil de atleta no tenga contraseña: "
             "responde “¿de quién son estos datos?”, no “¿quién tiene permiso?”. El RF-08 solo aplica al entrenador."),
            ("«extend» y no «include» para la retroalimentación en pantalla",
             "El análisis puede ejecutarse sin mostrar nada — es exactamente lo que hiciste al reprocesar los videos frame por frame "
             "para depurar el Mae Geri. Si fuera «include», el diagrama afirmaría que mostrar en pantalla es obligatorio, y sería falso."),
            ("Los módulos IMU son un actor externo, no una pieza interna",
             "Colocarlos fuera de la frontera del sistema es la representación gráfica de la decisión que ya tomaste: el sistema funciona "
             "completo en modo solo-visión y el hardware inercial lo mejora, no lo habilita."),
        ],
        defensa=[
            ("¿Por qué el deportista no se autentica si sus datos son biométricos?",
             "Porque el control de acceso está en quien <em>consulta y modifica</em>, no en quien es medido. El atleta nunca opera la aplicación: "
             "el entrenador autenticado abre la sesión y elige el perfil. Poner una contraseña por atleta añadiría una barrera de usabilidad "
             "(RNF-04, ciclo en ≤3 clics) sin cerrar ningún hueco real de seguridad, porque el acceso a la base de datos ya está detrás del login del entrenador."),
            ("¿Por qué “Editar umbrales biomecánicos” aparece punteado?",
             "Porque el requerimiento RF-08 lo exige y todavía no está construido. Preferí que el diagrama diga la verdad sobre el estado del código "
             "antes que prometer una función inexistente. La convención de color es consistente en las cuatro láminas."),
        ],
    ),
    dict(
        num="3.7.2", titulo="Diagrama de entidad-relación", script="d2_entidad_relacion.py",
        archivo="3.7.2_diagrama_entidad_relacion.svg", estado="4 tablas en uso · 1 propuesta",
        lee=[
            ("Las cuatro tablas azules existen y tienen datos reales",
             "<code>entrenador</code>, <code>atleta</code>, <code>sesion</code> y <code>tecnica_evaluada</code> son el esquema que ya corre en "
             "<code>karate_sistema.db</code>. El reprocesamiento de <code>prueba 3.mov</code> escribió 136 filas en <code>tecnica_evaluada</code>."),
            ("<code>rol</code> es un campo de texto, no una tabla de permisos",
             "El diagrama hace visible la decisión de YAGNI que ya habías tomado: con 3-5 senseis de un solo dojo, un RBAC completo "
             "(tablas ROL y PERMISO con relaciones muchos-a-muchos) resuelve problemas que este proyecto no tiene."),
            ("<code>UMBRAL_REFERENCIA</code> es la tabla que cierra dos huecos a la vez",
             "Cierra el RF-08 (“restringir la modificación de umbrales a entrenadores autorizados”) y da respaldo en el modelo de datos a la sección "
             "“Estrategia de recolección inicial de datos”, que promete umbrales promediados de cinturones negros."),
        ],
        defensa=[
            ("Si un entrenador recalibra un umbral, ¿qué pasa con el historial ya evaluado?",
             "Nada: no se reescribe. Por eso <code>tecnica_evaluada</code> lleva <code>id_umbral</code> como llave foránea — cada medición histórica "
             "apunta a la fila de umbral que la juzgó. Sin ese campo, recalibrar dejaría el historial sin criterio verificable y las gráficas de progreso "
             "compararían mediciones evaluadas con reglas distintas sin advertirlo. Es el mismo principio de un laboratorio que anota qué calibración "
             "tenía el instrumento el día de la medición."),
            ("¿Por qué SQLite y no PostgreSQL, si la tesis habla de un “gestor relacional”?",
             "SQLite <em>es</em> un gestor relacional completo: transacciones ACID, llaves foráneas, SQL estándar. La diferencia es que corre embebido en un "
             "archivo en vez de como servicio. Eso no es una concesión, es lo que exige el RNF-02: si el sistema debe operar 100 % local en el equipo del dojo, "
             "instalar y mantener un servidor de base de datos añade un punto de falla y una tarea de administración que nadie en el dojo va a hacer."),
        ],
    ),
    dict(
        num="3.7.3", titulo="Diagrama de clases", script="d3_clases.py",
        archivo="3.7.3_diagrama_clases.svg", estado="15 clases · 5 capas",
        lee=[
            ("La máquina de estados vive fuera del motor de inferencia",
             "<code>TechniqueAnalyzer</code> responde “¿qué hay ahora?”; <code>MaeGeriStateMachine</code> responde “¿en qué fase de un evento de varios "
             "frames estamos?”. Son responsabilidades distintas, y separarlas es lo que permitió probar la máquina con números sintéticos, sin cámara "
             "(<code>test_mae_geri_fsm.py</code>, 7/7)."),
            ("<code>MovingAverageFilter</code> aparece en dos composiciones",
             "Cinco instancias dentro del analizador (dos codos, dos rodillas, y la diferencia de profundidad Z de la guardia) y una dentro de cada máquina "
             "de estados. Es la misma clase reutilizada seis veces, no código duplicado — eso es lo que el diagrama demuestra."),
            ("<code>KarateRules</code> es solo métodos estáticos",
             "No tiene estado porque es la base de conocimientos, no el motor. Agregar una técnica nueva es agregar un método; el motor de inferencia no cambia. "
             "Esa es, literalmente, la separación motor/base de conocimientos que exige un sistema experto."),
            ("<code>main.py</code> sigue en el diagrama",
             "La GUI no lo reemplazó: es una vía de acceso alterna por consola, ya probada, que usa exactamente las mismas clases. Conservarla fue deliberado."),
        ],
        defensa=[
            ("¿Dónde está la separación entre motor de inferencia y base de conocimientos?",
             "En dos archivos distintos. <code>expert_system/knowledge_base.py</code> contiene solo los umbrales y su interpretación: recibe un ángulo, devuelve "
             "(correcto, mensaje, color). <code>expert_system/analyzer.py</code> es el motor: extrae los landmarks, calcula ángulos, los filtra, clasifica en qué "
             "postura está el atleta y decide a qué regla consultar. Si mañana cambian los umbrales del Shotokan, se toca un solo archivo y el motor no se entera."),
            ("¿Por qué la máquina de estados no está dentro de <code>TechniqueAnalyzer</code>?",
             "Por dos razones. La primera es de diseño: el analizador es sin memoria semántica, evalúa el frame actual; la máquina necesita recordar en qué fase de la "
             "patada va, el ángulo máximo alcanzado y la velocidad pico. La segunda es práctica: al no depender de MediaPipe ni de píxeles — solo recibe ángulo, "
             "visibilidad, Y del tobillo y timestamp — se puede probar con datos sintéticos. Eso es lo que permitió calibrar los umbrales sin cámara."),
        ],
    ),
    dict(
        num="3.7.4", titulo="Diagrama de despliegue físico", script="d4_despliegue.py",
        archivo="3.7.4_diagrama_despliegue.svg", estado="1 nodo Edge · 2 periféricos",
        lee=[
            ("Un solo nodo de cómputo, sin capa de servidor",
             "Todo el software vive en un <code>«device»</code>: el equipo del dojo. No hay nodo en la nube que dibujar porque no existe — eso es el RNF-02 hecho gráfico."),
            ("El modelo de red neuronal es un artefacto local",
             "<code>pose_landmarker_full.task</code> (≈32 MB) se despliega junto al código. MediaPipe no consulta ninguna API: la inferencia de pose corre en CPU local."),
            ("La base de datos es un archivo, no un servicio",
             "<code>karate_sistema.db</code> aparece como artefacto dentro del entorno de ejecución, al mismo nivel que el código. Respaldarla es copiar un archivo."),
        ],
        defensa=[
            ("¿Cómo demuestras que el sistema no usa Internet?",
             "Con una prueba de treinta segundos que se puede hacer en vivo: desconectar el Wi-Fi del equipo y ejecutar un ciclo completo — login, selección de perfil, "
             "análisis de una técnica en cámara y guardado en la base de datos. Si algo dependiera de la nube, fallaría ahí mismo. Vale la pena incluirla en el plan de "
             "pruebas del capítulo como criterio de aceptación del RNF-02, porque es verificable y no depende de creer en el diagrama."),
            ("Si los sensores inerciales no llegan a tiempo, ¿el sistema queda incompleto?",
             "No, queda en el alcance que el propio capítulo ya define. El RF-02 dice “cuando el hardware inercial esté disponible y conectado; el sistema debe permanecer "
             "operativo exclusivamente con visión artificial en su ausencia”, y el RF-04 aclara que la fusión aplica solo si hay stream IMU activo. El diagrama refleja esa "
             "condición dibujando los módulos punteados y fuera del nodo de cómputo."),
        ],
    ),
]


def bloque_lamina(l):
    lee = "\n".join(
        f'<li><h4>{t}</h4><p>{p}</p></li>' for t, p in l["lee"])
    defensa = "\n".join(
        f'<details><summary>{q}</summary><div class="respuesta"><p>{a}</p></div></details>'
        for q, a in l["defensa"])
    return f'''
<section class="lamina" id="s{l["num"].replace(".", "")}">
  <div class="cartela">
    <span class="cartela-num">{l["num"]}</span>
    <span class="cartela-tit">{l["titulo"]}</span>
    <span class="cartela-meta">{l["estado"]}</span>
    <code class="cartela-src">diagramas/{l["script"]}</code>
  </div>
  <div class="hoja-envoltura">
    <div class="hoja">{svg_responsivo(l["archivo"])}</div>
  </div>
  <div class="prosa">
    <h3 class="eyebrow">Qué decisiones refleja</h3>
    <ul class="lecturas">{lee}</ul>
    <h3 class="eyebrow">Mini-defensa</h3>
    <div class="defensa">{defensa}</div>
  </div>
</section>'''


HTML = f'''<title>Láminas del Sistema Experto</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* ---------- fichas de color: aka / ao, los dos colores de competencia del karate ---------- */
:root {{
  --papel:      #eceff3;
  --hoja:       #ffffff;
  --panel:      #f6f7f9;
  --tinta:      #0f1620;
  --tinta-2:    #4d5866;
  --tinta-3:    #7d8794;
  --borde:      #d2d8e0;
  --borde-2:    #e3e7ec;
  --ao:         #1e4fa8;
  --ao-suave:   #e7edf9;
  --aka:        #a5182b;
  --aka-suave:  #fbeaec;
  --sombra:     0 1px 2px rgba(15,22,32,.05), 0 8px 24px -12px rgba(15,22,32,.16);
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --papel:     #0c1016;
    --hoja:      #ffffff;
    --panel:     #141a23;
    --tinta:     #e7ebf1;
    --tinta-2:   #9aa5b4;
    --tinta-3:   #6d7784;
    --borde:     #242c38;
    --borde-2:   #1c232d;
    --ao:        #78a5f0;
    --ao-suave:  #16233a;
    --aka:       #ef7f8f;
    --aka-suave: #2d1620;
    --sombra:    0 1px 2px rgba(0,0,0,.4), 0 10px 30px -14px rgba(0,0,0,.7);
  }}
}}
:root[data-theme="dark"] {{
  --papel:     #0c1016;
  --hoja:      #ffffff;
  --panel:     #141a23;
  --tinta:     #e7ebf1;
  --tinta-2:   #9aa5b4;
  --tinta-3:   #6d7784;
  --borde:     #242c38;
  --borde-2:   #1c232d;
  --ao:        #78a5f0;
  --ao-suave:  #16233a;
  --aka:       #ef7f8f;
  --aka-suave: #2d1620;
  --sombra:    0 1px 2px rgba(0,0,0,.4), 0 10px 30px -14px rgba(0,0,0,.7);
}}

* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--papel);
  color: var(--tinta);
  font-family: "Newsreader", Georgia, serif;
  font-size: 17px;
  line-height: 1.62;
  -webkit-font-smoothing: antialiased;
}}
.envoltura {{ max-width: 1240px; margin: 0 auto; padding: 0 28px 96px; }}

h1, h2, h3, h4, .cartela, .eyebrow {{ font-family: "Archivo", "Helvetica Neue", sans-serif; }}
code, .mono {{ font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: .86em; }}
code {{ background: var(--panel); border: 1px solid var(--borde-2); border-radius: 3px; padding: .08em .34em; }}

/* ---------- portada ---------- */
header.portada {{
  padding: 64px 0 40px;
  border-bottom: 2px solid var(--tinta);
  margin-bottom: 8px;
}}
.marca {{
  display: flex; align-items: baseline; gap: 14px;
  font-family: "IBM Plex Mono", monospace; font-size: 11.5px;
  letter-spacing: .16em; text-transform: uppercase; color: var(--tinta-3);
  margin-bottom: 26px;
}}
.marca .aka {{ color: var(--aka); }}
.marca .ao  {{ color: var(--ao); }}
h1 {{
  font-size: clamp(2.3rem, 5.6vw, 4rem); font-weight: 700; line-height: 1.02;
  letter-spacing: -.024em; margin: 0 0 20px; text-wrap: balance; max-width: 20ch;
}}
.bajada {{ font-size: 1.2rem; color: var(--tinta-2); max-width: 62ch; margin: 0 0 34px; }}
.bajada strong {{ color: var(--tinta); font-weight: 500; }}
.ficha {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
  gap: 1px; background: var(--borde); border: 1px solid var(--borde);
  border-radius: 5px; overflow: hidden;
}}
.ficha div {{ background: var(--panel); padding: 13px 16px; }}
.ficha dt {{
  font-family: "IBM Plex Mono", monospace; font-size: 10px; letter-spacing: .13em;
  text-transform: uppercase; color: var(--tinta-3); margin-bottom: 5px;
}}
.ficha dd {{ margin: 0; font-size: .95rem; font-weight: 500; font-variant-numeric: tabular-nums; }}

/* ---------- índice ---------- */
nav.indice {{ margin: 44px 0 18px; }}
nav.indice ol {{
  list-style: none; margin: 0; padding: 0;
  display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px;
}}
nav.indice a {{
  display: flex; gap: 12px; align-items: baseline; text-decoration: none;
  color: var(--tinta); background: var(--panel);
  border: 1px solid var(--borde); border-left: 3px solid var(--ao);
  border-radius: 4px; padding: 12px 15px; transition: background .16s, transform .16s;
}}
nav.indice a:hover {{ background: var(--ao-suave); transform: translateY(-1px); }}
nav.indice a:focus-visible {{ outline: 2px solid var(--ao); outline-offset: 2px; }}
nav.indice .n {{ font-family: "IBM Plex Mono", monospace; font-size: .8rem; color: var(--ao); font-weight: 500; }}
nav.indice .t {{ font-family: "Archivo", sans-serif; font-size: .95rem; font-weight: 500; }}

/* ---------- bloque de aviso ---------- */
.aviso {{
  border: 1px solid var(--borde); border-left: 3px solid var(--aka);
  background: var(--panel); border-radius: 4px; padding: 20px 24px; margin: 34px 0 0;
}}
.aviso h3 {{ margin: 0 0 8px; font-size: 1rem; font-weight: 600; }}
.aviso p {{ margin: 0 0 10px; color: var(--tinta-2); font-size: .98rem; }}
.aviso p:last-child {{ margin-bottom: 0; }}

/* ---------- láminas ---------- */
.lamina {{ margin-top: 76px; scroll-margin-top: 20px; }}
.cartela {{
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 18px;
  border: 1px solid var(--tinta); border-bottom: none;
  background: var(--tinta); color: var(--papel);
  padding: 11px 18px; border-radius: 5px 5px 0 0;
}}
.cartela-num {{
  font-family: "IBM Plex Mono", monospace; font-size: .82rem; font-weight: 500;
  letter-spacing: .06em; padding: 2px 8px; border-radius: 3px;
  background: var(--papel); color: var(--tinta);
}}
.cartela-tit {{ font-size: 1.02rem; font-weight: 600; letter-spacing: -.008em; }}
.cartela-meta {{ font-size: .82rem; opacity: .74; font-family: "IBM Plex Mono", monospace; }}
.cartela-src {{
  margin-left: auto; font-size: .74rem; opacity: .62; background: none;
  border: none; padding: 0; color: inherit;
}}
.hoja-envoltura {{
  border: 1px solid var(--tinta); border-radius: 0 0 5px 5px;
  background: var(--hoja); overflow-x: auto; box-shadow: var(--sombra);
}}
.hoja {{ min-width: 660px; padding: 18px; }}
.hoja svg {{ display: block; width: 100%; height: auto; }}

/* ---------- prosa de la lámina ---------- */
.prosa {{ margin-top: 40px; max-width: 74ch; }}
.eyebrow {{
  font-size: 10.5px; letter-spacing: .17em; text-transform: uppercase;
  color: var(--tinta-3); font-weight: 600; margin: 0 0 16px;
  padding-bottom: 7px; border-bottom: 1px solid var(--borde);
}}
.lecturas {{ list-style: none; margin: 0 0 42px; padding: 0; display: grid; gap: 22px; }}
.lecturas h4 {{ margin: 0 0 5px; font-size: 1rem; font-weight: 600; letter-spacing: -.006em; }}
.lecturas p {{ margin: 0; color: var(--tinta-2); }}
.lecturas > li {{ padding-left: 18px; border-left: 2px solid var(--ao-suave); }}

.defensa {{ display: grid; gap: 10px; }}
details {{
  border: 1px solid var(--borde); border-radius: 4px;
  background: var(--panel); overflow: hidden;
}}
details[open] {{ border-color: var(--aka); }}
summary {{
  cursor: pointer; padding: 14px 18px; font-family: "Archivo", sans-serif;
  font-size: .96rem; font-weight: 500; list-style: none; display: flex; gap: 12px;
}}
summary::-webkit-details-marker {{ display: none; }}
summary::before {{
  content: "P"; font-family: "IBM Plex Mono", monospace; font-size: .78rem;
  color: var(--aka); font-weight: 500; flex-shrink: 0; padding-top: 1px;
}}
summary:focus-visible {{ outline: 2px solid var(--aka); outline-offset: -2px; }}
.respuesta {{ padding: 0 18px 16px 48px; border-top: 1px solid var(--borde-2); padding-top: 14px; }}
.respuesta p {{ margin: 0; color: var(--tinta-2); font-size: .98rem; }}

/* ---------- decisión / pendientes ---------- */
.cierre {{ margin-top: 92px; padding-top: 44px; border-top: 2px solid var(--tinta); }}
.cierre h2 {{ font-size: clamp(1.5rem, 3vw, 2.1rem); font-weight: 700; letter-spacing: -.02em; margin: 0 0 18px; text-wrap: balance; }}
.cierre h3 {{ font-size: 1.06rem; font-weight: 600; margin: 32px 0 10px; }}
.cierre p, .cierre li {{ color: var(--tinta-2); max-width: 74ch; }}
.cierre p {{ margin: 0 0 14px; }}
.cierre ul {{ padding-left: 22px; margin: 0 0 16px; }}
.cierre li {{ margin-bottom: 9px; }}
.cierre strong {{ color: var(--tinta); font-weight: 500; }}

pre {{
  background: var(--panel); border: 1px solid var(--borde); border-left: 3px solid var(--ao);
  border-radius: 4px; padding: 16px 18px; overflow-x: auto; margin: 0 0 18px;
  font-family: "IBM Plex Mono", monospace; font-size: 13px; line-height: 1.6; color: var(--tinta);
}}
.pendientes {{ list-style: none; padding: 0; display: grid; gap: 12px; margin: 0; }}
.pendientes li {{
  display: flex; gap: 14px; padding: 14px 17px; background: var(--panel);
  border: 1px solid var(--borde); border-left: 3px solid var(--aka); border-radius: 4px;
  margin: 0; max-width: none;
}}
.pendientes .marca-p {{
  font-family: "IBM Plex Mono", monospace; font-size: .74rem; color: var(--aka);
  letter-spacing: .08em; flex-shrink: 0; padding-top: 3px; text-transform: uppercase;
}}
.pendientes b {{ color: var(--tinta); font-weight: 500; }}

footer {{
  margin-top: 72px; padding-top: 22px; border-top: 1px solid var(--borde);
  font-family: "IBM Plex Mono", monospace; font-size: 11.5px; color: var(--tinta-3);
  display: flex; flex-wrap: wrap; gap: 8px 24px; letter-spacing: .04em;
}}
@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; animation: none !important; }}
}}
@media (max-width: 640px) {{
  .envoltura {{ padding: 0 16px 64px; }}
  header.portada {{ padding-top: 40px; }}
  .cartela-src {{ margin-left: 0; }}
  .hoja {{ padding: 10px; }}
}}
</style>

<div class="envoltura">

<header class="portada">
  <div class="marca">
    <span>Capítulo 3 · sección 3.7</span>
    <span class="ao">ao</span><span class="aka">aka</span>
    <span>Holweger Puerto · 1290-22-2830</span>
  </div>
  <h1>Láminas del Sistema Experto</h1>
  <p class="bajada">
    Los cuatro diagramas de la sección 3.7, generados <strong>desde el código real del repositorio</strong> y no
    dibujados aparte. Cada lámina va acompañada de las decisiones de ingeniería que representa y de las preguntas
    de terna que más probablemente dispare.
  </p>
  <dl class="ficha">
    <div><dt>Actualizado</dt><dd>23 ago 2026</dd></div>
    <div><dt>Láminas</dt><dd>4 de 4</dd></div>
    <div><dt>Clases documentadas</dt><dd>15</dd></div>
    <div><dt>Suite de pruebas</dt><dd>21 / 21</dd></div>
    <div><dt>Formato</dt><dd>SVG vectorial</dd></div>
  </dl>

  <nav class="indice" aria-label="Índice de láminas">
    <ol>
      <li><a href="#s371"><span class="n">3.7.1</span><span class="t">Casos de uso</span></a></li>
      <li><a href="#s372"><span class="n">3.7.2</span><span class="t">Entidad-relación</span></a></li>
      <li><a href="#s373"><span class="n">3.7.3</span><span class="t">Clases</span></a></li>
      <li><a href="#s374"><span class="n">3.7.4</span><span class="t">Despliegue físico</span></a></li>
    </ol>
  </nav>

  <div class="aviso">
    <h3>Cómo llevarlas al documento de Word</h3>
    <p>
      Word 2016 y posteriores insertan SVG como vector: <code>Insertar › Imágenes › Este dispositivo…</code> y elegir
      el <code>.svg</code>. No se pixela al ampliar ni al imprimir, y el texto interno queda nítido a cualquier tamaño.
    </p>
    <p>
      Los cuatro archivos están en <code>diagramas/</code> del repositorio, junto al script que los produce. Si el código
      cambia, se edita el script y se regenera — así el diagrama no queda desfasado respecto al repositorio, que es la
      contradicción más fácil de detectar en una defensa.
    </p>
  </div>
</header>

{"".join(bloque_lamina(l) for l in LAMINAS)}

<section class="cierre">
  <h2>La decisión que el 3.7.2 desbloquea: alcance del RF-08</h2>
  <p>
    El 22 de agosto quedó pendiente decidir cuánto de la edición de umbrales se construye ahora, precisamente porque esa
    forma se define en el modelo de datos. Con el diagrama en la mano, la recomendación es <strong>construir la tabla y la
    lectura ahora, y la pantalla de edición como una vista simple</strong> — no un sistema de versionado de umbrales.
  </p>

  <h3>Lo que sí entra</h3>
  <ul>
    <li>La tabla <code>umbral_referencia</code> con <code>fuente</code> ∈ <code>{{'literatura', 'modelado_experto'}}</code>, sembrada con los valores que hoy están escritos a mano en <code>knowledge_base.py</code>.</li>
    <li>La columna <code>id_umbral</code> en <code>tecnica_evaluada</code>, con la misma migración idempotente que ya usaste para <code>correcto</code> (<code>PRAGMA table_info</code> + <code>ALTER TABLE</code> solo si falta).</li>
    <li>Carga de umbrales al arrancar: <code>KarateRules</code> deja de leer constantes del módulo y recibe el diccionario cargado de la base de datos.</li>
    <li>Una pantalla de umbrales en la GUI, visible solo con sesión de entrenador iniciada — que es exactamente lo que pide el RF-08.</li>
  </ul>

  <h3>Lo que no entra</h3>
  <ul>
    <li>Historial de versiones de cada umbral con fechas de vigencia. El <code>id_umbral</code> en cada medición ya da trazabilidad suficiente sin construir un sistema temporal completo.</li>
    <li>Edición de los umbrales de la máquina de estados (<code>UMBRAL_CARGA</code>, timeouts). Son parámetros de detección de fase, no criterios de calidad técnica: exponerlos a un entrenador invita a romper la detección sin que nadie entienda por qué.</li>
  </ul>

  <h3>Por qué esta tabla vale más que el RF-08</h3>
  <p>
    Hay una brecha en el capítulo que esta tabla cierra de paso. La sección “Estrategia de recolección inicial de datos”
    promete que los umbrales salen de <em>promediar ejecuciones de cinturones negros</em>. Hoy salen de la literatura y de tu
    criterio como practicante — que es legítimo, pero no es lo que el texto afirma. El campo <code>fuente</code> permite que
    ambas cosas sean verdad sin contradicción: el sistema arranca con <code>'literatura'</code> y cada umbral migra a
    <code>'modelado_experto'</code> cuando esa medición exista. El capítulo deja de prometer un pasado que no ocurrió y pasa a
    describir un mecanismo que sí existe.
  </p>

  <h3>Sigue pendiente en el capítulo</h3>
  <ul class="pendientes">
    <li><span class="marca-p">Redacción</span><span><b>La frase que formaliza “funciona con o sin IMU”.</b> Los RF-02 y RF-04 ya la insinúan en su descripción, pero el RNF-03 sigue enunciando la fusión sensorial como si fuera obligatoria. Quedó abierta desde el 22 de agosto.</span></li>
    <li><span class="marca-p">Documento</span><span><b>Los cuatro subtítulos de 3.7 están vacíos en el .docx.</b> Solo existen los encabezados; falta insertar las láminas y el párrafo introductorio de cada una.</span></li>
    <li><span class="marca-p">Dato</span><span><b>El Modelado del Experto no se ha ejecutado.</b> La tabla lo deja representable, pero no hay ni una medición de cinturón negro capturada todavía. Es lo que le da sentido al campo <code>fuente</code>.</span></li>
    <li><span class="marca-p">Código</span><span><b>Cinco archivos modificados y cuatro sin trackear siguen fuera de git,</b> incluidos <code>persistence/medicion_logger.py</code> y <code>persistence/reportes.py</code>. Todo el trabajo de la Semana 3 vive solo en el disco local.</span></li>
  </ul>
</section>

<footer>
  <span>Sistema experto de análisis biomecánico · Karate Do Sacatepéquez</span>
  <span>Diagramas generados con <code>diagramas/*.py</code></span>
  <span>Azul: implementado · Gris punteado: planificado</span>
</footer>

</div>
'''

os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
open(SALIDA, "w", encoding="utf-8").write(HTML)
print(SALIDA, len(HTML), "bytes")
