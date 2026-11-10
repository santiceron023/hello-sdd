# Tareas 001: MVP de habits-cli

- **Spec:** `specs/001-habits-mvp/spec.md`
- **Plan:** `specs/001-habits-mvp/plan.md`

## Cómo trabajar estas tareas

- Haz las tareas en orden: cada una depende solo de las anteriores.
- Ninguna tarea debería llevar más de 20–30 minutos.
- En cada tarea, escribe primero el test y después el código que lo hace pasar
  (constitución, principio 4).
- Al cerrar cualquier tarea, `python -m unittest discover` debe pasar y no debe
  quedar ningún test en rojo.

## Fase 0: Preparación (bloquea la implementación)

- [x] **T01. Cerrar las dudas abiertas en la spec.**
  Incorporar a `spec.md` las resoluciones de D-1…D-4 propuestas en la sección 7
  del plan, o las que decida el usuario. Requiere petición explícita, porque
  `AGENTS.md` prohíbe tocar `specs/` sin ella.
  - **Cubre:** RF-1 (D-1), RF-4 (CA-4.4 / D-2), CL-15 (D-3) y RF-5/RF-7
    (D-4).
  - **Hecho cuando:** `grep -c "NECESITA ACLARACIÓN" specs/001-habits-mvp/spec.md`
    devuelve 0.

- [x] **T02. Alinear `AGENTS.md` con la constitución.**
  Cambiar Python 3.12+ por 3.11+ y declarar `python -m unittest discover` como
  verificación principal. `pytest -q` queda como alternativa.
  - **Cubre:** ningún RF; elimina la contradicción con la constitución.
  - **Hecho cuando:** `AGENTS.md` ya no contradice ningún principio de
    `docs/CONSTITUTION.md`.

- [x] **T03. Esqueleto del paquete y de los tests.**
  Crear:
  - `habits/__init__.py` vacío;
  - `tests/__init__.py`;
  - `tests/test_core.py`, `tests/test_storage.py` y `tests/test_cli.py`, cada
    uno con un `TestCase` vacío.
  - **Cubre:** infraestructura (constitución, principio 4).
  - **Hecho cuando:** `python -m unittest discover` termina con `OK` y
    `Ran 0 tests`.

## Fase 1: Dominio puro (`habits/core.py`)

- [x] **T04. Modelo `Habit` y excepciones de dominio.**
  Crear:
  - la dataclass `Habit` con `name: str` y `done_dates: set[date]`;
  - `HabitError` y sus subclases `EmptyNameError`, `DuplicateHabitError` y
    `HabitNotFoundError`. Cada excepción guarda el nombre afectado y no
    contiene textos para el usuario.
  - **Cubre:** base de RF-1…RF-7 (DT-9).
  - **Hecho cuando:**
    - un test crea un `Habit` y comprueba que las excepciones heredan de
      `HabitError`;
    - `grep -E "argparse|print\(|sys.argv" habits/core.py` no devuelve nada.

- [x] **T05. Normalización y clave de nombre.**
  `normalize_name` recorta espacios y lanza `EmptyNameError` si el nombre queda
  vacío. `name_key` devuelve el `casefold()` del nombre.
  - **Cubre:** RF-1 (CA-1.1, CA-1.2, CA-1.4), CL-6 y CL-7.
  - **Hecho cuando:** pasan los tests de:
    - `"  Leer "` → `"Leer"`;
    - `"   "` → `EmptyNameError`;
    - `name_key("Leer") == name_key("LEER")`;
    - `name_key("Straße") == name_key("STRASSE")`.

- [x] **T06. `find_habit` y `add_habit`.**
  `find_habit` busca por `name_key` y lanza `HabitNotFoundError` si no
  encuentra el hábito. `add_habit` normaliza el nombre, rechaza duplicados con
  `DuplicateHabitError` y conserva las mayúsculas originales.
  - **Cubre:** RF-1 (CA-1.3), RF-2 (CA-2.1, CA-2.2) y CL-5.
  - **Hecho cuando:** pasan los tests de:
    - crear «Leer» → hábito sin fechas con el nombre `"Leer"`;
    - crear «leer» con «Leer» existente → `DuplicateHabitError` y la lista no
      cambia;
    - buscar un nombre inexistente → `HabitNotFoundError`.

