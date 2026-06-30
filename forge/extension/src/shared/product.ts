// Journey-Forge Local — product build flags.
//
// This extension is the consumer-product fork (journey-forge-local). It ships
// pre-pointed at the local server and hides the ClawBench task-queue UI. The
// research extension behavior is recovered by flipping PRODUCT_LOCAL to false.

export const PRODUCT_LOCAL = true;

// Default ingestion server. Build-time configurable: set WXT_FORGE_ENDPOINT to
// bake your hosted recorder URL into the build (clients can still override it in
// Settings). Falls back to the local server (server/server.py's JFL_PORT 8099).
export const DEFAULT_ENDPOINT_URL =
  (import.meta.env.WXT_FORGE_ENDPOINT as string | undefined) || 'http://127.0.0.1:8099';

// Default Bearer key. Set WXT_FORGE_API_KEY to bake a default (e.g. a shared
// pilot key); otherwise the local server seeds this same key into api-keys.json
// on first run, so a local extension connects with zero config. Override per
// client in Settings — the hosted server issues a unique key per client.
export const DEFAULT_API_KEY =
  (import.meta.env.WXT_FORGE_API_KEY as string | undefined) || 'jfl-local-dev-key';

// Tasks = the ClawBench claim/lease queue. Off in the product (free-form only).
export const SHOW_TASKS_UI = !PRODUCT_LOCAL;

// Identity bundles are a research concept; in the product, identity fetch is
// best-effort and must never block recording or upload.
export const IDENTITY_BEST_EFFORT = PRODUCT_LOCAL;
