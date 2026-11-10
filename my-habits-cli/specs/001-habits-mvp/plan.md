# Plan técnico 001: MVP de habits-cli

- **Spec:** `specs/001-habits-mvp/spec.md`
- **Constitución:** `docs/CONSTITUTION.md`
- **Estado:** borrador
- **Fecha:** 2026-11-09

## 0. Restricciones de partida

- **Constitución.** Python 3.11+ y solo la biblioteca estándar. Lógica separada
  de la interfaz. Tests con `unittest`. Datos en un único `habits.json` con
  fechas ISO-8601. Identificadores en inglés y textos visibles en español.
- **Contradicción con `AGENTS.md`.** `AGENTS.md` dice Python 3.12+ y pytest; la
  constitución dice 3.11+ y `unittest`. Prevalece la constitución. Para
  satisfacer ambas:
  - El código usará solo sintaxis compatible con 3.11, que también funciona
    en 3.12.
  - Los tests se escribirán con `unittest`. `pytest -q` también los ejecuta, así
    que las dos órdenes de verificación funcionan.
  - Se propone corregir `AGENTS.md` en una tarea aparte.
- **Dudas abiertas de la spec (D-1…D-4).** Este plan propone una resolución
  provisional para cada una en la sección 7. Por el principio 2 de la
  constitución, no se implementará ninguna hasta que la spec la recoja.

## 1. Estructura de módulos

```
habits/
  __init__.py     vacío; marca el paquete
  __main__.py     punto de entrada de `python -m habits`; delega en cli.main
  core.py         dominio puro: modelo, reglas de nombre, registro, renombrado, racha
  storage.py      lectura, validación y escritura atómica de habits.json
  cli.py          argparse, textos en español, códigos de salida
tests/
  __init__.py
  test_core.py    reglas de nombre, registro, renombrado y racha
  test_storage.py persistencia, primer uso, corrupción y atomicidad
  test_cli.py     contrato: salidas, stderr y códigos de salida
```

**Dependencias permitidas:**
- `cli` depende de `core` y `storage`.
- `storage` depende de `core` (solo del modelo).
- `core` no depende de nadie.

`core` no importa `argparse`, no llama a `print` y no lee `sys.argv`
(constitución, principio 3).

### 1.1 Responsabilidades de `core` (RF-1 a RF-6)

| Elemento | Responsabilidad | RF |
|---|---|---|
| `Habit` (dataclass) | `name: str` (como se escribió) y `done_dates: set[date]` | todos |
| `normalize_name(raw)` | Recorta espacios; si queda vacío lanza `EmptyNameError` | RF-1 (CA-1.1, 1.4) |
| `name_key(name)` | Clave de comparación: `casefold()` del nombre ya normalizado | RF-1 (CA-1.2) |
| `find_habit(habits, name)` | Busca por clave; lanza `HabitNotFoundError` si no existe | RF-3.3, RF-4.2 |
| `add_habit(habits, raw_name)` | Crea el hábito sin fechas; lanza `DuplicateHabitError` si ya existe | RF-2 |
| `mark_done(habits, raw_name, today)` | Añade `today`; devuelve si hubo cambio (`False` si ya estaba marcado) | RF-3 |
| `rename_habit(habits, old, new)` | Cambia el nombre y conserva las fechas; lanza `DuplicateHabitError` si el nuevo nombre es de otro hábito | RF-4 |
| `current_streak(habit, today)` | Algoritmo de la sección 3 | RF-6 |
| `is_done_on(habit, day)` | Indica si la fecha está registrada | RF-5 (✓/✗) |
| `sorted_habits(habits)` | Ordena por `name_key` | RF-5 (CA-5.2) |
| Excepciones | `HabitError` y sus subclases `EmptyNameError`, `DuplicateHabitError`, `HabitNotFoundError` | RF-7 |

Detalles comunes:
- Todas las funciones que dependen de la fecha reciben `today` como parámetro.
  Ninguna llama a `date.today()` (RNF-7).
- Las funciones operan sobre una lista de `Habit` y devuelven datos. No generan
  textos para el usuario.