- [x] **T07. `mark_done`.**
  Recibe `today` como parámetro, añade la fecha y devuelve `True`. Si ya estaba
  marcado ese día, devuelve `False` sin cambiar nada. Si el hábito no existe,
  lanza `HabitNotFoundError` sin crear nada.
  - **Cubre:** RF-3 (CA-3.1, CA-3.2, CA-3.3, CA-3.4), CL-3 y CL-4.
  - **Hecho cuando:** pasan los tests de:
    - primer marcado → `True` y la fecha está en el conjunto;
    - segundo marcado del mismo día → `False` y el conjunto no cambia;
    - hábito inexistente → error y `len(habits)` no cambia.

- [x] **T08. `rename_habit`.**
  Valida los dos nombres antes de mutar nada.
  - Si el origen no existe → `HabitNotFoundError`.
  - Si el destino pertenece a otro hábito → `DuplicateHabitError`.
  - Si el nuevo nombre queda vacío → `EmptyNameError`.
  - Un cambio solo de mayúsculas se permite según lo que decida T01.
  - Las fechas se conservan.
  - **Cubre:** RF-4 (CA-4.1, CA-4.2, CA-4.3, CA-4.4), CL-8 y CL-9.
  - **Hecho cuando:** pasan los tests de los cuatro casos de error y éxito, y
    del cambio solo de mayúsculas. En cada error, la lista queda idéntica.

- [x] **T09. `current_streak`: casos básicos.**
  Implementar el algoritmo de la sección 3 del plan.
  - **Cubre:** RF-6 (CA-6.1, CA-6.2, CA-6.3), CL-1 y CL-2.
  - **Hecho cuando:** pasan los tests de una tabla de casos con hoy =
    miércoles 2026-11-11:
    - sin marcas → 0;
    - solo hoy → 1;
    - lunes y martes → 2;
    - lunes, martes y miércoles → 3;
    - última marca el lunes → 0.

- [x] **T10. `current_streak`: casos límite y rendimiento.**
  - **Cubre:** RF-6 (CA-6.4), CL-11, CL-12, CL-15 y RNF-6.
  - **Hecho cuando:** pasan los tests de:
    - hueco en el historial → solo cuenta el tramo final;
    - fecha repetida → cuenta una vez;
    - fecha futura → se ignora;
    - 100 hábitos con 5 años de marcas cada uno → se calculan en menos de 1 s.

- [x] **T11. `is_done_on` y `sorted_habits`.**
  - **Cubre:** RF-5 (CA-5.1 ✓/✗, CA-5.2).
  - **Hecho cuando:** pasan los tests de:
    - `is_done_on` devuelve `True` o `False` según la fecha;
    - `["yoga", "Leer", "árbol"]` se ordena por `casefold()` de forma estable y
      determinista.

## Fase 2: Persistencia (`habits/storage.py`)

- [x] **T12. `default_path` y `load` sin archivo.**
  `default_path` usa `HABITS_FILE` si está definida; si no, `~/habits.json`.
  `load` devuelve `[]` si el archivo no existe.
  - **Cubre:** RNF-1 y RNF-3.
  - **Hecho cuando:** pasan los tests de:
    - con `HABITS_FILE` → se usa esa ruta;
    - sin la variable → `Path.home() / "habits.json"`;
    - `load` de una ruta inexistente en un directorio temporal → `[]`.

- [x] **T13. `save` y `load`: ida y vuelta.**
  El JSON se guarda con `version: 1`, `indent=2` y `ensure_ascii=False`, y con
  las fechas ordenadas y sin duplicados.
  - **Cubre:** RNF-1, RNF-2, CA-1.3 y CA-6.4.
  - **Hecho cuando:** pasan los tests de:
    - `save` seguido de `load` devuelve hábitos iguales;
    - el archivo contiene `"Repasar inglés"` literal, sin `é`;
    - las fechas aparecen en orden ascendente.

- [x] **T14. Validación de datos corruptos.**
  `load` lanza `CorruptDataError` en cada regla de la sección 2.2 del plan y
  tolera fechas repetidas y futuras.
  - **Cubre:** RNF-4, CL-12, CL-13 y CL-15.
  - **Hecho cuando:**
    - hay un test por regla: JSON inválido, raíz no objeto, sin `habits`,
      versión ≠ 1, nombre vacío, fecha inválida y nombres duplicados;
    - el contenido del archivo es idéntico antes y después de cada caso.

- [x] **T15. Escritura atómica.**
  `save` escribe en un archivo temporal del mismo directorio y lo sustituye
  con `os.replace`.
  - **Cubre:** RNF-5.
  - **Hecho cuando:**
    - un test parchea `os.replace` para que falle, comprueba que el
      `habits.json` previo queda intacto y que no queda ningún archivo
      temporal.

