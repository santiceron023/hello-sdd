---
name: arquitectura-arquitectura-backend
description: Guía simple de arquitectura hexagonal para el arquitectura-backend de checklist-app. Carga este skill cuando vayas a implementar o modificar código del arquitectura-backend.
---

# Arquitectura Backend (Hexagonal) — Ilustrativo

Este skill es un ejemplo simple. Úsalo cuando trabajes en el backend.

## Capas

### 1. Dominio (`domain/`)
- Entidades y lógica de negocio pura.
- Sin dependencias de FastAPI ni de archivos.
- Ejemplo: clase `Checklist`, `ChecklistItem`.

### 2. Aplicación (`application/`)
- Casos de uso (ej. `CreateChecklist`, `ToggleItem`).
- Orquesta el dominio.
- No conoce detalles de HTTP ni del JSON.

### 3. Infraestructura (`infrastructure/`)
- Adaptadores: endpoints FastAPI, lectura/escritura del archivo JSON.
- Aquí sí se usa FastAPI y se toca el archivo `checklists.json`.

## Reglas simples
- La lógica de negocio nunca va en los endpoints de FastAPI.
- Los casos de uso reciben y devuelven objetos del dominio.
- Mantén todo lo más simple posible (es unbjgfjgh proyecto ilustrativo).

## Ejemplo de flujo
1. Endpoint FastAPI recibe la petición.
2. Llama a un caso de uso.
3. El caso de uso usa el dominio y un repositorio (que lee/escribe el JSON).
4. Devuelve la respuesta.

Consulta siempre `constitution.md` y `AGENTS.md`.
