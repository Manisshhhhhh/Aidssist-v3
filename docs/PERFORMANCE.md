# Performance Notes

## Storage

Local storage uses direct filesystem reads/writes under the configured storage root. This is simple and fast for local demos, but large files are still processed synchronously by pandas-oriented services unless callers opt into background jobs.

S3-compatible storage is scaffolded, not production verified. A real object-storage rollout should add streaming uploads/downloads, multipart handling, lifecycle policies, and provider-level metrics.

The frontend code-splits major libraries through Vite/Rollup:

- Recharts is isolated in a `charts` chunk.
- Framer Motion is isolated in a `motion` chunk.
- DataGalaxy and Three.js are lazy-loaded from the upload/dashboard visual areas.

Vite may warn that the lazy `DataGalaxy` chunk is larger than 500 KB after minification. That is expected with Three.js and does not block the main analytics experience because the component is loaded as a decorative enhancement. The visual layer also has WebGL and reduced-motion fallbacks.
