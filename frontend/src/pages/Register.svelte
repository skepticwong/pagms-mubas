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
   // { value: 'RSU', label: 'RSU Admin' }
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
  <div class="w-full max-w-6xl">
    <div class="glass rounded-3xl shadow-glass-lg overflow-hidden">
      <div class="grid md:grid-cols-2 gap-0">
        <!-- Left Column - Form -->
        <div class="p-8 md:p-12 lg:p-16 max-h-screen overflow-y-auto">
          <div class="mb-6">
            <div class="flex items-center gap-3 mb-6">
              <!-- MUBAS Logo -->
              <img 
                src="/src/images/mubas-logo-full.png" 
                alt="MUBAS Logo" 
                class="h-12 w-auto object-contain"
                on:error={(e) => { e.target.style.display='none'; e.target.nextElementSibling.style.display='flex'; }}
              />
              <!-- Fallback logo if image doesn't load -->
              <div class="hidden w-12 h-12 bg-primary/20 backdrop-blur-md rounded-full items-center justify-center border-2 border-primary/30">
                <span class="text-primary font-bold text-xl">M</span>
              </div>
              <div>
                <h1 class="text-2xl font-bold text-secondary tracking-tight">PAGMS</h1>
                <p class="text-xs text-gray-600">MUBAS</p>
              </div>
            </div>
            <h2 class="text-3xl font-bold text-secondary mb-2">Join us today!</h2>
            <p class="text-gray-600 text-sm">Create your account and start managing grants efficiently.</p>
          </div>
          
          <form on:submit={handleSubmit} class="space-y-4">
            <div>
              <input
                id="name"
                type="text"
                class="w-full px-4 py-3 bg-white/50 backdrop-blur-md border border-gray-300/50 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                bind:value={name}
                placeholder="Full Name"
                required
              />
            </div>

            <div>
              <input
                id="email"
                type="email"
                class="w-full px-4 py-3 bg-white/50 backdrop-blur-md border border-gray-300/50 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                bind:value={email}
                placeholder="Email"
                required
              />
            </div>

            <div>
              <select
                id="role"
                class="w-full px-4 py-3 bg-white/50 backdrop-blur-md border border-gray-300/50 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                bind:value={role}
                required
              >
                {#each roles as roleOption}
                  <option value={roleOption.value}>{roleOption.label}</option>
                {/each}
              </select>
            </div>

            <div>
              <input
                id="payRate"
                type="number"
                step="0.01"
                min="0"
                class="w-full px-4 py-3 bg-white/50 backdrop-blur-md border border-gray-300/50 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                bind:value={payRate}
                placeholder="Pay Rate (Optional)"
              />
            </div>
            
            <div>
              <input
                id="password"
                type="password"
                class="w-full px-4 py-3 bg-white/50 backdrop-blur-md border border-gray-300/50 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                bind:value={password}
                placeholder="Password (min. 6 characters)"
                required
                minlength="6"
              />
            </div>

            <div>
              <input
                id="confirmPassword"
                type="password"
                class="w-full px-4 py-3 bg-white/50 backdrop-blur-md border border-gray-300/50 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                bind:value={confirmPassword}
                placeholder="Confirm Password"
                required
                minlength="6"
              />
            </div>

            {#if error}
              <div class="text-red-600 text-sm font-medium p-3 bg-red-50/40 backdrop-blur-md rounded-lg border border-red-200/30" role="alert" aria-live="polite">
                {error}
              </div>
            {/if}
            
            <button
              type="submit"
              class="w-full bg-secondary text-white py-3 px-6 rounded-xl font-semibold hover:bg-secondary/90 focus:outline-none focus:ring-2 focus:ring-secondary focus:ring-offset-2 transition-all duration-150 shadow-lg"
              disabled={isLoading}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>

            <div class="text-center text-sm text-gray-600">
              or continue with
            </div>

            <div class="flex justify-center gap-4">
              <button type="button" class="w-12 h-12 bg-secondary text-white rounded-full flex items-center justify-center hover:bg-secondary/90 transition-all shadow-md">
                <span class="text-lg font-bold">G</span>
              </button>
              <button type="button" class="w-12 h-12 bg-secondary text-white rounded-full flex items-center justify-center hover:bg-secondary/90 transition-all shadow-md">
                <span class="text-lg">🍎</span>
              </button>
              <button type="button" class="w-12 h-12 bg-secondary text-white rounded-full flex items-center justify-center hover:bg-secondary/90 transition-all shadow-md">
                <span class="text-lg font-bold">f</span>
              </button>
            </div>

            <div class="text-center text-sm text-gray-600 mt-6">
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

        <!-- Right Column - Illustration -->
        <div class="bg-gradient-to-br from-primary/5 via-primary/10 to-accent/10 p-8 md:p-12 flex flex-col items-center justify-center relative overflow-hidden">
          <!-- Decorative circles -->
          <div class="absolute top-10 right-10 w-20 h-20 bg-primary/10 rounded-full blur-2xl"></div>
          <div class="absolute bottom-20 left-10 w-32 h-32 bg-accent/10 rounded-full blur-3xl"></div>
          
          <!-- Main illustration area -->
          <div class="relative z-10 text-center space-y-8">
            <!-- Central illustration -->
            <div class="relative inline-block">
              <!-- Team collaboration -->
              <div class="w-64 h-64 mx-auto mb-6 relative">
                <div class="absolute inset-0 bg-primary/5 rounded-full"></div>
                <!-- Central icon -->
                <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <div class="w-32 h-32 bg-primary/20 rounded-full flex items-center justify-center border-4 border-primary/30">
                    <div class="text-5xl">🎯</div>
                  </div>
                </div>
                
                <!-- Floating team members -->
                <div class="absolute top-4 left-12 w-16 h-16 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center border-2 border-primary/20 shadow-lg animate-float">
                  <div class="text-2xl">👨‍🔬</div>
                </div>
                <div class="absolute top-12 right-8 w-14 h-14 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center border-2 border-accent/20 shadow-lg animate-float-delayed">
                  <div class="text-xl">👩‍💼</div>
                </div>
                <div class="absolute bottom-16 left-4 w-12 h-12 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center border-2 border-primary/20 shadow-lg animate-float">
                  <div class="text-lg">👨‍💻</div>
                </div>
                <div class="absolute bottom-8 right-12 w-14 h-14 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center border-2 border-accent/20 shadow-lg animate-float-delayed">
                  <div class="text-xl">👩‍🎓</div>
                </div>
              </div>

              <!-- Feature cards -->
              <div class="space-y-3">
                <div class="inline-block bg-white/90 backdrop-blur-md rounded-2xl p-3 shadow-glass-lg border border-white/50">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center">
                      <span class="text-xl">📊</span>
                    </div>
                    <div class="text-left">
                      <div class="font-semibold text-secondary text-sm">Grant Tracking</div>
                      <div class="text-xs text-gray-600">Real-time updates</div>
                    </div>
                  </div>
                </div>
                
                <div class="inline-block bg-white/90 backdrop-blur-md rounded-2xl p-3 shadow-glass-lg border border-white/50">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-accent/20 rounded-lg flex items-center justify-center">
                      <span class="text-xl">👥</span>
                    </div>
                    <div class="text-left">
                      <div class="font-semibold text-secondary text-sm">Team Collaboration</div>
                      <div class="text-xs text-gray-600">Work together</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Bottom text -->
            <div class="space-y-2">
              <h3 class="text-xl font-bold text-secondary">
                Start your journey with us
              </h3>
              <p class="text-sm text-gray-600">
                Join <span class="font-semibold text-primary">PAGMS</span> community today
              </p>
            </div>

            <!-- Pagination dots -->
            <div class="flex justify-center gap-2 pt-4">
              <div class="w-2 h-2 rounded-full bg-gray-400"></div>
              <div class="w-6 h-2 rounded-full bg-secondary"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  input:focus,
  select:focus {
    outline: none;
  }

  @keyframes float {
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-10px);
    }
  }

  .animate-float {
    animation: float 3s ease-in-out infinite;
  }

  .animate-float-delayed {
    animation: float 3s ease-in-out infinite;
    animation-delay: 1.5s;
  }

  /* Custom scrollbar for form area */
  .overflow-y-auto::-webkit-scrollbar {
    width: 6px;
  }

  .overflow-y-auto::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }

  .overflow-y-auto::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 10px;
  }

  .overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.3);
  }
</style>