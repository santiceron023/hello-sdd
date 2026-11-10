# Plan técnico — Gestión básica de checklists

La spec no numera requisitos funcionales. Este plan les asigna un identificador
a partir del alcance y de los criterios de aceptación, para poder marcar cobertura.

| ID | Requisito (spec) |
|----|------------------|
| RF-1 | Crear una checklist con título (US-1) |
| RF-2 | La checklist aparece en la lista principal (US-1) |
| RF-3 | Crear, agregar y cambiar estado se guardan en el JSON (US-1, US-2, US-3) |
| RF-4 | Agregar un ítem de texto a una checklist (US-2) |
| RF-5 | El ítem nuevo queda desmarcado (US-2) |
| RF-6 | Marcar y desmarcar un ítem (US-3) |
| RF-7 | El cambio de estado se guarda de inmediato (US-3) |
| RF-8 | La interfaz muestra el estado actual (US-3) |
| RF-9 | Ver las checklists existentes con sus ítems (alcance) |

## Estructura de módulos

El backend vive en `arquitectura-backend/` (comandos de `AGENTS.md` y skill
`arquitectura-backend`). El frontend vive en `frontend/`.

```
arquitectura-backend/
├── main.py                          # arranque de FastAPI (RF-1, RF-2, RF-4, RF-6, RF-9)
├── requirements.txt
├── domain/
│   ├── checklist.py                 # Checklist (RF-1)
│   └── checklist_item.py           # ChecklistItem (RF-4, RF-5, RF-6)
├── application/
│   ├── create_checklist.py          # RF-1, RF-3
│   ├── list_checklists.py           # RF-2, RF-9
│   ├── add_item.py                  # RF-4, RF-5, RF-3
│   └── toggle_item.py               # RF-6, RF-7
├── infrastructure/
│   ├── json_repository.py           # único archivo JSON (RF-3)
│   └── api.py                       # rutas FastAPI; sin lógica de negocio
├── data/
│   └── checklists.json
└── tests/
    ├── test_domain.py
    ├── test_repository.py
    ├── test_use_cases.py
    └── test_api.py

frontend/
├── index.html
├── package.json
├── vite.config.ts
└── src/
    ├── main.tsx
    ├── App.tsx                      # lista, alta y estado visible (RF-2, RF-8, RF-9)
    ├── api.ts                       # solo llama a la API; no decide reglas
    └── types.ts
```

Dominio y aplicación no importan FastAPI ni leen el archivo. La infraestructura
sí. El frontend no duplica reglas: muestra lo que devuelve la API y envía
título, texto o la acción de marcar.

## Modelo de datos JSON

Un solo archivo: `arquitectura-backend/data/checklists.json`.
La constitución lo nombra `backend/data/checklists.json`; se guarda dentro de
`arquitectura-backend/` porque ese es el directorio del backend en `AGENTS.md`.
Sigue siendo un único JSON, sin base de datos.

Archivo vacío:

```json
{ "checklists": [] }
```

Ejemplo (el de la spec):

```json
{
  "checklists": [
    {
      "id": "6f1c0a3e-7b24-4d1a-9c0e-1a2b3c4d5e6f",
      "title": "Compras",
      "items": [
        {
          "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "text": "Leche",
          "completed": false
        }
      ]
    }
  ]
}
```

- `id` de checklist e ítem: UUID en texto.
- `title` y `text`: el texto que escribió el usuario.
- `completed`: booleano. Un ítem nuevo se guarda en `false` (RF-5).
- El orden de `checklists` e `items` es el de inserción. No se reordena.

## Contrato de la API

Sin autenticación. JSON de entrada y de salida. Si la checklist o el ítem no
existen, la API responde `404` con `{ "detail": "..." }`.

| Método y ruta | Recibe | Devuelve | RF |
|---------------|--------|----------|----|
| `POST /checklists` | `{ "title": "Compras" }` | `201` y la checklist creada, con `id` e `items: []` | RF-1, RF-3 |
| `GET /checklists` | nada | `200` y `{ "checklists": [ ... ] }` con ítems | RF-2, RF-9 |
| `POST /checklists/{checklist_id}/items` | `{ "text": "Leche" }` | `201` y el ítem, con `completed: false` | RF-4, RF-5, RF-3 |
| `POST /checklists/{checklist_id}/items/{item_id}/toggle` | nada | `200` y el ítem con `completed` invertido | RF-6, RF-7 |

El frontend, tras cada acción, vuelve a leer `GET /checklists` y pinta esa
respuesta (RF-8). CORS solo permite el origen de Vite (`http://localhost:5173`)
para que las dos apps del stack fijo puedan hablarse en local.

## Decisiones técnicas

- **UUID en texto, no enteros incrementales.** El JSON se puede mirar y editar
  a mano; un entero depende de contar registros y choca si el archivo se toca.
  Alternativa descartada: ids `1`, `2`, `3`.
- **Toggle en el servidor, no un `completed` enviado por el cliente.** El clic
  de US-3 cambia el estado; el backend es el dueño de ese cambio (principio III).
  Alternativa descartada: `PATCH` con `{ "completed": true }`, que dejaría la
  regla en el frontend.
- **Casos de uso que devuelven objetos de dominio.** Las rutas solo traducen
  HTTP ↔ dominio. Alternativa descartada: lógica de alta y marcado dentro de
  las rutas FastAPI.
- **pytest + TestClient de FastAPI.** Cubre dominio, repositorio, casos de uso
  y HTTP sin navegador. Alternativa descartada: una librería de tests de UI;
  la constitución pide no sumar librerías que el spec no pide. La UI se comprueba
  a mano contra la API.
- **Un `App.tsx`.** No hace falta un router ni un estado global para tres
  acciones. Alternativa descartada: React Router y una store.

## Estrategia de tests

- Dominio, sin archivos ni HTTP: ítem nuevo desmarcado (RF-5) y cambio de
  `completed` (RF-6).
- Repositorio con `tmp_path`: archivo inexistente crea la estructura vacía;
  un JSON válido se lee y se vuelve a escribir igual (RF-3).
- Casos de uso: crear (RF-1), listar vacía y con datos (RF-2, RF-9), agregar
  ítem desmarcado (RF-4, RF-5), marcar y desmarcar (RF-6, RF-7).
- API con TestClient: los cuatro endpoints y un `404` si falta la checklist
  o el ítem (RF-1, RF-2, RF-4, RF-6, RF-9).
- Frontend: sin librería de tests. Comprobación manual de que la lista, el alta,
  el ítem nuevo y el clic reflejan `GET /checklists` (RF-2, RF-8, RF-9).
