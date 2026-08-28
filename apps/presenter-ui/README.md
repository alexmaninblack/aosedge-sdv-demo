# Presenter UI

Fixture-only browser application for `WP-P1-UI-001`. Every observed fact is
labelled as deterministic fixture data. The bundle has no Cloud, helper,
backend, Gateway, CARLA, VM, Unit or credential capability.

Use Node `26.0.0` and npm `11.12.1`:

```text
npm ci
npm run typecheck
npm run test:unit
npm run test:browser
npm run build
npm run dev -- --host 127.0.0.1 --port 18070
```

Append `?fixture=<id>` to select an accepted deterministic presentation state.
The default is `ready`; fixture identifiers are owned by
`src/adapters/fixtures/fixtureCatalog.ts`.
