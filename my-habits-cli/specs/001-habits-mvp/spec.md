# Spec 001 — MVP de habits-cli

- **Estado:** borrador
- **Fecha:** 2026-11-09

## 1. Contexto y objetivo

Mantener hábitos de estudio cuesta más cuando no se ve el progreso. Una racha
de días consecutivos es una forma sencilla de verlo y motiva a no romperla.

**Objetivo:** ofrecer una herramienta de línea de comandos, local y sin
cuentas, para crear hábitos, renombrarlos, marcarlos como hechos cada día y
consultar la racha actual de cada uno.

## 2. Usuarios

- **Estudiante individual** que trabaja en la terminal y quiere registrar
  hábitos diarios (leer, repasar, practicar) con el mínimo de fricción.
- Un solo usuario por instalación. Los datos son locales y el usuario puede
  editarlos a mano.

## 3. Historias de usuario

- **HU-1.** Como estudiante, quiero crear un hábito con un nombre para empezar
  a registrarlo.
- **HU-2.** Como estudiante, quiero marcar un hábito como hecho hoy para que
  cuente en mi racha.
- **HU-3.** Como estudiante, quiero listar mis hábitos con su racha y saber si
  ya los hice hoy para decidir qué me falta.
- **HU-4.** Como estudiante, quiero renombrar un hábito sin perder su
  historial para corregir erratas o ajustar su descripción.

## 4. Requisitos funcionales

Los criterios de aceptación usan notación EARS:

- **Ubicuo:** "El sistema deberá…"
- **Por evento:** "Cuando…, el sistema deberá…"
- **Por estado:** "Mientras…, el sistema deberá…"
- **No deseado:** "Si…, entonces el sistema deberá…"

### RF-1. Reglas de nombre de hábito

Estas reglas se aplican siempre que el usuario introduce un nombre, ya sea al
crear, marcar o renombrar un hábito.

- **CA-1.1.** El sistema deberá eliminar los espacios al inicio y al final de
  todo nombre introducido antes de usarlo.
- **CA-1.2.** El sistema deberá comparar los nombres sin distinguir mayúsculas
  de minúsculas, de modo que «Leer» y «leer» identifican al mismo hábito.
- **CA-1.3.** El sistema deberá conservar las mayúsculas y minúsculas con que
  se escribió el nombre al crearlo o renombrarlo, y mostrarlo así.
- **CA-1.4.** Si el nombre queda vacío tras eliminar los espacios de los
  extremos, entonces el sistema deberá rechazar la operación con un mensaje de
  error, no modificar ningún dato y terminar con código de salida distinto
  de 0.

### RF-2. Crear un hábito

- **CA-2.1.** Cuando el usuario crea un hábito con un nombre válido que no
  existe, el sistema deberá guardarlo sin días registrados, confirmar la
  creación con un mensaje y terminar con código de salida 0.
- **CA-2.2.** Si ya existe un hábito con ese nombre (según CA-1.2), entonces
  el sistema deberá rechazar la creación con un mensaje de error que nombre el
  hábito, no modificar ningún dato y terminar con código de salida distinto
  de 0.

### RF-3. Marcar un hábito como hecho hoy

- **CA-3.1.** Cuando el usuario marca como hecho un hábito existente que no
  está marcado hoy, el sistema deberá registrar la fecha de hoy para ese
  hábito, confirmarlo con un mensaje y terminar con código de salida 0.
- **CA-3.2.** Mientras el hábito ya está marcado hoy, cuando el usuario lo
  vuelve a marcar, el sistema deberá dejar los datos sin cambios, informar con
  un mensaje de que ya estaba marcado hoy y terminar con código de salida 0.
- **CA-3.3.** Si el hábito indicado no existe, entonces el sistema deberá
  mostrar un error que nombre el hábito («No existe el hábito …»), no crear
  ningún hábito, no modificar ningún dato y terminar con código de salida
  distinto de 0.
- **CA-3.4.** El sistema deberá registrar siempre la fecha de hoy según el
  reloj local del equipo. No se admite marcar otras fechas.

### RF-4. Renombrar un hábito

- **CA-4.1.** Cuando el usuario renombra un hábito existente a un nombre
  válido que no está en uso, el sistema deberá cambiar el nombre, conservar
  intacto el historial de días marcados, confirmarlo con un mensaje y terminar
  con código de salida 0.
- **CA-4.2.** Si el hábito de origen no existe, entonces el sistema deberá
  mostrar un error que lo nombre, no modificar ningún dato y terminar con
  código de salida distinto de 0.
- **CA-4.3.** Si el nuevo nombre ya pertenece a otro hábito (según CA-1.2),
  entonces el sistema deberá rechazar el cambio con un mensaje de error, no
  modificar ningún dato y terminar con código de salida distinto de 0.
- **CA-4.4.** Cuando el nuevo nombre solo difiere del actual en mayúsculas o
  minúsculas (por ejemplo, «leer» → «Leer»), el sistema deberá aceptarlo como
  un cambio de formato del mismo hábito, conservar su historial y terminar con
  código de salida 0 (D-2).

### RF-5. Listar hábitos

- **CA-5.1.** Cuando el usuario lista los hábitos y existe al menos uno, el
  sistema deberá mostrar una línea por hábito con:
  - el nombre;
  - la racha actual en días;
  - si está hecho hoy (✓) o no (✗).

  Después deberá terminar con código de salida 0.
- **CA-5.2.** El sistema deberá ordenar el listado alfabéticamente por nombre,
  sin distinguir mayúsculas de minúsculas.
- **CA-5.3.** Mientras no existe ningún hábito, cuando el usuario lista los
  hábitos, el sistema deberá mostrar el mensaje «No existen hábitos» y
  terminar con código de salida 0.

### RF-6. Cálculo de la racha actual

