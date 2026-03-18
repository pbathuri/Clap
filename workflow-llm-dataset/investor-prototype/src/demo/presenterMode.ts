/** Shared detection for presenter overlay + presenter-only chrome (e.g. Reset demo). */
export function isPresenterDemoMode(): boolean {
  if (typeof window === 'undefined') return false;
  if (new URLSearchParams(window.location.search).get('presenter') === '1')
    return true;
  return import.meta.env.VITE_PRESENTER_OVERLAY === '1';
}
