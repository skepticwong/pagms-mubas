import { writable } from 'svelte/store';

const rsuNavTarget = writable(null);

const setRsuNavTarget = (sectionId) => {
  rsuNavTarget.set(sectionId);
};

const clearRsuNavTarget = () => {
  rsuNavTarget.set(null);
};

export { rsuNavTarget, setRsuNavTarget, clearRsuNavTarget };
