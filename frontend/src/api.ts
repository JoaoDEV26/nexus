// Access token somente em memória. Cookie HttpOnly é enviado pelo navegador.
let token = "";
let refreshing: Promise<boolean> | null = null;
export function setToken(value: string) {
  token = value;
}
export async function renew(): Promise<boolean> {
  if (!refreshing)
    refreshing = fetch("/api/v1/auth/refresh", {
      method: "POST",
      credentials: "include",
    })
      .then(async (r) => {
        if (!r.ok) {
          token = "";
          return false;
        }
        token = (await r.json()).access_token;
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshing = null;
      });
  return refreshing;
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  retry = true,
): Promise<T> {
  const r = await fetch("/api/v1" + path, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (r.status === 401 && retry && !path.startsWith("/auth/")) {
    if (await renew()) return api<T>(path, method, body, false);
    window.dispatchEvent(new Event("session-ended"));
  }
  if (!r.ok) {
    const data = await r.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Confira os campos e tente novamente.",
    );
  }
  return r.status === 204 ? (undefined as T) : r.json();
}
export type Org = {
  id: string;
  name: string;
  role: string;
  membership_id: string;
};
export type Member = { id: string; name: string; email: string; role: string };
export type Project = {
  id: string;
  name: string;
  description: string;
  status: string;
};
export type Task = {
  id: string;
  project_id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  assignee_id: string | null;
  due_date: string | null;
  archived: boolean;
};
export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};
export type Activity = {
  id: string;
  action: string;
  entity_id: string;
  changes: Record<string, unknown>;
  created_at: string;
};