### 1.2 Responsabilidades de `storage` (RNF-1 a RNF-5)

| Elemento | Responsabilidad | RNF/RF |
|---|---|---|
| `default_path()` | Usa `HABITS_FILE` si está definida; si no, `~/habits.json` | RNF-1 |
| `load(path)` | Si el archivo no existe, devuelve `[]`. Si existe, lo parsea y valida (sección 2.2) y lanza `CorruptDataError` si no es válido | RNF-3, RNF-4 |
| `save(path, habits)` | Serializa con fechas ordenadas y sin duplicados. Escribe en un archivo temporal del mismo directorio y lo sustituye con `os.replace` | RNF-2, RNF-5 |

### 1.3 Responsabilidades de `cli` (RF-2 a RF-5 y RF-7)

- `main(argv=None, *, today=None, data_path=None) -> int`
  - Lee la fecha una sola vez al inicio (CL-14).
  - Carga los datos, ejecuta el comando y guarda solo si hubo cambios.
  - Traduce las excepciones a mensajes en español y devuelve el código de
    salida.
  - Los parámetros `today` y `data_path` existen para los tests.
- Subclase de `ArgumentParser` que sobrescribe `error()` para que el mensaje de
  uso salga en español con código 2. Por defecto argparse escribe en inglés
  (RF-7, CA-7.2).

## 2. Modelo de datos JSON

### 2.1 Formato y ejemplo

```json
{
  "version": 1,
  "habits": [
    {
      "name": "Leer",
      "done": ["2026-11-06", "2026-11-07", "2026-11-08"]
    },
    {
      "name": "Repasar inglés",
      "done": []
    }
  ]
}
```

- `version`: entero que permite migrar el formato en el futuro.
- `habits`: lista de objetos.
  - `name`: el nombre tal como lo escribió el usuario (CA-1.3).
  - `done`: lista de fechas `AAAA-MM-DD` (RNF-2). Al guardar se escribe ordenada
    y sin repetidos.
- Se guarda con `indent=2` y `ensure_ascii=False` para que acentos y «ñ» sean
  legibles a mano (RNF-2, principio 5).

### 2.2 Reglas de validación al cargar (RNF-4)

Cualquiera de estas condiciones lanza `CorruptDataError`, y el archivo no se
toca:
- JSON inválido.
- La raíz no es un objeto.
- Falta `habits` o no es una lista.
- `version` distinta de 1.
- `name` no es texto o queda vacío al recortarlo.
- `done` no es una lista de textos con formato `AAAA-MM-DD` válido
  (`date.fromisoformat`).
- Dos hábitos con la misma clave de nombre.

Situaciones que se toleran:
- **Fechas repetidas en `done`.** Se convierten en conjunto (CA-6.4, CL-12).
- **Fechas futuras.** Se conservan y el cálculo de racha las ignora de forma
  natural (sección 3), lo que encaja con la propuesta para D-3.

## 3. Algoritmo de cálculo de racha (RF-6)

```
función current_streak(fechas_hechas, hoy):
    días ← conjunto(fechas_hechas)                  # CA-6.4: cada día cuenta una vez

    si hoy ∈ días:            ancla ← hoy           # CA-6.1
    si no, si hoy-1 ∈ días:   ancla ← hoy - 1 día   # CA-6.2: el día en curso no rompe la racha
    si no:                    devolver 0            # CA-6.3

    racha ← 0
    cursor ← ancla
    mientras cursor ∈ días:
        racha ← racha + 1
        cursor ← cursor - 1 día
    devolver racha
```

- **Coste:** O(n) para construir el conjunto y O(racha) para recorrerlo.
  Cumple RNF-6 con 100 hábitos y 5 años de historial.
- **Fechas futuras:** como el recorrido empieza en `hoy` o `hoy-1` y va hacia
  atrás, nunca se cuentan.
- **Huecos:** el bucle se detiene en el primer día que falta, así que solo
  cuenta el tramo final continuo (CL-11).
