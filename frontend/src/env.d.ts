declare const __APP_VERSION__: string

interface ImportMetaEnv {
  /** Sentry DSN for frontend error tracking. Absent locally, so init is skipped. */
  readonly VITE_SENTRY_DSN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
