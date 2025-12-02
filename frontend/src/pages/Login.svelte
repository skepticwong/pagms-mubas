<!-- src/pages/Login.svelte -->
<script>
  import { router } from '../stores/router.js';
  import { login } from '../stores/auth.js'; // ← Your real auth store

  let email = '';
  let password = '';
  let error = '';
  let isLoading = false;

  // Pre-fill demo accounts for easy testing (optional)
  $: if (!email) {
    email = 'pi@mubas.ac.mw';
    password = 'mubas123';
  }

  async function handleSubmit(event) {
    event.preventDefault();
    error = '';
    isLoading = true;

    const result = await login(email, password);
    if (result.success) {
      router.goToDashboard();
    } else {
      error = result.error;
    }
    isLoading = false;
  }
</script>

<div class="min-h-screen bg-glass-gradient flex items-center justify-center px-4 py-8">
  <div class="w-full max-w-md">
    <div class="glass rounded-2xl shadow-glass-lg p-8 md:p-10">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-secondary mb-2 tracking-tight">PAGMS</h1>
        <p class="text-gray-700 text-base">Post-Award Grant Management System</p>
        <p class="text-sm text-gray-600 mt-1">MUBAS</p>
      </div>
      
      <form on:submit={handleSubmit} class="space-y-6">
        <div class="space-y-4">
          <div>
            <label for="email" class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">
              Email
            </label>
            <input
              id="email"
              type="email"
              class="w-full px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
              bind:value={email}
              placeholder="e.g., pi@mubas.ac.mw"
              required
            />
          </div>
          
          <div>
            <label for="password" class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">
              Password
            </label>
            <input
              id="password"
              type="password"
              class="w-full px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
              bind:value={password}
              placeholder="Enter password"
              required
            />
          </div>
        </div>

        {#if error}
          <div class="text-red-600 text-sm font-medium p-3 bg-red-50/40 backdrop-blur-md rounded-lg border border-red-200/30" role="alert" aria-live="polite">
            {error}
          </div>
        {/if}
        
        <button
          type="submit"
          class="w-full bg-primary/40 backdrop-blur-md border border-white/20 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary/60 hover:shadow-glass-lg focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 transition-all duration-150 shadow-glass"
          disabled={isLoading}
        >
          {isLoading ? 'Signing in...' : 'Sign in to Dashboard'}
        </button>

        <div class="text-center text-sm text-gray-600 mt-4">
          Don't have an account? 
          <button
            type="button"
            on:click={() => router.goToRegister()}
            class="text-primary font-semibold hover:underline focus:outline-none"
          >
            Create one
          </button>
        </div>

        <div class="text-center text-xs text-gray-500 mt-2">
          Demo accounts: pi@mubas.ac.mw, team@mubas.ac.mw, finance@mubas.ac.mw, rsu@mubas.ac.mw<br/>
          Password: <code class="bg-gray-100/80 px-1 rounded">mubas123</code>
        </div>
      </form>
    </div>
  </div>
</div>

<style>
  input:focus {
    outline: none;
  }
</style>