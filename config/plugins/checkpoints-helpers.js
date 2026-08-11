export const SKIP_PATTERNS = [
  /node_modules/,
  /\.git\//,
  /\.local\/share\/opencode\/plugins-data/,
  /(?:^|\/)\.env(?:$|\.)/,
  /id_rsa/i,
  /id_ed25519/i,
  /id_ecdsa/i,
  /id_dsa/i,
  /\.pem$/i,
  /\.key$/i,
  /\.pfx$/i,
  /\.p12$/i,
  /credentials\.json$/i,
  /service-account.*\.json$/i,
];

export function isSkippable(absPath) {
  return SKIP_PATTERNS.some((p) => p.test(absPath));
}
