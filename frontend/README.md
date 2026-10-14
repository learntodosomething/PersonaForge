# Frontend

React + TypeScript (Vite). Phase 1 UI: upload `message_*.json` files, review the import report,
choose the speaker, delete the import.

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (backend must run on 127.0.0.1:8000)
npm run build      # type-check + production build
```

Set `VITE_API_URL` in `frontend/.env.local` if the backend runs elsewhere.
