# AGENTS.md — checklist-app

Este archivo es la fuente de verdad de instrucciones para todos los agentes de código (Claude Code, Codex, Cursor, etc.).

## Proyecto

**Nombre**: checklist-app  
**Descripción**: Aplicación web simple de listas de verificación (checklists).  
Cada checklist tiene un título y una lista de ítems que se pueden marcar/desmarcar.

**Persistencia**: archivo JSON único (`backend/data/checklists.json`).  
**Sin autenticación ni seguridad**.

## Stack

| Capa       | Tecnología                  |
|------------|-----------------------------|
| Backend    | Python + FastAPI            |
| Frontend   | React + TypeScript (Vite)   |
| Persistencia | Archivo JSON              |

## Comandos

### Backend
```bash
cd arquitectura-backend
python -m venv .venv
source .venv/bin/activate   # o .venv\Scripts\activate en Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Roles de Agentes

### Agente `dev`
**Responsabilidad**: Implementar.
- Escribe y modifica código.
- Genera specs iniciales, planes y tareas.
- Sigue estrictamente la constitution y el spec aprobado.
- **No se auto-aprueba**. Siempre espera revisión del agente `qa` cuando se le pide.

### Agente `qa`
**Responsabilidad**: Revisar y validar.
- Revisa specs, planes, código y criterios de aceptación.
- Busca ambigüedades, edge cases faltantes y desviaciones de la constitution.
- **Nunca implementa** código.
- Su salida debe ser clara: aprobado / cambios requeridos + lista concreta de observaciones.

## Cómo usar los roles

1. Para generar o modificar algo → usa el agente **`dev`**.
2. Para revisar → usa el agente **`qa`** en una sesión nueva o como subagente.
3. El `qa` tiene la última palabra sobre si un spec está listo para pasar a implementación.

## Convenciones de nombres (siempre)

- Python (backend): `snake_case` para variables y funciones, `PascalCase` para clases.
- TypeScript (frontend): `camelCase` para variables y funciones, `PascalCase` para componentes y tipos.
- Nombres claros y en inglés.

## Arquitectura

El backend sigue arquitectura hexagonal (ver constitution.md).  
Para detalles al implementar backend, usa el skill `arquitectura-backend`.

## Referencias obligatorias

- Siempre consulta `constitution.md` antes de generar o revisar cualquier artefacto.
- Documentación y specs en **español**. Código en **inglés**.
