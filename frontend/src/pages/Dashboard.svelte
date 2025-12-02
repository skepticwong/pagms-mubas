<script>
  import { onMount } from 'svelte'
  import { router } from '../stores/router.js'
  import FileText from '../components/icons/FileText.svelte'
  import CheckSquare from '../components/icons/CheckSquare.svelte'
  import Users from '../components/icons/Users.svelte'
  import BarChart3 from '../components/icons/BarChart3.svelte'
  import DollarSign from '../components/icons/DollarSign.svelte'
  import CreditCard from '../components/icons/CreditCard.svelte'
  import AlertTriangle from '../components/icons/AlertTriangle.svelte'
  import FileCheck from '../components/icons/FileCheck.svelte'
  import Menu from '../components/icons/Menu.svelte'
  import X from '../components/icons/X.svelte'
  import LogOut from '../components/icons/LogOut.svelte'
  import Lock from '../components/icons/Lock.svelte'
  import Settings from '../components/icons/Settings.svelte'
  
  let userRole = ''
  let sidebarOpen = false
  let userData = null
  let currentPath = '/'
  
  const navigation = {
    'PI': [
      { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
      { name: 'Grants', path: '/dashboard/grants', icon: FileText },
      { name: 'Tasks', path: '/dashboard/tasks', icon: CheckSquare },
      { name: 'Budget', path: '/dashboard/budget', icon: DollarSign },
      { name: 'Team', path: '/dashboard/team', icon: Users },
      { name: 'Reports', path: '/dashboard/reports', icon: FileCheck },
      { name: 'Audit Trail', path: '/dashboard/audit', icon: Lock }
    ],
    'Team Member': [
      { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
      { name: 'My Tasks', path: '/dashboard/tasks', icon: CheckSquare },
      { name: 'Submit Evidence', path: '/dashboard/evidence', icon: FileCheck },
      { name: 'Audit Trail', path: '/dashboard/audit', icon: Lock }
    ],
    'Finance Officer': [
      { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
      { name: 'Budgets', path: '/dashboard/budgets', icon: DollarSign },
      { name: 'Expenses', path: '/dashboard/expenses', icon: CreditCard },
      { name: 'Budget Tracking', path: '/dashboard/budget-tracking', icon: DollarSign },
      { name: 'Reports', path: '/dashboard/reports', icon: FileCheck },
      { name: 'Audit Trail', path: '/dashboard/audit', icon: Lock }
    ],
    'RSU Admin': [
      { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
      { name: 'All Grants', path: '/dashboard/grants', icon: FileText },
      { name: 'Team Management', path: '/dashboard/team', icon: Users },
      { name: 'Risk Monitor', path: '/dashboard/risks', icon: AlertTriangle },
      { name: 'Budget Overview', path: '/dashboard/budgets', icon: DollarSign },
      { name: 'Reports', path: '/dashboard/reports', icon: FileCheck },
      { name: 'Audit Logs', path: '/dashboard/audit', icon: Lock },
      { name: 'Settings', path: '/dashboard/settings', icon: Settings }
    ]
  }
  
  onMount(async () => {
    // Check if user is logged in
    const role = localStorage.getItem('userRole')
    if (!role) {
      router.goToLogin()
      return
    }
    
    userRole = role
    currentPath = window.location.pathname
    
    // Fetch user data from API
    try {
      const response = await fetch('http://localhost:5000/api/me')
      if (response.ok) {
        userData = await response.json()
      }
    } catch (error) {
      console.error('Failed to fetch user data:', error)
    }
  })
  
  function handleLogout() {
    localStorage.removeItem('userRole')
    router.goToLogin()
  }
  
  function getRoleLabel(role) {
    const labels = {
      'PI': 'Principal Investigator',
      'Team Member': 'Team Member',
      'Finance Officer': 'Finance Officer',
      'RSU Admin': 'RSU Administrator'
    }
    return labels[role] || role
  }
  
  function isActive(path) {
    return currentPath === path || currentPath.startsWith(path + '/')
  }
</script>

<div class="min-h-screen bg-gradient-to-br from-blue-100 via-blue-50 to-cyan-100">
  <!-- Top Navigation -->
  <nav class="bg-white/30 backdrop-blur-xl border-b border-white/20 shadow-lg sticky top-0 z-50">
    <div class="px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center gap-4">
          <button
            class="md:hidden p-2 rounded-lg text-gray-900 hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-blue-400/50 transition-all duration-150"
            on:click={() => sidebarOpen = !sidebarOpen}
            aria-label="Toggle sidebar"
          >
            {#if sidebarOpen}
              <X size={24} />
            {:else}
              <Menu size={24} />
            {/if}
          </button>
          <div>
            <h1 class="text-2xl font-bold text-blue-900 tracking-tight">🏥 MUBAS</h1>
            <p class="text-xs text-gray-700">Grant Management System</p>
          </div>
        </div>
        <div class="flex items-center gap-6">
          <div class="hidden sm:flex items-center gap-2">
            <span class="text-sm text-gray-900 font-medium">
              Role:
            </span>
            <span class="text-sm font-semibold text-blue-600 bg-blue-100/50 px-3 py-1 rounded-full backdrop-blur-sm">
              {getRoleLabel(userRole)}
            </span>
          </div>
          <button
            on:click={handleLogout}
            class="flex items-center gap-2 text-sm text-gray-900 hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400/50 rounded-lg px-3 py-2 transition-all duration-150 hover:bg-white/20 backdrop-blur-sm"
            aria-label="Logout"
          >
            <LogOut size={18} />
            <span class="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
    </div>
  </nav>

  <div class="flex">
    <!-- Sidebar -->
    <aside class="bg-white/30 backdrop-blur-xl border-r border-white/20 shadow-lg w-64 fixed h-[calc(100vh-4rem)] md:relative md:h-auto md:translate-x-0 transition-transform duration-300 {sidebarOpen ? 'translate-x-0' : '-translate-x-full'} z-40 overflow-y-auto">
      <nav class="p-4 space-y-1">
        {#each navigation[userRole] || [] as item}
          <a
            href={item.path}
            on:click={() => sidebarOpen = false}
            class="flex items-center px-4 py-3 text-gray-900 rounded-lg font-medium transition-all duration-150 group {isActive(item.path) ? 'bg-blue-500/40 border border-white/40 text-blue-900' : 'hover:bg-white/20 border border-transparent'}"
          >
            <svelte:component
              this={item.icon}
              size={20}
              className="mr-3 {isActive(item.path) ? 'text-blue-700' : 'text-blue-600 group-hover:text-blue-700'} transition-colors duration-150"
            />
            <span class="text-base">{item.name}</span>
          </a>
        {/each}
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 p-4 sm:p-6 lg:p-8 min-h-[calc(100vh-4rem)]">
      <div class="max-w-7xl mx-auto space-y-6">
        <!-- Header -->
        <div class="space-y-2">
          <h2 class="text-4xl font-bold text-gray-900 tracking-tight">
            Welcome back, {userData?.name || getRoleLabel(userRole)}
          </h2>
          <p class="text-gray-700 text-base">
            {#if userData}
              {userData.email}
            {:else}
              Manage your grants, tasks, and budgets from here.
            {/if}
          </p>
        </div>

        <!-- Quick Stats -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-blue-500/40 backdrop-blur-xl border border-white/30 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-150 hover:bg-blue-500/50">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-white/80 font-medium">Active Grants</p>
                <p class="text-3xl font-bold text-white mt-2">8</p>
              </div>
              <FileText size={32} className="text-white/40" />
            </div>
          </div>

          <div class="bg-amber-500/40 backdrop-blur-xl border border-white/30 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-150 hover:bg-amber-500/50">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-white/80 font-medium">Pending Tasks</p>
                <p class="text-3xl font-bold text-white mt-2">12</p>
              </div>
              <CheckSquare size={32} className="text-white/40" />
            </div>
          </div>

          <div class="bg-emerald-500/40 backdrop-blur-xl border border-white/30 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-150 hover:bg-emerald-500/50">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-white/80 font-medium">Budget Used</p>
                <p class="text-3xl font-bold text-white mt-2">33%</p>
              </div>
              <DollarSign size={32} className="text-white/40" />
            </div>
          </div>

          <div class="bg-rose-500/40 backdrop-blur-xl border border-white/30 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-150 hover:bg-rose-500/50">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-white/80 font-medium">Alerts</p>
                <p class="text-3xl font-bold text-white mt-2">3</p>
              </div>
              <AlertTriangle size={32} className="text-white/40" />
            </div>
          </div>
        </div>

        <!-- Main Card -->
        <div class="bg-white/40 backdrop-blur-xl border border-white/30 rounded-2xl shadow-lg p-8 hover:shadow-xl transition-all duration-150">
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Getting Started</h3>
          <p class="text-gray-800 text-base leading-relaxed mb-6">
            Welcome to MUBAS, the comprehensive post-war grant management system. Use the sidebar navigation to access different sections based on your role.
          </p>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-blue-100/30 backdrop-blur-sm border border-blue-200/40 rounded-lg p-4">
              <p class="font-semibold text-gray-900 mb-2">📋 Manage Grants</p>
              <p class="text-sm text-gray-700">Register, track, and modify grants with real-time budget monitoring.</p>
            </div>
            <div class="bg-blue-100/30 backdrop-blur-sm border border-blue-200/40 rounded-lg p-4">
              <p class="font-semibold text-gray-900 mb-2">✓ Track Tasks</p>
              <p class="text-sm text-gray-700">Assign tasks, collect evidence, and manage team workflows efficiently.</p>
            </div>
            <div class="bg-blue-100/30 backdrop-blur-sm border border-blue-200/40 rounded-lg p-4">
              <p class="font-semibold text-gray-900 mb-2">💰 Control Budget</p>
              <p class="text-sm text-gray-700">Monitor spending, approve expenses, and generate comprehensive reports.</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- Mobile overlay -->
  {#if sidebarOpen}
    <div
      class="fixed inset-0 bg-black/20 backdrop-blur-sm z-30 md:hidden"
      on:click={() => sidebarOpen = false}
      on:keydown={(e) => e.key === 'Escape' && (sidebarOpen = false)}
      role="button"
      tabindex="0"
      aria-label="Close sidebar"
    ></div>
  {/if}
</div>

<style>
  :global(body) {
    @apply bg-gradient-to-br from-blue-100 via-blue-50 to-cyan-100;
  }
</style>