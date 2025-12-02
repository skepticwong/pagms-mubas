import { writable } from 'svelte/store'

// Determine initial route
function getInitialRoute() {
  if (typeof window !== 'undefined') {
    const role = localStorage.getItem('userRole')
    return role ? 'dashboard' : 'login'
  }
  return 'login'
}

function createRouter() {
  const { subscribe, set, update } = writable(getInitialRoute())
  
  return {
    subscribe,
    navigate: (page) => set(page),
    goToLogin: () => {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('userRole')
      }
      set('login')
    },
    goToRegister: () => set('register'),
    goToDashboard: () => set('dashboard')
  }
}

export const router = createRouter()

