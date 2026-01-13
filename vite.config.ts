import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    allowedHosts: [
      '64b26497cee8.ngrok-free.app', // Tu dominio de ngrok
      '.ngrok-free.app', // Permite todos los subdominios de ngrok
      '.ngrok.io', // Por si usas el dominio antiguo
    ],
    port: 8080,
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
