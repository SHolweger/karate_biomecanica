"""
Nombre legible de una cámara del sistema.

OpenCV identifica los dispositivos solo por un número, y «Cámara 0 · 1280x720»
no le dice a un instructor cuál de las tres que tiene conectadas es. El nombre
hay que pedírselo al sistema operativo, y cada uno lo expone a su manera.

El análisis de la respuesta vive separado de la llamada al sistema para poder
verificarlo en la integración continua, donde no hay cámaras que enumerar.

Nada de esto es indispensable: si el sistema no da nombres, la pantalla de
cámaras se queda con el índice, la resolución y la miniatura, que ya bastan para
distinguirlas. Por eso ningún fallo aquí interrumpe la enumeración.
"""
import json
import platform
import subprocess

# El sondeo no debe colgar la interfaz: si el sistema tarda más que esto en
# responder, se sigue sin nombres.
TIEMPO_LIMITE_S = 4


def analizar_salida_macos(texto_json):
    """
    Nombres de cámara a partir de `system_profiler SPCameraDataType -json`.

    Devuelve la lista en el orden en que el sistema las reporta, que es el mismo
    en que AVFoundation las numera.
    """
    try:
        datos = json.loads(texto_json)
    except (ValueError, TypeError):
        return []

    camaras = datos.get("SPCameraDataType") or []
    nombres = []
    for camara in camaras:
        if not isinstance(camara, dict):
            continue
        nombre = camara.get("_name") or camara.get("spcamera_model-id")
        if nombre:
            nombres.append(str(nombre).strip())
    return nombres


def analizar_nombre_v4l2(texto):
    """Nombre de `/sys/class/video4linux/videoN/name`, sin el salto final."""
    return (texto or "").strip() or None


def _nombres_macos():
    salida = subprocess.run(
        ["system_profiler", "SPCameraDataType", "-json"],
        capture_output=True, text=True, timeout=TIEMPO_LIMITE_S, check=False)
    return analizar_salida_macos(salida.stdout)


def _nombre_linux(indice):
    # En Linux el índice de OpenCV corresponde a /dev/videoN, así que la
    # asociación es directa y no hay que adivinarla.
    try:
        with open(f"/sys/class/video4linux/video{indice}/name", encoding="utf-8") as archivo:
            return analizar_nombre_v4l2(archivo.read())
    except OSError:
        return None


def nombres_del_sistema(indices):
    """
    Nombre por índice, como dict. Los índices sin nombre no aparecen.

    Cualquier fallo devuelve un diccionario vacío: quedarse sin nombres degrada
    la pantalla, pero un error aquí no puede impedir que el entrenador elija su
    cámara.
    """
    sistema = platform.system()
    try:
        if sistema == "Darwin":
            nombres = _nombres_macos()
            return {indice: nombres[indice] for indice in indices
                    if 0 <= indice < len(nombres)}
        if sistema == "Linux":
            encontrados = {}
            for indice in indices:
                nombre = _nombre_linux(indice)
                if nombre:
                    encontrados[indice] = nombre
            return encontrados
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}
    return {}
