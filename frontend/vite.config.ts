// Input: 上游调用方与同目录文件。
// Output: 输出 vite.config.ts 对应的文本化或代码能力。
// Pos: 仓库受管文件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/",
  server: {
    host: "127.0.0.1",
    port: 5173,
  },
  preview: {
    host: "127.0.0.1",
    port: 4173,
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          "react-vendor": ["react", "react-dom"],
        },
      },
    },
  },
});
