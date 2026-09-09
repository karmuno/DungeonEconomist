import { createApp } from 'vue'
import { createPinia } from 'pinia'
import * as Sentry from '@sentry/vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

// Gated on the DSN exactly like the backend, so local dev reports nothing.
// Errors only: no tracing, no session replay.
if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    app,
    dsn: import.meta.env.VITE_SENTRY_DSN,
    // 'development' under `npm run dev`, 'production' in a build, so local
    // debugging does not pollute the cohort's errors.
    environment: import.meta.env.MODE,
    integrations: [],
    tracesSampleRate: 0,
    // Same build string as the version badge, so an error names the build it came from.
    release: __APP_VERSION__,
  })
}

app.use(createPinia())
app.use(router)

app.mount('#app')
