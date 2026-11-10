# Checklist App Constitution

Este documento establece los principios no negociables del proyecto **checklist-app**.
Todos los specs, planes, tareas e implementaciones deben respetarlo.

**Versión**: 1.0.0  
**Ratificada**: 2026-11-10  
**Última modificación**: 2026-11-10

## Principios Fundamentales

### I. Simplicidad Primero (NON-NEGOTIABLE)
El proyecto debe ser lo más simple posible.  
No se agregan abstracciones, librerías ni features que no estén explícitamente en el spec.

### II. Persistencia en JSON
Toda la data se guarda en un único archivo JSON (`backend/data/checklists.json`).  
No se usa base de datos, ORM ni almacenamiento externo.

### III. Separación Clara de Responsabilidades
- El **backend (Python + FastAPI)** es el único dueño de la data y de la lógica de negocio.
- El **frontend (React + TypeScript)** solo consume la API y muestra la UI.
- No se duplica lógica de negocio en el frontend.

### IV. Sin Seguridad
No se implementa autenticación, autorización, validación de usuarios ni protección de endpoints.  
El proyecto es de uso local / demo.

### V. Código en Inglés, Documentación en Español
- Código, nombres de variables, funciones, endpoints y comentarios → **inglés**.
- Specs, constitution, AGENTS.md, planes y tareas → **español**.

### VI. Stack Fijo
- Backend: Python + FastAPI
- Frontend: React + TypeScript (Vite)
- Persistencia: archivo JSON

Cualquier cambio de stack requiere actualizar esta constitution primero.

### VII. Arquitectura Hexagonal (Backend)
El backend sigue arquitectura hexagonal por capas:
- **Dominio**: lógica de negocio pura (sin frameworks).
- **Aplicación**: casos de uso.
- **Infraestructura**: FastAPI, persistencia JSON, etc.

No se mezcla lógica de negocio con detalles de infraestructura.

## Gobierno

- Esta constitution tiene prioridad sobre cualquier otra práctica o decisión.
- Cualquier desviación debe justificarse y documentarse explícitamente.
- Los agentes `dev` y `qa` deben consultar este documento antes de generar o revisar cualquier artefacto.
