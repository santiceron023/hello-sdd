# Proyecto: `checklist-app`

Aplicación web simple de listas de verificación. Cada checklist tiene un título y una lista de ítems que se pueden marcar y desmarcar.

Persistencia en un único archivo JSON. Sin autenticación.

## Estructura del proyecto

```
checklist-app/
├── AGENTS.md
├── CLAUDE.md
├── notas.md
├── docs/
│   └── CONSTITUTION.md
├── specs/
│   └── 001-checklist/
│       └── SPEC.md
├── skills/
│   └── backend/
│       └── SKILL.md
└── .claude/
    └── agents/
        ├── dev.md
        └── qa.md
```

## Comandos

### Backend

```bash
cd arquitectura-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Prompts SDD

### 1. Especificación

```text
NO escribas código en ningún momento.
Solo vamos a redactar la especificación de la funcionalidad "Gestión básica de checklists" de checklist-app.

Lee constitution.md y AGENTS.md antes de empezar.

Alcance exacto de este spec (no te salgas de esto):
- Crear una checklist con título.
- Agregar ítems de texto a una checklist.
- Marcar y desmarcar ítems como completados.
- Ver las checklists existentes con sus ítems.
- Persistencia en un único archivo JSON.

Fuera de alcance (no lo incluyas):
- Editar títulos, eliminar listas o ítems, reordenar, usuarios, autenticación, múltiples archivos, búsqueda, progreso visual avanzado.

Tu trabajo:
1. Hazme máximo 4 preguntas (de una en una) solo para aclarar casos límite dentro del alcance anterior.
2. Después genera el archivo specs/001-checklists-basico/spec.md con esta estructura fija:
   - Contexto y objetivo
   - Historias de usuario (máximo 3)
   - Requisitos funcionales (RF-1, RF-2…) con criterios de aceptación en notación EARS
   - Casos límite
   - Fuera de alcance
   - Criterios de finalización

Solo el QUÉ y el POR QUÉ. Nada de stack, arquitectura, endpoints ni nombres de archivos.

Empieza con la primera pregunta.
```

*Genera el [specs/001-checklist/SPEC.md](./specs/001-checklist/SPEC.md)*

### 2. Clarificación

```text
Revisa specs/001-checklists/spec.md como si fueras el agente qa descrito en AGENTS.md.

Lista únicamente:
1. Ambigüedades restantes
2. Contradicciones entre requisitos
3. Casos límite no cubiertos
4. Conflictos con constitution.md

No propongas soluciones todavía: solo detecta.
Formato: lista numerada clara.

Al final indica: APROBADO o CAMBIOS REQUERIDOS.
```

### 3. Planificación

```text
Lee constitution.md y specs/001-checklists/spec.md.
NO escribas código.

Genera specs/001-checklists/plan.md con:

- Estructura de módulos (backend y frontend)
- Modelo de datos JSON con un ejemplo
- Contrato de la API (endpoints principales, qué reciben y qué devuelven)
- Decisiones técnicas justificadas (y alternativa descartada)
- Estrategia de tests

Todo debe respetar la constitución y cubrir todos los RF del spec.
Marca qué RF cubre cada parte del plan.
```

*Genera el specs/001-checklists/plan.md*

### 4. Tareas

```text
A partir de specs/001-checklists/spec.md y specs/001-checklists/plan.md,
genera specs/001-checklists/tasks.md.

Crea tareas pequeñas (máximo 20-30 minutos cada una), en orden de dependencia.
Cada tarea debe incluir:
- Los RF que cubre
- Una línea "Hecho cuando:" verificable

Usa checkboxes.
```

*Genera el specs/001-checklists/tasks.md*

### 5. Implementación

**Tarea directa:**

```text
Implementa la tarea T1 de specs/001-checklists/tasks.md, siguiendo plan.md y constitution.md.

Escribe primero los tests, luego el código.
Ejecuta los tests y muéstrame el resultado.

Al terminar:
- Marca T1 como completada en tasks.md
- Indica qué RF cubre
- PÁRATE. No empieces la siguiente tarea.
```

**Agente `dev`:**

```text
Actúa como el agente dev descrito en AGENTS.md.

Implementa la tarea T1 de specs/001-checklists/tasks.md, siguiendo plan.md y constitution.md.

Escribe primero los tests, luego el código.
Ejecuta los tests y muéstrame el resultado.

Al terminar:
- Marca T1 como completada en tasks.md
- Indica qué RF cubre
- PÁRATE. No empieces la siguiente tarea.
```

**Atajo `/dev`:**

```text
/dev

Implementa la tarea T1 de specs/001-checklists/tasks.md...
```

### 6. Validación

**Revisión del spec:**

```text
Actúa como el agente qa descrito en AGENTS.md.
Revisa el archivo spec.md.
```

**Cobertura requisito por requisito:**

```text
Actúa como el agente qa descrito en AGENTS.md.

Recorre specs/001-checklists/spec.md requisito por requisito
Para cada uno indica:
- Qué test lo cubre
- El resultado de ejecutarlo

Si algún RF no está cubierto o falla, dilo claramente.

Después comprueba los criterios de finalización y dame un veredicto: ¿la spec está cumplida?
```
