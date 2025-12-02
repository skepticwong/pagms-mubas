<script>
  import { router } from './stores/router.js'
  import Login from './pages/Login.svelte'
  import Register from './pages/Register.svelte'
  import Dashboard from './pages/Dashboard.svelte'
</script>

{#if $router === 'login'}
  <Login />
{:else if $router === 'register'}
  <Register />
{:else if $router === 'dashboard'}
  <Dashboard />
{/if}