## Fase 3: Interfaz (`habits/cli.py`, `habits/__main__.py`)

- [x] **T16. Parser en español y errores de uso.**
  Crear:
  - una subclase de `ArgumentParser` con `error()` en español y código de
    salida 2;
  - los subcomandos `crear`, `hecho`, `renombrar` y `listar`;
  - `main(argv, *, today=None, data_path=None) -> int`.
  - **Cubre:** RF-7 (CA-7.1, CA-7.2).
  - **Hecho cuando:** pasan los tests de:
    - `main(["volar"])` y `main(["crear"])` devuelven 2;
    - stderr contiene `uso:` y `Error:` y no contiene `usage:` ni
      `error: the following`.

- [x] **T17. Comando `crear`.**
  - **Cubre:** RF-2 (CA-2.1, CA-2.2) y RF-1 (CA-1.4) desde la CLI.
  - **Hecho cuando:** pasan los tests de:
    - éxito → stdout `Hábito «Leer» creado.`, código 0 y el hábito está
      guardado en disco;
    - duplicado → stderr `Error: ya existe el hábito «Leer».` y código 1;
    - nombre vacío → mensaje de la tabla 4.1 y código 1.

- [x] **T18. Comando `hecho`.**
  `main` lee la fecha de hoy una sola vez y solo guarda si hubo cambio.
  - **Cubre:** RF-3 (CA-3.1…CA-3.4), CL-3, CL-4 y CL-14.
  - **Hecho cuando:** pasan los tests de los tres mensajes de la tabla 4.1 con
    sus códigos y flujos de salida. En el caso «ya marcado», la fecha de
    modificación del archivo no cambia.

- [x] **T19. Comando `renombrar`.**
  - **Cubre:** RF-4 (CA-4.1…CA-4.4), CL-8 y CL-9.
  - **Hecho cuando:**
    - pasan los tests de las cuatro filas de la tabla 4.1;
    - tras renombrar, `listar` muestra la misma racha con el nombre nuevo.

- [x] **T20. Comando `listar`.**
  Imprime el formato de la sección 4.2 del plan: ✓/✗, nombre alineado y
  «racha: N día/días».
  - **Cubre:** RF-5 (CA-5.1, CA-5.2, CA-5.3), RF-6 integrado y CL-10.
  - **Hecho cuando:** pasan los tests de:
    - la salida exacta de un ejemplo con tres hábitos, incluido el singular
      «1 día»;
    - sin hábitos → `No existen hábitos` y código 0;
    - `listar` nunca escribe el archivo.

- [x] **T21. Datos corruptos desde la CLI.**
  `main` captura `CorruptDataError`, imprime el mensaje en stderr y devuelve 1.
  - **Cubre:** RNF-4 y CL-13.
  - **Hecho cuando:** con un `habits.json` inválido, todos los comandos
    devuelven 1, el mensaje empieza por
    `Error: no se puede leer el archivo de hábitos` y el archivo no cambia.

- [x] **T22. Punto de entrada `python -m habits`.**
  `habits/__main__.py` llama a `sys.exit(main())`.
  - **Cubre:** RNF-1 y el contrato de invocación de la sección 4 del plan.
  - **Hecho cuando:** un test con `subprocess` ejecuta
    `python -m habits listar` con `HABITS_FILE` en un directorio temporal y
    obtiene `No existen hábitos` y código 0.

## Fase 4: Cierre

- [x] **T23. Trazabilidad y criterios de finalización.**
  Revisar que cada CA (RF-1…RF-7) y cada CL-1…CL-15 tengan al menos un test
  cuyo nombre incluya su identificador (por ejemplo, `..._ca_3_2`, `..._cl_11`).
  - **Cubre:** sección 8 de la spec (criterios de finalización) y RNF-7.
  - **Hecho cuando:**
    - un `grep` de cada identificador en `tests/` encuentra al menos un test;
    - `grep -rn "date.today" habits/core.py tests/` no devuelve nada.

- [x] **T24. Verificación final.**
  - **Cubre:** todos los RF y RNF.
  - **Hecho cuando:**
    - `python -m unittest discover` y `pytest -q` terminan en verde;
    - una prueba manual de `crear` → `hecho` → `listar` → `renombrar` →
      `listar` con `HABITS_FILE` temporal da las salidas de la tabla 4.1 del
      plan.
