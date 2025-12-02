<!-- src/pages/Register.svelte -->
<script>
  import { router } from '../stores/router.js';
  import { register } from '../stores/auth.js';

  let name = '';
  let email = '';
  let password = '';
  let confirmPassword = '';
  let role = 'Team';
  let payRate = '';
  let error = '';
  let isLoading = false;

  const roles = [
    { value: 'PI', label: 'Principal Investigator' },
    { value: 'Team', label: 'Team Member' },
    { value: 'Finance', label: 'Finance Officer' },
    { value: 'RSU', label: 'RSU Admin' }
  ];

  async function handleSubmit(event) {
    event.preventDefault();
    error = '';
    isLoading = true;

    // Validation
    if (!name || !email || !password || !confirmPassword) {
      error = 'All fields are required';
      isLoading = false;
      return;
    }

    if (password !== confirmPassword) {
      error = 'Passwords do not match';
      isLoading = false;
      return;
    }

    if (password.length < 6) {
      error = 'Password must be at least 6 characters';
      isLoading = false;
      return;
    }

    const result = await register(
      name,
      email,
      password,
      role,
      payRate ? parseFloat(payRate) : null
    );

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
        <h1 class="text-3xl font-bold text-secondary mb-2 tracking-tight">Create Account</h1>
        <p class="text-gray-700 text-base">Post-Award Grant Management System</p>
        <p class="text-sm text-gray-600 mt-1">MUBAS</p>
      </div>
      
      <form on:submit={handleSubmit} class="space-y-6">
        <div class="space-y-4">
          <div>
            <label for="name" class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              class="w-full px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
              bind:value={name}
              placeholder="e.g., Dr. John Doe"
              required
            />
          </div>

          <div>
            <label for="email" class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">
              Email
            </label>
            <input
              id="email"
              type="email"
              class="w-full px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
              bind:value={email}
              placeholder="e.g., john.doe@mubas.ac.mw"
              required
            />
          </div>

          <div>
            <label for="role" class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">
              Role
            </label>
            <select
              id="role"
              class="w-full px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
              bind:value={role}
              required
            >
              {#each roles as roleOption}
                <option value={roleOption.value}>{roleOption.label}</option>
              {/each}
            </select>
          </div>

          <div>
            <label for="payRate" class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">
              Pay Rate (Optional)
            </label>
            <input
              id="payRate"
              type="number"
              step="0.01"
              min="0"
              class="w-full px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
              bind:value={payRate}
              placeholder="e.g., 25.50"
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
              placeholder="At least 6 characters"
              required
              minlength="6"
            />
          </div>

          <div>
            <label for="confirmPassword" class="block text-xs font-semibold text-gray-900 mb-2 uppercase tracking-wide">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              class="w-full px-4 py-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
              bind:value={confirmPassword}
              placeholder="Re-enter password"
              required
              minlength="6"
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
          {isLoading ? 'Creating Account...' : 'Create Account'}
        </button>

        <div class="text-center text-sm text-gray-600 mt-4">
          Already have an account? 
          <button
            type="button"
            on:click={() => router.goToLogin()}
            class="text-primary font-semibold hover:underline focus:outline-none"
          >
            Sign in
          </button>
        </div>
      </form>
    </div>
  </div>
</div>

<style>
  input:focus,
  select:focus {
    outline: none;
  }
</style>

