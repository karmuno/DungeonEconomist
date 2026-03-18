---
description: Vue 3 and TypeScript conventions for the frontend
globs: ["frontend/src/**/*.vue", "frontend/src/**/*.ts"]
---

# Frontend Style

- Vue 3 Composition API with `<script setup lang="ts">`.
- State management via Pinia stores in `frontend/src/stores/`.
- API calls in typed client modules under `frontend/src/api/`.
- TypeScript interfaces in `frontend/src/types/index.ts`.
- Reusable logic in composables under `frontend/src/composables/`.
- ESLint enforces style (see `frontend/eslint.config.js`).
