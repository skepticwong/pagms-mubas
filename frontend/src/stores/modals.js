import { writable } from "svelte/store";

/**
 * @typedef {Object} ModalState
 * @property {'confirm' | 'prompt'} type
 * @property {string} message
 * @property {string} [defaultValue]
 * @property {(value: any) => void} resolve
 * @property {(reason?: any) => void} reject
 */

/** @type {import('svelte/store').Writable<ModalState | null>} */
export const modal = writable(null);

/**
 * Show a system-based confirmation modal.
 * @param {string} message
 * @returns {Promise<boolean>}
 */
export function confirm(message) {
  return new Promise((resolve) => {
    modal.set({
      type: 'confirm',
      message,
      resolve: (val) => {
        modal.set(null);
        resolve(val);
      },
      reject: () => {
        modal.set(null);
        resolve(false);
      }
    });
  });
}

/**
 * Show a system-based prompt modal.
 * @param {string} message
 * @param {string} [defaultValue]
 * @returns {Promise<string | null>}
 */
export function prompt(message, defaultValue = "") {
  return new Promise((resolve) => {
    modal.set({
      type: 'prompt',
      message,
      defaultValue,
      resolve: (val) => {
        modal.set(null);
        resolve(val);
      },
      reject: () => {
        modal.set(null);
        resolve(null);
      }
    });
  });
}

export function closeModal() {
  modal.update(state => {
    if (state) state.resolve(null);
    return null;
  });
}
