# Tareas — Gestión básica de checklists

Orden de dependencia. Cada tarea cabe en 20-30 minutos.
Spec: `specs/001-checklist/SPEC.md`. Plan: `specs/001-checklist/plan.md`.

- [ ] T1. Esqueleto de `arquitectura-backend`: `requirements.txt` (FastAPI, uvicorn, pytest), `main.py` que expone la app y `data/checklists.json` con `{ "checklists": [] }`.
      (RF: RF-3) Hecho cuando: el JSON vacío existe y `uvicorn main:app` importa la app sin error.

- [ ] T2. Dominio `Checklist` y `ChecklistItem` en memoria, sin FastAPI ni archivos. Un ítem nuevo nace con `completed` en falso y puede invertirlo.
      (RF: RF-1, RF-4, RF-5, RF-6) Hecho cuando: `tests/test_domain.py` pasa esos tres casos.

- [ ] T3. Repositorio JSON: leer y escribir el archivo del plan. Si no existe, deja la estructura vacía.
      (RF: RF-3) Hecho cuando: `tests/test_repository.py` pasa con `tmp_path` (inexistente y válido).

- [ ] T4. Caso de uso crear checklist: título, id UUID y lista de ítems vacía, persistido.
      (RF: RF-1, RF-3) Hecho cuando: un test crea una checklist y al releer el JSON sigue ahí.

- [ ] T5. Caso de uso listar checklists con sus ítems, incluido el caso vacío.
      (RF: RF-2, RF-9) Hecho cuando: un test de lista vacía y otro con una checklist e ítem pasan.

- [ ] T6. Caso de uso agregar ítem: texto, id propio y `completed: false`, persistido.
      (RF: RF-4, RF-5, RF-3) Hecho cuando: un test agrega "Leche" y el JSON queda como el ejemplo del plan.

- [ ] T7. Caso de uso toggle: invierte `completed` y lo guarda al momento. Falla si no existe la checklist o el ítem.
      (RF: RF-6, RF-7) Hecho cuando: un test marca, otro desmarca y otro cubre el id inexistente.

- [ ] T8. Rutas FastAPI del contrato, sin lógica de negocio, con CORS de `http://localhost:5173`.
      (RF: RF-1, RF-2, RF-4, RF-6, RF-9) Hecho cuando: `tests/test_api.py` pasa los cuatro endpoints y un 404.

- [ ] T9. Frontend Vite (React + TypeScript) con `api.ts` que solo llama a los cuatro endpoints.
      (RF: RF-1, RF-4, RF-6, RF-9) Hecho cuando: `npm run dev` arranca y las funciones de `api.ts` coinciden con el contrato.

- [ ] T10. UI en `App.tsx`: ver listas e ítems, crear checklist, agregar ítem y marcar o desmarcar con un clic. Tras cada acción se vuelve a pintar `GET /checklists`.
      (RF: RF-2, RF-8, RF-9) Hecho cuando: en el navegador se completa ese recorrido y `checklists.json` refleja el resultado.
