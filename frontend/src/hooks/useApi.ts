export type Ok<T> = { ok: true; data: T };
export type Err = { ok: false; error: { code: string; message: string } };
export type J<T> = Ok<T> | Err;

export function useApi(baseUrl: string) {
  async function get<T>(p: string): Promise<J<T>> {
    const r = await fetch(`${baseUrl}${p}`);
    return r.json();
  }
  async function post<T>(p: string, body: any): Promise<J<T>> {
    const r = await fetch(`${baseUrl}${p}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return r.json();
  }
  return { get, post };
}
