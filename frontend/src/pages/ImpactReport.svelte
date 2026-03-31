<script>
  import { onMount } from 'svelte';
  import Layout from '../components/Layout.svelte';
  import { user } from '../stores/auth.js';
  import axios from 'axios';
  import Icon from '../components/Icon.svelte';

  let stats = null;
  let milestones = [];
  let loading = true;
  let error = null;

  onMount(async () => {
    try {
      const res = await axios.get('/api/me/impact', { withCredentials: true });
      stats = res.data.stats;
      milestones = res.data.contributed_milestones || [];
    } catch (e) {
      error = 'Could not load your impact report.';
    } finally {
      loading = false;
    }
  });

  function pct(val, total) {
    if (!total) return 0;
    return Math.min(100, Math.round((val / total) * 100));
  }

  const milestoneStatusColors = {
    COMPLETED:    'bg-emerald-100 text-emerald-700 border-emerald-200',
    IN_PROGRESS:  'bg-blue-100 text-blue-700 border-blue-200',
    NOT_STARTED:  'bg-slate-100 text-slate-500 border-slate-200',
  };

  function getBadges(s) {
    const badges = [];
    if (!s) return badges;
    if (s.completion_rate >= 90) badges.push({ icon: 'target', label: 'Precision Expert', desc: '90%+ task accuracy', color: 'from-amber-400 to-orange-500' });
    if (s.total_verified_hours >= 40) badges.push({ icon: 'clock', label: 'Field Veteran', desc: `${s.total_verified_hours} hrs certified`, color: 'from-blue-400 to-indigo-500' });
    if (s.milestones_contributed >= 2) badges.push({ icon: 'activity', label: 'Strategic Asset', desc: `${s.milestones_contributed} milestones hit`, color: 'from-emerald-400 to-teal-500' });
    if (s.effort_certifications_signed >= 3) badges.push({ icon: 'check-circle', label: 'Audit Ready', desc: 'Flawless compliance', color: 'from-violet-400 to-purple-500' });
    if (s.approved_deliverables >= 5) badges.push({ icon: 'document', label: 'Knowledge Creator', desc: '5+ approved outputs', color: 'from-rose-400 to-pink-500' });
    if (badges.length === 0) badges.push({ icon: 'rocket', label: 'Rising Star', desc: 'Contributions pending review', color: 'from-slate-400 to-slate-500' });
    return badges;
  }
</script>

