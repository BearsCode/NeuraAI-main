const backendBaseUrl = process.env.NEURAAI_BACKEND_URL ?? "http://127.0.0.1:8000";
const apiPrefix = process.env.NEURAAI_API_PREFIX ?? "/api/v1";

function normalizePrefix(prefix: string): string {
  if (!prefix.startsWith("/")) {
    return `/${prefix}`;
  }
  return prefix.endsWith("/") ? prefix.slice(0, -1) : prefix;
}

export function buildBackendUrl(path: string): string {
  const normalizedPrefix = normalizePrefix(apiPrefix);
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return new URL(`${normalizedPrefix}${normalizedPath}`, backendBaseUrl).toString();
}

export async function backendRequest(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  return fetch(buildBackendUrl(path), {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
}

export async function readJson<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

export async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as {
      detail?: string;
      message?: string;
      error?: { message?: string };
    };
    return (
      payload.detail ??
      payload.message ??
      payload.error?.message ??
      `Request failed with status ${response.status}`
    );
  } catch {
    return `Request failed with status ${response.status}`;
  }
}