- **Ejemplo de la spec:** hoy es miércoles y hay marcas el lunes y el martes.
  `hoy ∉ días` y `martes ∈ días`, así que el ancla es el martes y la racha es 2.

## 4. Contrato de la CLI (RF-2, RF-3, RF-4, RF-5, RF-7)

**Invocación:** `python -m habits <comando> [argumentos]`. Los nombres con
espacios van entre comillas.

**Convenciones:**
- Las salidas correctas van a stdout y los errores a stderr.
- Códigos de salida:
  - **0:** éxito, incluidos «ya estaba marcado» y «No existen hábitos».
  - **1:** error de dominio o de datos (nombre vacío, duplicado, no existe,
    archivo corrupto).
  - **2:** error de uso (comando desconocido o argumentos que faltan).

### 4.1 Comandos

| Comando | Caso | Salida | Código | RF |
|---|---|---|---|---|
| `crear <nombre>` | Éxito | `Hábito «Leer» creado.` | 0 | CA-2.1 |
| | Ya existe | `Error: ya existe el hábito «Leer».` | 1 | CA-2.2 |
| | Nombre vacío | `Error: el nombre del hábito no puede estar vacío.` | 1 | CA-1.4 |
| `hecho <nombre>` | Éxito | `Hábito «Leer» marcado como hecho hoy.` | 0 | CA-3.1 |
| | Ya marcado hoy | `El hábito «Leer» ya estaba marcado hoy.` | 0 | CA-3.2 |
| | No existe | `Error: no existe el hábito «Leeer».` | 1 | CA-3.3 |
| `renombrar <actual> <nuevo>` | Éxito | `Hábito «Leer» renombrado a «Lectura».` | 0 | CA-4.1 |
| | Origen no existe | `Error: no existe el hábito «X».` | 1 | CA-4.2 |
| | Nuevo nombre en uso | `Error: ya existe el hábito «Repasar».` | 1 | CA-4.3 |
| | Nombre vacío | `Error: el nombre del hábito no puede estar vacío.` | 1 | CA-1.4 |
| `listar` | Hay hábitos | Una línea por hábito (ver 4.2) | 0 | CA-5.1, 5.2 |
| | Sin hábitos | `No existen hábitos` | 0 | CA-5.3 |
| (cualquiera) | Archivo corrupto | `Error: no se puede leer el archivo de hábitos (<ruta>): <motivo>.` | 1 | RNF-4 |
| (cualquiera) | Comando desconocido o faltan argumentos | `uso: python -m habits {crear,hecho,renombrar,listar} ...` y `Error: <detalle>` | 2 | CA-7.2 |

En los mensajes, el nombre se muestra tal como está guardado (CA-1.3). En los
errores de «no existe» se muestra normalizado, tal como lo escribió el usuario.

### 4.2 Formato del listado

```
✓ Lectura         racha: 3 días
✗ Repasar inglés  racha: 1 día
✗ Yoga            racha: 0 días
```

- Columna 1: `✓` si está hecho hoy y `✗` si no.
- Columna 2: el nombre, alineado al más largo.
- Columna 3: `racha: N día(s)`, con singular para 1.
- Orden: alfabético por `casefold()` (CA-5.2).

## 5. Flujo por comando

```
main(argv):
  hoy  ← today o date.today()             # se lee una vez (CL-14)
  ruta ← data_path o default_path()
  args ← parser.parse_args(argv)          # error de uso → código 2

  intentar:
    hábitos ← storage.load(ruta)
    según args.comando:
      crear:     core.add_habit(...);    storage.save(...); imprimir confirmación
      hecho:     cambió ← core.mark_done(...)
                 si cambió: storage.save(...); imprimir confirmación
                 si no: imprimir aviso de que ya estaba marcado
      renombrar: core.rename_habit(...); storage.save(...); imprimir confirmación
      listar:    imprimir líneas o «No existen hábitos»    # nunca guarda
    devolver 0
  capturar HabitError o CorruptDataError:
    imprimir el mensaje en español en stderr
    devolver 1
```

Las operaciones de `core` validan todo antes de mutar. Si fallan, no se llama a
`save`, así que el archivo queda intacto (RNF-5).

