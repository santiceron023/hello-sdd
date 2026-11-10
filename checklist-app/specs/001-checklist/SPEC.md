# Spec: Gestión Básica de Checklists

## Objetivo
Permitir al usuario crear checklists, asignarles un título, agregar ítems y marcarlos o desmarcarlos como completados.  
Toda la información se guarda en un archivo JSON.

## Alcance
- Crear una checklist con título.
- Agregar ítems a una checklist.
- Marcar / desmarcar un ítem.
- Ver la lista de checklists y sus ítems.

## Fuera de alcance
- Autenticación o usuarios.
- Editar el título de una checklist después de creada.
- Reordenar ítems.
- Eliminar checklists o ítems (se puede agregar en un spec posterior).

## User Stories

### US-1: Crear checklist
**Como** usuario  
**Quiero** crear una nueva checklist con un título  
**Para** organizar mis tareas

**Criterios de aceptación:**
- Puedo ingresar un título y crear la checklist.
- La checklist aparece en la lista principal.
- Se guarda en el archivo JSON.

### US-2: Agregar ítem
**Como** usuario  
**Quiero** agregar ítems a una checklist  
**Para** detallar las tareas

**Criterios de aceptación:**
- Puedo escribir el texto de un ítem y agregarlo.
- El ítem aparece desmarcado por defecto.
- Se persiste en el JSON.

### US-3: Marcar / desmarcar ítem
**Como** usuario  
**Quiero** marcar o desmarcar un ítem  
**Para** indicar si está completado

**Criterios de aceptación:**
- Al hacer clic en un ítem cambia su estado (completado / pendiente).
- El cambio se guarda inmediatamente en el JSON.
- La interfaz refleja el estado actual.

## Modelo de datos (JSON)

```json
{
  "checklists": [
    {
      "id": "uuid-o-simple-id",
      "title": "Compras",
      "items": [
        {
          "id": "item-1",
          "text": "Leche",
          "completed": false
        }
      ]
    }
  ]
}
```

## Notas técnicas
- Backend: FastAPI expone endpoints para crear checklist, agregar ítem y actualizar estado.
- Frontend: React + TypeScript muestra las listas y permite las acciones.
- Persistencia: único archivo `backend/data/checklists.json`.
- Seguir arquitectura hexagonal en el backend (ver skill `backend` o `arquitectura-backend`).

## Estado
Borrador inicial — pendiente de revisión por el agente `qa`.