- **CA-6.1.** Mientras el hábito está marcado hoy, el sistema deberá calcular
  la racha como el número de días consecutivos marcados que terminan hoy.
- **CA-6.2.** Mientras el hábito no está marcado hoy pero sí ayer, el sistema
  deberá calcular la racha como el número de días consecutivos marcados que
  terminan ayer. El día en curso no rompe la racha.
- **CA-6.3.** Mientras el hábito no está marcado ni hoy ni ayer, el sistema
  deberá mostrar una racha de 0.
- **CA-6.4.** El sistema deberá contar cada día natural como máximo una vez,
  aunque aparezca repetido en los datos.

**Ejemplo.** Hoy es miércoles y el hábito está marcado el lunes y el martes:
la racha es 2 y el hábito aparece como ✗ hoy. Si se marca hoy, la racha pasa
a 3 y aparece como ✓.

### RF-7. Errores generales

- **CA-7.1.** El sistema deberá mostrar todos los mensajes, incluidos los de
  error, en español.
- **CA-7.2.** Si el usuario invoca un comando desconocido o con argumentos que
  faltan, entonces el sistema deberá mostrar un mensaje de uso en español y
  terminar con código de salida distinto de 0.

## 5. Requisitos no funcionales

- **RNF-1. Persistencia local.** Los datos deberán persistir entre ejecuciones
  en el equipo del usuario, sin red, base de datos ni cuentas.
- **RNF-2. Datos legibles.** Los datos guardados deberán ser texto legible y
  editable a mano, con las fechas en formato ISO-8601 (AAAA-MM-DD).
- **RNF-3. Primer uso.** Si todavía no existen datos guardados, el sistema
  deberá comportarse como si no hubiera hábitos, sin mostrar error.
- **RNF-4. Datos corruptos.** Si los datos guardados no se pueden interpretar,
  entonces el sistema deberá mostrar un error en español, terminar con código
  de salida distinto de 0 y no sobrescribirlos.
- **RNF-5. Atomicidad.** Una operación que falla no deberá dejar los datos a
  medio modificar.
- **RNF-6. Rendimiento.** Cada comando deberá responder de forma prácticamente
  instantánea (menos de 1 segundo) con hasta 100 hábitos y 5 años de
  historial.
- **RNF-7. Verificabilidad.** Cada regla de registro y de racha de esta spec
  deberá poder comprobarse con pruebas automáticas que no dependan de la fecha
  real del sistema.

## 6. Casos límite

| # | Situación | Comportamiento esperado |
|---|-----------|-------------------------|
| CL-1 | Hoy no está marcado, ayer sí | La racha cuenta hasta ayer (CA-6.2) |
| CL-2 | Hábito recién creado sin marcas | Racha 0 y ✗ |
| CL-3 | Se marca dos veces el mismo día | Sin cambios y aviso; código 0 (CA-3.2) |
| CL-4 | Se marca un hábito que no existe | Error; no se crea el hábito (CA-3.3) |
| CL-5 | Se crea «leer» existiendo «Leer» | Error por duplicado (CA-2.2) |
| CL-6 | El nombre solo tiene espacios | Error por nombre vacío (CA-1.4) |
| CL-7 | El nombre tiene espacios en los extremos («  Leer ») | Se usa «Leer» (CA-1.1) |
| CL-8 | Se renombra a un nombre que usa otro hábito | Error; sin cambios (CA-4.3) |
| CL-9 | Se renombra un hábito con racha | La racha y el historial se conservan (CA-4.1) |
| CL-10 | Se lista sin hábitos | «No existen hábitos»; código 0 (CA-5.3) |
| CL-11 | Hay un hueco de un día en el historial | La racha solo cuenta el tramo final continuo |
| CL-12 | El historial tiene una fecha duplicada (por edición manual) | Cuenta una sola vez (CA-6.4) |
| CL-13 | Los datos guardados están corruptos | Error sin sobrescribirlos (RNF-4) |
| CL-14 | Se ejecuta el comando justo al cambiar de día (medianoche) | Se usa la fecha local leída al inicio del comando |
| CL-15 | El historial tiene fechas futuras (por edición manual) | Se conservan y se ignoran en la racha (D-3) |

## 7. Fuera de alcance (MVP)

- Marcar días pasados o futuros: solo se marca el día de hoy.
- Desmarcar un día.
- Borrar hábitos.
- Mejor racha histórica, estadísticas o gráficos.
- Recordatorios o notificaciones.
- Frecuencias no diarias (por ejemplo, «3 veces por semana»).
- Varios usuarios, sincronización o acceso por red.

## 8. Criterios de finalización

- [ ] Todos los criterios de aceptación de RF-1 a RF-7 tienen al menos una
  prueba automática que falla si la regla se rompe.
- [ ] Todos los casos límite CL-1 a CL-15 están cubiertos por pruebas.
- [ ] Las pruebas de racha no dependen de la fecha real del sistema
  (RNF-7).
- [ ] Todos los mensajes visibles para el usuario están en español.
- [ ] Los códigos de salida coinciden con lo especificado en cada caso.
- [ ] Las dudas abiertas de la sección 9 están resueltas o ## 9. Dudas resueltas

- **D-1.** El nombre de un hábito no tiene longitud máxima ni caracteres
  prohibidos en el MVP. Solo se exige que no quede vacío (CA-1.4).
- **D-2.** Se permite renombrar cambiando solo mayúsculas o minúsculas
  (CA-4.4).
- **D-3.** Las fechas futuras que aparezcan en los datos por edición manual se
  conservan, pero no cuentan para la racha (CL-15).
- **D-4.** Los textos de los mensajes y el formato del listado son los
  definidos en el contrato de la CLI del plan técnico (secciones 4.1 y 4.2).
