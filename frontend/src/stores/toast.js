import { writable } from "svelte/store";

/** @type {import('svelte/store').Writable<{ message: string; type: 'success' | 'error' | 'info'; id: number } | null>} */
export const toast = writable(null);

let seq = 0;

/**
 * Show an in-app toast (not window.alert).
 * @param {string} message
 * @param {'success'|'error'|'info'} [type]
 * @param {number} [durationMs]
 */
export function showToast(message, type = "info", durationMs = 4200) {
  const id = ++seq;
  toast.set({ id, message, type });
  if (durationMs > 0) {
    setTimeout(() => {
      toast.update((t) => (t && t.id === id ? null : t));
    }, durationMs);
  }
}

export function dismissToast() {
  toast.set(null);
}
