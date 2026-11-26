const path = "/invitacion";
const pathPattern = /^\/invitacion(?:\/([\w-]+))?\/?$/;

export function isInvitationPage(pathname: string) {
  return pathPattern.test(pathname);
}

export function invitationToken(pathname: string, search: string) {
  const match = pathPattern.exec(pathname);
  if (!match) return "";
  return match[1] ?? new URLSearchParams(search).get("token") ?? "";
}

export function invitationPath(token = "", language?: string) {
  const route = token ? `${path}/${encodeURIComponent(token)}` : path;
  return language === "en" ? `${route}?lang=en` : route;
}

export function parseInvitation(input: string) {
  const value = input.trim();
  if (/^[\w-]+$/.test(value)) return value;
  try {
    const url = new URL(value, window.location.origin);
    const token = invitationToken(url.pathname, url.search);
    return /^[\w-]+$/.test(token) ? token : "";
  } catch {
    return "";
  }
}
