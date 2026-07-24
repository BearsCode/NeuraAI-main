export function isValidRedirect(path: string): boolean {
  try {
    const url = new URL(path, "http://localhost");
    return url.origin === "http://localhost" && path.startsWith("/");
  } catch {
    return false;
  }
}
