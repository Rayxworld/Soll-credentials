const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://soll-credentialsapi.onrender.com"
).replace(/\/$/, "");

const CSRF_STORAGE_KEY = "soll_csrf_token";

export type AuthenticatedUser = {
  id: string;
  email: string;
};

export type Organization = {
  id: string;
  name: string;
  slug: string;
  role: "owner" | "admin" | "issuer";
  is_active: boolean;
  chain_registered: boolean;
  created_at: string;
};

type ApiErrorBody = { detail?: string | { msg?: string }[] };

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export function saveCsrfToken(token: string) {
  if (typeof window !== "undefined") {
    window.sessionStorage.setItem(CSRF_STORAGE_KEY, token);
  }
}

export function getCsrfToken() {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(CSRF_STORAGE_KEY);
}

export function clearCsrfToken() {
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem(CSRF_STORAGE_KEY);
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const method = (options.method ?? "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    method,
    headers,
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        message = body.detail[0].msg;
      }
    } catch {
      // Keep the safe status-based message when the response is not JSON.
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function ensureCsrfToken() {
  if (getCsrfToken()) return;
  const result = await apiRequest<{ csrf_token: string }>("/api/v1/auth/csrf", {
    method: "POST",
  });
  saveCsrfToken(result.csrf_token);
}
