const MAX_HOSTNAME_LEN = 253;
const MAX_LABEL_LEN = 63;
const LABEL_RE = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$/;

function normalizeWhitelistEntry(rawValue: string): string {
  let value = rawValue.trim().toLowerCase();
  if (!value) {
    return "";
  }

  if (value.includes("://")) {
    try {
      value = new URL(value).hostname;
    } catch {
      return "";
    }
  } else {
    value = value.split("/", 1)[0];
    if (value.includes("@")) {
      value = value.split("@").at(-1) ?? "";
    }
    if ((value.match(/:/g) ?? []).length === 1) {
      const [host, port] = value.split(":");
      if (port && /^\d+$/.test(port)) {
        value = host;
      }
    }
  }

  value = value.trim().replace(/\.+$/, "");
  if (value.startsWith("*.")) {
    value = value.slice(2);
  }

  return value;
}

function isValidIpv4(host: string): boolean {
  const parts = host.split(".");
  if (parts.length !== 4) {
    return false;
  }

  return parts.every(
    (part) => /^\d+$/.test(part) && Number(part) >= 0 && Number(part) <= 255,
  );
}

function isValidIpv6(host: string): boolean {
  try {
    return new URL(`http://[${host}]`).hostname === `[${host}]`;
  } catch {
    return false;
  }
}

function validateWhitelistHost(host: string): string {
  if (!host || host.length > MAX_HOSTNAME_LEN) {
    throw new Error("Ungültiger Host- oder Adresseintrag");
  }

  if (isValidIpv4(host) || isValidIpv6(host)) {
    return host;
  }

  let asciiHost: string;
  try {
    asciiHost = new URL(`http://${host}`).hostname;
  } catch {
    throw new Error("Ungültiger Host- oder Adresseintrag");
  }

  if (
    !asciiHost ||
    asciiHost.includes("..") ||
    asciiHost.startsWith(".") ||
    asciiHost.endsWith(".")
  ) {
    throw new Error("Ungültiger Host- oder Adresseintrag");
  }

  const labels = asciiHost.split(".");
  if (labels.length === 0 || labels.length > 127 || labels.length < 2) {
    throw new Error("Ungültiger Host- oder Adresseintrag");
  }

  for (const label of labels) {
    if (!label || label.length > MAX_LABEL_LEN || !LABEL_RE.test(label)) {
      throw new Error("Ungültiger Host- oder Adresseintrag");
    }
  }

  return asciiHost.toLowerCase();
}

export function parseWhitelistUrlEntry(rawValue: string): string | null {
  const normalized = normalizeWhitelistEntry(rawValue);
  if (!normalized) {
    return null;
  }

  try {
    return validateWhitelistHost(normalized);
  } catch {
    throw new Error(`Ungültiger Whitelist-Eintrag: ${rawValue.trim()}`);
  }
}

export function parseWhitelistUrlList(rawValue: string): string[] {
  const cleaned: string[] = [];
  const seen = new Set<string>();

  for (const line of rawValue.split("\n")) {
    const canonical = parseWhitelistUrlEntry(line);
    if (!canonical || seen.has(canonical)) {
      continue;
    }
    seen.add(canonical);
    cleaned.push(canonical);
  }

  return cleaned;
}
