import { defineConfig, loadEnv } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": {
          target: env.API_URL || "http://127.0.0.1:8000",
          changeOrigin: true,
          rewrite: p => p.replace(/^\/api/, ""),
          headers: { "X-Api-Key": env.API_KEY || "" },
        },
      },
    },
  }
})