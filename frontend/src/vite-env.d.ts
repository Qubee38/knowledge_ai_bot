/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  // 他の環境変数を追加する場合はここに定義
  readonly VITE_OTHER_VAR: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}