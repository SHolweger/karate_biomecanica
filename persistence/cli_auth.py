import getpass


def login_o_registro(db):
    """
    Flujo de consola para autenticar a un entrenador (RF-08). Si es la
    primera vez que se usa el sistema (no hay ningún entrenador registrado),
    ofrece crear la primera cuenta. Devuelve el dict del entrenador
    autenticado.

    Esta es una capa de UI temporal: cuando llegue la GUI (Sprint 3,
    CustomTkinter), solo se reemplaza este archivo — la lógica de
    autenticación en database.py no cambia.
    """
    print("\n=== SHOTOKAN AI — Acceso de entrenador ===")

    if not db.existe_algun_entrenador():
        print("No hay entrenadores registrados todavía. Vamos a crear el primero.")
        return _registrar_entrenador(db, rol="principal")

    while True:
        usuario = input("Usuario: ").strip()
        password = getpass.getpass("Contraseña: ")
        entrenador = db.autenticar_entrenador(usuario, password)
        if entrenador is not None:
            print(f"Bienvenido, {entrenador['nombre']} ({entrenador['rol']}).")
            return entrenador

        opcion = input("Usuario o contraseña incorrectos. ¿Reintentar (r) o crear cuenta nueva (n)? ").strip().lower()
        if opcion == "n":
            return _registrar_entrenador(db, rol="sensei")


def _registrar_entrenador(db, rol):
    nombre = input("Nombre completo: ").strip()
    usuario = input("Nombre de usuario: ").strip()
    correo = input("Correo: ").strip()
    password = getpass.getpass("Contraseña: ")
    db.crear_entrenador(nombre, usuario, correo, password, rol=rol)
    print(f"Cuenta creada. Bienvenido, {nombre}.")
    return db.autenticar_entrenador(usuario, password)


def elegir_o_crear_perfil(db):
    """
    Selección de perfil de atleta al estilo Netflix: lista los atletas ya
    registrados y permite elegir uno o crear un perfil nuevo. A diferencia
    del login del entrenador, esto NO es control de acceso (sin contraseña):
    solo responde "a quién pertenece esta sesión de medición".
    """
    atletas = db.listar_atletas()

    print("\n=== ¿Quién entrena hoy? ===")
    for i, atleta in enumerate(atletas, start=1):
        print(f"  {i}. {atleta['nombre']}")
    print(f"  {len(atletas) + 1}. + Agregar perfil nuevo")

    while True:
        opcion = input("Elige un número: ").strip()
        if not opcion.isdigit():
            print("Ingresa un número válido.")
            continue
        opcion = int(opcion)
        if 1 <= opcion <= len(atletas):
            return atletas[opcion - 1]
        if opcion == len(atletas) + 1:
            return _crear_perfil_atleta(db)
        print("Opción fuera de rango.")


def _crear_perfil_atleta(db):
    nombre = input("Nombre del nuevo atleta: ").strip()
    grado = input("Grado (kyu/dan, opcional, Enter para omitir): ").strip() or None
    id_atleta = db.crear_atleta(nombre, grado_cinturon=grado)
    return {"id_atleta": id_atleta, "nombre": nombre, "grado_cinturon": grado}
