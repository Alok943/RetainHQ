import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { sentryVitePlugin } from '@sentry/vite-plugin'

const SENTRY_UPLOAD_ENABLED = !!process.env.SENTRY_AUTH_TOKEN;

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Uploads sourcemaps so Sentry can de-minify stack traces. Silent no-op
    // without SENTRY_AUTH_TOKEN (a build-time secret, never in Vercel's
    // client-exposed VITE_* vars) — safe on every branch/PR build.
    sentryVitePlugin({
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
      disable: !SENTRY_UPLOAD_ENABLED,
      sourcemaps: {
        // Sourcemaps are uploaded to Sentry, then removed from the deployed
        // dist/ — they never ship publicly (source shouldn't be fetchable).
        filesToDeleteAfterUpload: ['./dist/**/*.map'],
      },
    }),
  ],
  build: {
    // Only generate maps when there's a token to upload+delete them (see
    // above). Without a token nothing would strip them post-build, so they'd
    // sit in dist/ and Vercel would serve full source publicly — worse than
    // no sourcemaps at all. 'hidden' = no //# sourceMappingURL comment, so
    // even when enabled, only Sentry's direct upload sees the map.
    sourcemap: SENTRY_UPLOAD_ENABLED ? 'hidden' : false,
  },
})
