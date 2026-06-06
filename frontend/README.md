This is the FitVTON presentation frontend for comparing virtual try-on artifacts and model variants.

## Getting Started

Install dependencies and run the development server:

```bash
npm install
npm run dev
```

Open:

- [http://localhost:3000/model-compare](http://localhost:3000/model-compare)

The root route redirects to `/model-compare`.

## Data Source

Create `.env.local` from `.env.example` when connecting a backend:

```bash
NEXT_PUBLIC_USE_MOCK=true
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

- `NEXT_PUBLIC_USE_MOCK=true` always uses `src/lib/mockData.ts`.
- `NEXT_PUBLIC_USE_MOCK=false` tries the real API first.
- Network errors, fetch failures, and non-2xx responses fall back to mock data.
- Restart the Next dev server after changing `.env.local`.

Expected backend endpoints:

```bash
GET /api/demo/samples
GET /api/demo/model-compare/{pairId}
```

## Verification

```bash
npm run lint
npm run build
```