## 6. Decisiones técnicas

| # | Decisión | Justificación | Alternativa descartada |
|---|---|---|---|
| DT-1 | Comandos en español (`crear`, `hecho`, `renombrar`, `listar`) | El usuario los ve, y el principio 6 exige que todo texto visible esté en español | Comandos en inglés (`add`, `done`, `list`): incumple el principio 6 |
| DT-2 | Lista de objetos `{name, done}` en el JSON | Conserva el nombre original y es fácil de editar a mano | Diccionario `{nombre: [fechas]}`: al editar a mano se pueden crear claves que solo difieren en mayúsculas y que la comparación no detectaría hasta cargar |
| DT-3 | Campo `version` en la raíz | Permite migrar el formato sin ambigüedad | Sin versión: una migración futura tendría que adivinar el formato |
| DT-4 | Comparar con `casefold()` | Es la comparación sin mayúsculas recomendada por Unicode (por ejemplo, «ß» y «ss») | `lower()`: falla en casos Unicode |
| DT-5 | `today` inyectado como parámetro en `core` y `cli.main` | Hace los tests deterministas (RNF-7) y fija la fecha al inicio del comando (CL-14) | Llamar a `date.today()` dentro de `core`: obliga a parchear el reloj en los tests |
| DT-6 | Escritura atómica: archivo temporal en el mismo directorio y `os.replace` | Un fallo a mitad de escritura no deja el JSON corrupto (RNF-5) | Escribir directamente sobre `habits.json`: si se interrumpe, se pierden los datos |
| DT-7 | Ruta por defecto `~/habits.json`, con `HABITS_FILE` para cambiarla | Los datos son los mismos sin importar desde qué carpeta se ejecute. La variable permite aislar los tests | `./habits.json` en el directorio actual: los datos «desaparecen» al cambiar de carpeta |
| DT-8 | `argparse` con `error()` sobrescrito | Está en la biblioteca estándar y da los mensajes de uso en español (CA-7.2) | Parsear `sys.argv` a mano: más código y más errores; `argparse` sin modificar: mensajes en inglés |
| DT-9 | Excepciones de dominio sin texto para el usuario; `cli` decide el mensaje | Mantiene `core` libre de interfaz (principio 3) y centraliza los textos en español | Mensajes en español dentro de `core`: mezcla lógica e interfaz |
| DT-10 | `hecho` no guarda si no hubo cambio | Garantiza «sin cambios» en CA-3.2 y evita escrituras innecesarias | Guardar siempre: reescribe el archivo y puede alterar ediciones manuales de formato |
| DT-11 | Exit 1 para errores de dominio y 2 para errores de uso | Es la convención Unix y la de `argparse`; distingue fallos de los scripts | Un único código 1: los scripts no distinguen un uso incorrecto de un error de datos |
| DT-12 | Las fechas se guardan como texto ISO y en memoria como `set[date]` | ISO en disco cumple el principio 5. El conjunto da búsquedas O(1) y deduplica (CA-6.4) | Guardar timestamps: no son legibles a mano |

## 7. Resolución propuesta para las dudas abiertas

Estas propuestas no se implementan hasta que se incorporen a la spec (principio
2).

| Duda | Propuesta | Impacto en el plan |
|---|---|---|
| D-1. Longitud máxima del nombre | Sin límite ni caracteres prohibidos en el MVP | Ninguno: no hay validación extra |
| D-2. Renombrar cambiando solo mayúsculas | Permitirlo; al buscar conflictos se excluye el propio hábito | En `rename_habit`, el conflicto se comprueba contra los demás hábitos |
| D-3. Fechas futuras en los datos | Conservarlas e ignorarlas en la racha | Ya resuelto por el algoritmo de la sección 3 |
| D-4. Textos y formato | Los de la sección 4 | Los tests de CLI fijan esos textos |

## 8. Estrategia de tests

**Herramientas:**
- Framework: `unittest` (principio 4).
- Verificación: `python -m unittest discover`. `pytest -q` también funciona.

