/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly MODE: string;
  // להוסיף כאן עוד משתנים אם יהיו בעתיד
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
