import { writable } from 'svelte/store';

/**
 * Notification object structure:
 * {
 *   id: string,
 *   type: 'budget' | 'task' | 'milestone' | 'system',
 *   message: string,
 *   grant_code: string (optional),
 *   timestamp: Date,
 *   read: boolean
 * }
 */

export const notifications = writable([]);

export function addNotification(type, message, grant_code = '') {
  const newNotification = {
    id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
    type,
    message,
    grant_code,
    timestamp: new Date(),
    read: false
  };

  notifications.update(n => {
    // Avoid duplicates for the same message/grant
    if (n.some(item => item.message === message && item.grant_code === grant_code)) {
      return n;
    }
    return [newNotification, ...n];
  });
}

export function markAsRead(id) {
  notifications.update(n =>
    n.map(item => item.id === id ? { ...item, read: true } : item)
  );
}

export function clearAll() {
  notifications.set([]);
}

export function removeNotification(id) {
  notifications.update(n => n.filter(item => item.id !== id));
}
