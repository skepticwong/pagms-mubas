import { writable } from 'svelte/store';

const initialId = typeof window !== 'undefined'
  ? window.sessionStorage.getItem('currentGrantBudgetId')
  : null;

const { subscribe, set } = writable(initialId);

function persist(id) {
  if (typeof window !== 'undefined') {
    if (id) {
      window.sessionStorage.setItem('currentGrantBudgetId', id);
    } else {
      window.sessionStorage.removeItem('currentGrantBudgetId');
    }
  }
}

export const currentGrantBudgetId = {
  subscribe,
  set(id) {
    persist(id);
    set(id);
  }
};

export function selectGrantBudget(id) {
  currentGrantBudgetId.set(id ? String(id) : null);
}

export function clearGrantBudgetSelection() {
  currentGrantBudgetId.set(null);
}