**Principios:**
- Los tests no dependen del reloj real: siempre se pasa una fecha fija (por
  ejemplo, `date(2026, 11, 11)`, miércoles) (RNF-7).
- No se toca el `~/habits.json` real: se usa `tempfile.TemporaryDirectory`, y
  `data_path` o `HABITS_FILE`.
- Cada criterio de aceptación tiene al menos un test con un nombre en inglés que
  lo identifica, por ejemplo `test_mark_done_twice_is_noop_ca_3_2`.

**Niveles:**

1. **`test_core.py`** (unitarios y puros): nombres, creación, marcado,
   renombrado y racha. La racha se prueba con tablas de casos:
   - vacío → 0;
   - solo hoy → 1;
   - lunes y martes con hoy miércoles → 2;
   - lunes, martes y miércoles → 3;
   - con hueco → solo el tramo final;
   - con duplicados;
   - con fechas futuras;
   - última marca anteayer → 0.
2. **`test_storage.py`**:
   - archivo inexistente → `[]`;
   - ida y vuelta de guardar y cargar;
   - cada regla de corrupción de 2.2 → `CorruptDataError` con el archivo sin
     modificar (se compara el contenido antes y después);
   - acentos legibles en disco;
   - fechas ordenadas y sin duplicados al guardar;
   - atomicidad: se simula un fallo en `os.replace` y se comprueba que el
     archivo original sigue intacto.
3. **`test_cli.py`** (contrato): se invoca `main([...], today=..., data_path=...)`
   capturando la salida con `contextlib.redirect_stdout` y `redirect_stderr`.
   Para cada fila de la tabla 4.1 se comprueban:
   - el texto exacto;
   - que el mensaje sale por el flujo correcto (stdout o stderr);
   - el código de salida.

   Además, un test de humo ejecuta `python -m habits listar` con `subprocess` y
   `HABITS_FILE` apuntando a un directorio temporal.

## 9. Matriz de trazabilidad

| Requisito | Diseño | Tests |
|---|---|---|
| RF-1 (CA-1.1…1.4) | `normalize_name`, `name_key`; DT-4 | test_core (nombres), test_cli (nombre vacío) |
| RF-2 (CA-2.1, 2.2) | `add_habit`; tabla 4.1 | test_core, test_cli |
| RF-3 (CA-3.1…3.4) | `mark_done`; DT-5, DT-10; tabla 4.1 | test_core, test_cli (incluido «no crea hábito») |
| RF-4 (CA-4.1…4.4) | `rename_habit`; D-2; tabla 4.1 | test_core (conserva fechas, conflictos), test_cli |
| RF-5 (CA-5.1…5.3) | `sorted_habits`, `is_done_on`, `current_streak`; sección 4.2 | test_cli (formato, orden, vacío) |
| RF-6 (CA-6.1…6.4) | Sección 3; DT-12 | test_core (tabla de rachas) |
| RF-7 (CA-7.1, 7.2) | DT-8, DT-9, DT-11; sección 4 | test_cli (errores de uso, idioma) |
| RNF-1 | `default_path`; DT-7 | test_cli (`HABITS_FILE`) |
| RNF-2 | Sección 2.1; DT-12 | test_storage (legibilidad e ISO) |
| RNF-3 | `load` sin archivo | test_storage, test_cli (`listar` en el primer uso) |
| RNF-4 | Sección 2.2 | test_storage, test_cli |
| RNF-5 | DT-6; validar antes de mutar | test_storage (fallo simulado) |
| RNF-6 | Complejidad del algoritmo (sección 3) | test_core: 100 hábitos y 5 años de historial en menos de 1 s |
| RNF-7 | DT-5 | Todos: fecha inyectada |
| CL-1…CL-15 | Cubiertos por las filas anteriores | Un test por caso límite, nombrado con su identificador |

## 10. Orden de implementación sugerido

1. Actualizar la spec con las resoluciones de D-1…D-4.
2. `core` y `test_core`.
3. `storage` y `test_storage`.
4. `cli`, `__main__` y `test_cli`.
5. Ejecutar la suite completa.
