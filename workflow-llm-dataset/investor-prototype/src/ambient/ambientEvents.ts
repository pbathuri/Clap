type AmbientPulseDetail = {
  intensity: number;
};

const AMBIENT_EVENT = 'ambient-pulse';
const ambientBus = new EventTarget();

export function triggerAmbientPulse(intensity = 1): void {
  ambientBus.dispatchEvent(
    new CustomEvent<AmbientPulseDetail>(AMBIENT_EVENT, {
      detail: { intensity },
    })
  );
}

export function subscribeAmbientPulse(
  handler: (detail: AmbientPulseDetail) => void
): () => void {
  const listener = (event: Event) => {
    const custom = event as CustomEvent<AmbientPulseDetail>;
    handler(custom.detail);
  };
  ambientBus.addEventListener(AMBIENT_EVENT, listener);
  return () => ambientBus.removeEventListener(AMBIENT_EVENT, listener);
}
