// frontend/src/hooks/useApi.ts
export type Ok<T> = { ok: true; data: T };
export type Err = { ok: false; error: { code: string; message: string } };
export type J<T> = Ok<T> | Err;

function getDefaultBase(): string {
  try {
    const fromLocal = window.localStorage.getItem("baseUrl");
    if (fromLocal && fromLocal.trim()) return fromLocal.trim();
  } catch {}
  const fromEnv = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined;
  if (fromEnv && fromEnv.trim()) return fromEnv.trim();
  return "/api"; // פיתוח דרך פרוקסי של Vite
}

export function useApi(baseUrl?: string) {
  const base = (baseUrl && baseUrl.trim()) || getDefaultBase();

  async function get<T>(p: string): Promise<J<T>> {
    try {
      const r = await fetch(`${base}${p}`);
      return r.json();
    } catch (e: any) {
      return { ok: false, error: { code: "network_error", message: e?.message || "Network error" } };
    }
  }

  async function post<T>(p: string, body: any): Promise<J<T>> {
    try {
      const r = await fetch(`${base}${p}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return r.json();
    } catch (e: any) {
      return { ok: false, error: { code: "network_error", message: e?.message || "Network error" } };
    }
  }

  return { get, post, base };
}

