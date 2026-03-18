/**
 * Investor-path copy hardening: strip eval/benchmark noise from live backend strings.
 */

const ENGINEERING_TOKENS =
  /\b(bleu|benchmark|f1\s*score|\bf1\b|p95|p99|latency\s*\d|token\s*count|eval\s*run|ground\s*truth|ablation|rouge|perplexity|hallucination\s*rate)\b/i;

/** Split on sentence boundaries (rough). */
function sentences(s: string): string[] {
  return (s || '')
    .split(/(?<=[.!?])\s+/)
    .map((x) => x.trim())
    .filter(Boolean);
}

/**
 * Remove sentences that read like benchmarks or evals; fall back if nothing left.
 */
export function softenEngineeringCopy(text: string, fallback: string): string {
  const t = (text || '').trim();
  if (!t) return fallback;
  const kept = sentences(t).filter((sent) => !ENGINEERING_TOKENS.test(sent));
  const out = kept.join(' ').trim();
  if (out.length >= 20) return out;
  return fallback;
}

export function capInvestorLine(s: string, max: number): string {
  const t = (s || '').trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max - 1)}…`;
}
