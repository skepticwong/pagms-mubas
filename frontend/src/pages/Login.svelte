<!-- src/pages/Login.svelte -->
<script>
  import { router } from "../stores/router.js";
  import { login } from "../stores/auth.js"; // ← Your real auth store

  let email = "";
  let password = "";
  let error = "";
  let isLoading = false;

  // Pre-fill demo accounts for easy testing (optional)
  $: if (!email) {
    email = "pi@mubas.ac.mw";
    password = "mubas123";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    error = "";
    isLoading = true;

    const result = await login(email, password);
    if (result.success) {
      const role = result.user?.role || result.role;
      if (router.goToRoleHome) {
        router.goToRoleHome(role);
      } else {
        router.goToDashboard();
      }
    } else {
      error = result.error;
    }

    isLoading = false;
  }
</script>

<div
  class="min-h-screen bg-glass-gradient flex items-center justify-center px-4 py-8"
>
  <div class="w-full max-w-6xl">
    <div class="glass rounded-3xl shadow-glass-lg overflow-hidden">
      <div class="grid md:grid-cols-2 gap-0">
        <!-- Left Column - Form -->
        <div class="p-8 md:p-12 lg:p-16">
          <div class="mb-8">
            <div class="flex items-center gap-3 mb-6">
              <!-- MUBAS Logo -->
              <img
                src="/src/images/mubas-logo-full.png"
                alt="MUBAS Logo"
                class="h-12 w-auto object-contain"
                on:error={(e) => {
                  e.target.style.display = "none";
                  e.target.nextElementSibling.style.display = "flex";
                }}
              />
              <!-- Fallback logo if image doesn't load -->

              <div>
                <h1 class="text-2xl font-bold text-secondary tracking-tight">
                  PAGMS
                </h1>
                <p class="text-xs text-gray-600">MUBAS</p>
              </div>
            </div>
            <h2 class="text-3xl font-bold text-secondary mb-2">
              Welcome back!
            </h2>
            <p class="text-gray-600 text-sm">
              Simplify your workflow and boost your productivity with PAGMS. Get
              started for free.
            </p>
          </div>

          <form on:submit={handleSubmit} class="space-y-5">
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
              <input
                id="password"
                type="password"
                class="w-full px-4 py-3 bg-white/50 backdrop-blur-md border border-gray-300/50 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
                bind:value={password}
                placeholder="Password"
                required
              />
              <div class="text-right mt-2">
                <button
                  type="button"
                  class="text-xs text-gray-600 hover:text-primary transition-colors"
                >
                  Forgot Password?
                </button>
              </div>
            </div>

            {#if error}
              <div
                class="text-red-600 text-sm font-medium p-3 bg-red-50/40 backdrop-blur-md rounded-lg border border-red-200/30"
                role="alert"
                aria-live="polite"
              >
                {error}
              </div>
            {/if}

            <button
              type="submit"
              class="w-full bg-secondary text-white py-3 px-6 rounded-xl font-semibold hover:bg-secondary/90 focus:outline-none focus:ring-2 focus:ring-secondary focus:ring-offset-2 transition-all duration-150 shadow-lg"
              disabled={isLoading}
            >
              {isLoading ? "Signing in..." : "Login"}
            </button>

            <div class="text-center text-sm text-gray-600">
              or continue with
            </div>

            <div class="flex justify-center gap-4">
              <button
                type="button"
                class="w-12 h-12 bg-secondary text-white rounded-full flex items-center justify-center hover:bg-secondary/90 transition-all shadow-md"
              >
                <span class="text-lg font-bold">G</span>
              </button>
              <button
                type="button"
                class="w-12 h-12 bg-secondary text-white rounded-full flex items-center justify-center hover:bg-secondary/90 transition-all shadow-md"
              >
                <span class="text-lg">🍎</span>
              </button>
              <button
                type="button"
                class="w-12 h-12 bg-secondary text-white rounded-full flex items-center justify-center hover:bg-secondary/90 transition-all shadow-md"
              >
                <span class="text-lg font-bold">f</span>
              </button>
            </div>

            <div class="text-center text-sm text-gray-600 mt-6">
              Not a member?
              <button
                type="button"
                on:click={() => router.goToRegister()}
                class="text-primary font-semibold hover:underline focus:outline-none"
              >
                Register now
              </button>
            </div>

            <div
              class="text-center text-xs text-gray-500 mt-4 p-3 bg-gray-50/50 rounded-lg"
            >
              <strong>Demo accounts:</strong> pi@mubas.ac.mw, team@mubas.ac.mw,
              finance@mubas.ac.mw, rsu@mubas.ac.mw<br />
              Password:
              <code class="bg-gray-200/80 px-1.5 py-0.5 rounded">mubas123</code>
            </div>
          </form>
        </div>

        <!-- Right Column - Illustration -->
        <div
          class="bg-gradient-to-br from-primary/5 via-primary/10 to-accent/10 p-8 md:p-12 flex flex-col items-center justify-center relative overflow-hidden"
        >
          <!-- Decorative circles -->
          <div
            class="absolute top-10 right-10 w-20 h-20 bg-primary/10 rounded-full blur-2xl"
          ></div>
          <div
            class="absolute bottom-20 left-10 w-32 h-32 bg-accent/10 rounded-full blur-3xl"
          ></div>

          <!-- Main illustration area -->
          <div class="relative z-10 text-center space-y-8">
            <!-- Central illustration -->
            <div class="relative inline-block">
              <!-- Meditation person -->
              <div class="w-64 h-64 mx-auto mb-6 relative">
                <div class="absolute inset-0 bg-primary/5 rounded-full"></div>
                <!-- Person silhouette -->
                <div
                  class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
                >
                  <div
                    class="w-32 h-32 bg-primary/20 rounded-full flex items-center justify-center border-4 border-primary/30"
                  >
                    <div class="text-5xl">🧘‍♀️</div>
                  </div>
                </div>

                <!-- Floating avatars -->
                <div
                  class="absolute top-8 left-8 w-16 h-16 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center border-2 border-primary/20 shadow-lg"
                >
                  <div class="text-2xl">👨‍💼</div>
                </div>
                <div
                  class="absolute top-8 right-8 w-12 h-12 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center border-2 border-accent/20 shadow-lg"
                >
                  <div class="text-xl">💡</div>
                </div>
                <div
                  class="absolute bottom-12 right-4 w-14 h-14 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center border-2 border-primary/20 shadow-lg"
                >
                  <div class="text-xl">👩‍🔬</div>
                </div>
              </div>

              <!-- Project card -->
              <div
                class="inline-block bg-white/90 backdrop-blur-md rounded-2xl p-4 shadow-glass-lg border border-white/50 mb-4"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center"
                  >
                    <span class="text-xl">📊</span>
                  </div>
                  <div class="text-left">
                    <div class="font-semibold text-secondary text-sm">
                      Grant Project
                    </div>
                    <div class="text-xs text-gray-600">10 Tasks</div>
                  </div>
                  <div class="ml-4 px-3 py-1 bg-primary/10 rounded-full">
                    <span class="text-xs font-semibold text-primary"
                      >Active</span
                    >
                  </div>
                </div>
              </div>
            </div>

            <!-- Bottom text -->
            <div class="space-y-2">
              <h3 class="text-xl font-bold text-secondary">
                Make your work easier and organized
              </h3>
              <p class="text-sm text-gray-600">
                with <span class="font-semibold text-primary">PAGMS</span>
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
  input:focus {
    outline: none;
  }
</style>
