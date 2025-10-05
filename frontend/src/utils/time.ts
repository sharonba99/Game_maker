export const TIME_LIMIT_SEC = 20;

export function msToSec(ms: number) {
  return Math.max(0, Math.round(ms / 100) / 10); // 0.1s precision
}
