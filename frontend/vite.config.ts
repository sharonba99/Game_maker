// frontend/vite.config.ts
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default ({ mode }: { mode: string }) => {
  const rootEnv = loadEnv(mode, path.resolve(__dirname, ".."), ""); // קורא .env מהשורש
  const API_BASE = rootEnv.VITE_API_BASE_URL || "http://localhost:5001";

  return defineConfig({
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
        "@pages": path.resolve(__dirname, "src/pages"),
        "@components": path.resolve(__dirname, "src/components"),
        "@hooks": path.resolve(__dirname, "src/hooks"),
        "@utils": path.resolve(__dirname, "src/utils"),
        "@types": path.resolve(__dirname, "src/types"),
      },
    },
    define: {
      __API_BASE__: JSON.stringify(API_BASE), // ✅ קונסטנט גלובלי
    },
  });
};