<Layout>
  <div class="space-y-8 pt-4 pb-12 px-2">
    <!-- Premium Header -->
    <header class="relative bg-white/40 backdrop-blur-xl border border-white/60 rounded-[2.5rem] p-10 overflow-hidden shadow-2xl">
      <div class="absolute -top-24 -right-24 w-64 h-64 bg-emerald-400/10 rounded-full blur-[80px]"></div>
      <div class="absolute -bottom-24 -left-24 w-64 h-64 bg-blue-400/10 rounded-full blur-[80px]"></div>
      
      <div class="relative z-10 flex flex-col md:flex-row items-center gap-8">
        <div class="h-24 w-24 rounded-[2rem] bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-white shadow-2xl shadow-emerald-200/50 transform -rotate-3 hover:rotate-0 transition-transform duration-500">
          <Icon name="analytics" size={48} />
        </div>
        <div>
          <h1 class="text-5xl font-black text-slate-900 tracking-tight">Impact <span class="text-emerald-500">Analytics</span></h1>
          <p class="text-slate-500 font-medium text-lg mt-2">Quantitative and qualitative evidence of your research contributions.</p>
          <div class="flex gap-4 mt-6">
            <div class="px-4 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold uppercase tracking-widest border border-emerald-100 flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Live Contribution Feed
            </div>
            <div class="px-4 py-1.5 rounded-full bg-slate-50 text-slate-500 text-xs font-bold uppercase tracking-widest border border-slate-100 italic">
              Academic Year 2025/26
            </div>
          </div>
        </div>
      </div>
    </header>

    {#if loading}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each [1,2,3,4,5,6] as _}
          <div class="h-48 bg-white/40 backdrop-blur-md rounded-[2rem] animate-pulse border border-white/60"></div>
        {/each}
      </div>
    {:else if error}
      <div class="bg-rose-50 border-2 border-rose-100 rounded-[2rem] p-10 text-center">
        <div class="text-rose-500 mb-4 flex justify-center">
            <Icon name="alert-triangle" size={48} />
        </div>
        <p class="text-rose-900 font-bold text-xl">{error}</p>
        <button on:click={() => window.location.reload()} class="mt-4 px-6 py-2 bg-rose-500 text-white rounded-xl font-bold hover:bg-rose-600 transition-all">Try Again</button>
      </div>
    {:else}
      <!-- Impact Pulse Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Tasks Card -->
        <div class="group relative bg-white/70 backdrop-blur-xl border border-white/60 rounded-[2rem] p-8 shadow-xl hover:shadow-2xl transition-all hover:-translate-y-1">
          <div class="flex justify-between items-start mb-6">
            <div class="p-4 rounded-2xl bg-blue-50 text-blue-600 group-hover:scale-110 transition-transform">
              <Icon name="tasks" size={24} />
            </div>
            <span class="text-4xl font-black text-slate-900">{stats?.completed_tasks ?? 0}</span>
          </div>
          <p class="text-slate-900 font-bold text-lg leading-none">Operational Efficiency</p>
          <p class="text-slate-500 text-sm mt-1">Total tasks executed against targets</p>
          <div class="mt-6">
            <div class="flex justify-between text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">
              <span>Completion Rate</span>
              <span>{stats?.completion_rate ?? 0}%</span>
            </div>
            <div class="bg-slate-100 rounded-full h-3 overflow-hidden p-0.5">
              <div class="bg-gradient-to-r from-blue-400 to-blue-600 h-full rounded-full transition-all duration-1000" style="width:{stats?.completion_rate ?? 0}%"></div>
            </div>
          </div>
        </div>

        <!-- Deliverables Card -->
        <div class="group relative bg-white/70 backdrop-blur-xl border border-white/60 rounded-[2rem] p-8 shadow-xl hover:shadow-2xl transition-all hover:-translate-y-1">
          <div class="flex justify-between items-start mb-6">
            <div class="p-4 rounded-2xl bg-violet-50 text-violet-600 group-hover:scale-110 transition-transform">
              <Icon name="document" size={24} />
            </div>
            <span class="text-4xl font-black text-slate-900">{stats?.approved_deliverables ?? 0}</span>
          </div>
          <p class="text-slate-900 font-bold text-lg leading-none">Knowledge Outputs</p>
          <p class="text-slate-500 text-sm mt-1">Peer-approved technical deliverables</p>
          <div class="mt-6 flex gap-2">
            <div class="flex-1 bg-violet-50 rounded-xl p-3 text-center">
              <p class="text-xs font-black text-violet-600 uppercase">Submissions</p>
              <p class="text-lg font-black text-slate-900">{stats?.total_deliverables ?? 0}</p>
            </div>
            <div class="flex-1 bg-emerald-50 rounded-xl p-3 text-center">
              <p class="text-xs font-black text-emerald-600 uppercase">Approval</p>
              <p class="text-lg font-black text-slate-900">{pct(stats?.approved_deliverables, stats?.total_deliverables)}%</p>
            </div>
          </div>
        </div>

        <!-- Effort Card -->
        <div class="group relative bg-white/70 backdrop-blur-xl border border-white/60 rounded-[2rem] p-8 shadow-xl hover:shadow-2xl transition-all hover:-translate-y-1 bg-gradient-to-br from-white/70 to-emerald-50/30">
          <div class="flex justify-between items-start mb-6">
            <div class="p-4 rounded-2xl bg-emerald-50 text-emerald-600 group-hover:scale-110 transition-transform">
              <Icon name="clock" size={24} />
            </div>
            <span class="text-4xl font-black text-emerald-600">{stats?.total_verified_hours ?? 0} <span class="text-lg">hrs</span></span>
          </div>
          <p class="text-slate-900 font-bold text-lg leading-none">Certified Academic Effort</p>
          <p class="text-slate-500 text-sm mt-1">Verified research time (Audit Proof)</p>
          <div class="mt-8 flex items-center gap-3">
             <div class="flex -space-x-2">
                {#each [1,2,3] as _}
                    <div class="w-8 h-8 rounded-full border-2 border-white bg-slate-200 flex items-center justify-center">
                        <Icon name="user" size={12} className="text-slate-400" />
                    </div>
                {/each}
             </div>
             <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-tight">Verified by PI &<br/>RSU Compliance</p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Milestone Contributions -->
        <div class="lg:col-span-2 space-y-6">
          <section class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-[2.5rem] p-8 shadow-xl">
            <h2 class="text-2xl font-black text-slate-900 flex items-center gap-3 mb-8">
              <Icon name="target" size={24} className="text-indigo-500" />
              Strategic Impact Map
            </h2>
            
            {#if milestones.length > 0}
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {#each milestones as m}
                  <div class="relative bg-slate-50/50 hover:bg-white transition-all rounded-3xl p-6 border border-slate-100 hover:border-indigo-200 hover:shadow-md group">
                    <div class="flex justify-between items-start mb-4">
                      <div>
                        <h4 class="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">{m.title}</h4>
                        <p class="text-[10px] font-black uppercase text-slate-400 mt-0.5 tracking-widest">{m.grant}</p>
                      </div>
                      <span class="text-[10px] font-black px-3 py-1 rounded-full border shadow-sm {milestoneStatusColors[m.status] || milestoneStatusColors.NOT_STARTED}">
                        {m.status?.replace('_', ' ')}
                      </span>
                    </div>
                    
                    <div class="flex items-center gap-4">
                      <div class="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden">
                        <div class="bg-gradient-to-r from-indigo-500 to-blue-500 h-full rounded-full" style="width:{m.progress ?? 0}%"></div>
                      </div>
                      <span class="text-xs font-black text-slate-600">{m.progress ?? 0}%</span>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="text-center py-16 bg-slate-50/50 rounded-3xl border border-dashed border-slate-200">
                <p class="text-slate-400 font-medium">No milestone contributions recorded yet.</p>
              </div>
            {/if}
          </section>

          <!-- Secondary Quick Stats -->
          <div class="grid grid-cols-3 gap-6">
             <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl p-6 text-center shadow-md">
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Active Projects</p>
                <p class="text-2xl font-black text-slate-900">{stats?.active_grants ?? 0}</p>
             </div>
             <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl p-6 text-center shadow-md">
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Impact Tokens</p>
                <p class="text-2xl font-black text-slate-900">{stats?.milestones_contributed ?? 0}</p>
             </div>
             <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl p-6 text-center shadow-md text-pink-600">
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Certifications</p>
                <p class="text-2xl font-black">{stats?.effort_certifications_signed ?? 1}</p>
             </div>
          </div>
        </div>

        <!-- Excellence Recognition (Badges) -->
        <section class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-[2.5rem] p-8 shadow-xl">
          <h2 class="text-2xl font-black text-slate-900 flex items-center gap-3 mb-8">
            <Icon name="mission" size={24} className="text-amber-500" />
            Hall of Merit
          </h2>
          <div class="space-y-4">
            {#each getBadges(stats) as badge}
              <div class="group flex items-center gap-5 p-5 rounded-[2rem] bg-gradient-to-br from-white to-slate-50 border border-slate-100 transition-all hover:shadow-xl hover:-translate-x-1 hover:border-amber-200">
                <div class="w-16 h-16 shrink-0 rounded-2xl bg-gradient-to-tr {badge.color} flex items-center justify-center text-white shadow-lg group-hover:rotate-6 transition-transform">
                  <Icon name={badge.icon} size={30} />
                </div>
                <div>
                  <h4 class="font-black text-slate-900 leading-tight">{badge.label}</h4>
                  <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">{badge.desc}</p>
                </div>
              </div>
            {/each}
          </div>
          
          <div class="mt-10 p-6 rounded-3xl bg-indigo-600 text-white shadow-xl shadow-indigo-100">
             <h4 class="font-black text-lg">Contribution Export</h4>
             <p class="text-indigo-100 text-xs mt-1">Generate a verified PDF impact report for your academic CV or evaluation.</p>
             <button class="mt-4 w-full py-3 bg-white text-indigo-600 rounded-xl font-bold text-sm shadow-lg active:scale-95 transition-all">Download Portfolio Dossier</button>
          </div>
        </section>
      </div>
    {/if}
  </div>
</Layout>

<style>
  :global(body) { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
</style>
