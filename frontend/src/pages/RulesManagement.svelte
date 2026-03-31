<script>
  import { onMount } from "svelte";
  import { user } from "../stores/auth.js";
  import { prompt } from "../stores/modals.js";
  import Layout from "../components/Layout.svelte";
  import Icon from "../components/Icon.svelte";
  
  let profiles = [];
  let rules = []; 
  let loading = true;
  let error = "";
  let success = "";
  
  // UI State
  let viewMode = 'rules'; // 'rules', 'profiles', 'approvals', 'exemptions'
  let priorApprovals = [];
  let exemptions = [];
  let exemptionForm = { grant_id: "", rule_id: "", justification: "" };
  let selectedProfileId = null;
  let showRuleDrawer = false;
  let showProfileModal = false;
  
  // Forms
  let ruleForm = {
    id: null,
    name: "",
    rule_type: "THRESHOLD",
    logic_config: { condition: "amount_greater_than", value: 5000, category: "equipment", module: "finance" },
    outcome: "BLOCK",
    priority_level: 3,
    guidance_text: "",
    is_active: true
  };
  
  let profileForm = {
    name: "",
    funder_id: "",
    rule_ids: []
  };

  $: selectedProfile = profiles.find(p => p.id === selectedProfileId);
  $: profileRules = selectedProfile ? selectedProfile.rules : [];

  onMount(async () => {
    await loadData();
  });

  async function loadData() {
    try {
      loading = true;
      const [profRes, ruleRes] = await Promise.all([
        fetch("/api/profiles", { credentials: "include" }),
        fetch("/api/rules", { credentials: "include" })
      ]);
      
      if (profRes.ok) profiles = await profRes.json();
      if (ruleRes.ok) rules = await ruleRes.json();
      
      if (profiles.length > 0 && !selectedProfileId) {
        selectedProfileId = profiles[0].id;
      }
    } catch (err) {
      error = "Failed to load data";
    } finally {
      loading = false;
    }
  }

  async function loadApprovals() {
    try {
      const res = await fetch("/api/prior-approvals", { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        priorApprovals = data.requests;
      }
    } catch (err) { console.error(err); }
  }

  async function loadExemptions() {
    try {
      const res = await fetch("/api/rule-exemptions", { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        exemptions = data.exemptions || [];
      }
    } catch (err) { console.error(err); }
  }

  $: if (viewMode === 'approvals') loadApprovals();
  $: if (viewMode === 'exemptions') loadExemptions();

  async function resolvePA(id, decision) {
    const justification = await prompt(`Enter justification for ${decision}:`);
    if (!justification) return;
    try {
      const res = await fetch(`/api/prior-approvals/${id}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ decision, justification })
      });
      if (res.ok) {
        success = "Resolution saved";
        loadApprovals();
      }
    } catch (err) { error = "Failed to resolve"; }
  }

  async function saveExemption() {
    try {
      const res = await fetch("/api/rule-exemptions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(exemptionForm)
      });
      if (res.ok) {
        success = "Exemption created";
        exemptionForm = { grant_id: "", rule_id: "", justification: "" };
        loadExemptions();
      }
    } catch (err) { error = "Failed to save exemption"; }
  }

  function openRuleDrawer(rule = null) {
    if (rule) {
      ruleForm = { 
        ...rule, 
        logic_config: typeof rule.logic_config === 'string' ? JSON.parse(rule.logic_config) : rule.logic_config 
      };
    } else {
      ruleForm = {
        id: null,
        name: "",
        rule_type: "THRESHOLD",
        logic_config: { condition: "amount_greater_than", value: 5000, category: "equipment" },
        outcome: "BLOCK",
        priority_level: 2,
        guidance_text: "",
        is_active: true
      };
    }
    showRuleDrawer = true;
  }

  function closeDrawer() {
    showRuleDrawer = false;
  }

  async function saveRule() {
    error = ""; success = "";
    try {
      const isNew = !ruleForm.id;
      const url = isNew ? "/api/rules" : `/api/rules/${ruleForm.id}`;
      const method = isNew ? "POST" : "PATCH";
      
      const payload = { 
        ...ruleForm,
        rule_type: ruleForm.logic_config.module?.toUpperCase() || 'FINANCE'
      };
      
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        success = `Rule ${isNew ? 'created' : 'updated'} successfully`;
        showRuleDrawer = false;
        await loadData();
      } else {
        const data = await res.json();
        error = data.error || "Failed to save rule";
      }
    } catch (err) {
      error = "Network error";
    }
  }

  async function saveProfile() {
    error = ""; success = "";
    try {
      const res = await fetch("/api/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(profileForm)
      });
      
      if (res.ok) {
        success = "Profile created successfully";
        showProfileModal = false;
        await loadData();
        const created = await res.json();
        selectedProfileId = created.id;
      } else {
        const data = await res.json();
        error = data.details || data.error || "Failed to create profile";
      }
    } catch (err) {
      error = "Network error";
    }
  }

  function toggleProfileRule(ruleId) {
    const idx = profileForm.rule_ids.indexOf(ruleId);
    if (idx > -1) profileForm.rule_ids.splice(idx, 1);
    else profileForm.rule_ids.push(ruleId);
    profileForm = { ...profileForm };
  }

</script>

<Layout>
  <div class="max-w-7xl mx-auto pb-12">
    <!-- Header -->
    <div class="bg-gradient-to-br from-indigo-600 to-blue-700 text-white rounded-3xl shadow-lg p-8 mb-8 relative overflow-hidden flex justify-between items-center flex-wrap gap-4">
      <div class="relative z-10">
        <h1 class="text-3xl font-bold mb-2">Compliance Rules Engine</h1>
        <p class="text-indigo-100 max-w-2xl">Configure automated compliance rules and assign them to funder profiles.</p>
      </div>
      
      <button 
        on:click={() => openRuleDrawer()}
        class="relative z-10 px-6 py-3 bg-white text-indigo-700 hover:bg-indigo-50 font-bold rounded-xl shadow-xl shadow-indigo-900/20 hover:-translate-y-0.5 transition-all outline-none border-2 border-transparent focus:border-indigo-300"
      >
        + Global Rule Builder
      </button>

      <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
    </div>

    <!-- Error/Success -->
    {#if error}
      <div class="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-center gap-3">
        <Icon name="warning" size={20} />
        <p>{error}</p>
      </div>
    {/if}
    {#if success}
      <div class="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl flex items-center gap-3">
        <div class="text-emerald-500">✓</div>
        <p>{success}</p>
      </div>
    {/if}

    <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
      
      <!-- Left Panel: Navigation -->
      <div class="md:col-span-1 space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-bold text-gray-900">Explorer</h2>
        </div>
        
        {#if loading}
          <div class="animate-pulse space-y-3">
            <div class="h-12 bg-gray-200 rounded-xl"></div>
            <div class="h-12 bg-gray-200 rounded-xl"></div>
          </div>
        {:else}
          <div class="space-y-3">
            <!-- Global Rules Tab -->
            <button 
              on:click={() => { viewMode = 'rules'; selectedProfileId = null; }}
              class="w-full text-left p-4 rounded-xl border transition-all duration-200 {viewMode === 'rules' ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-200' : 'bg-white text-gray-700 border-gray-200 hover:border-indigo-300'}"
            >
              <div class="font-semibold flex items-center gap-2">
                <Icon name="setting" size={18} /> Global Rules Library
              </div>
              <div class="text-xs mt-1 {viewMode === 'rules' ? 'text-indigo-100' : 'text-gray-500'}">{rules.length} total rules configured</div>
            </button>

            <div class="pt-4 pb-1">
              <h3 class="text-xs font-bold text-gray-400 uppercase tracking-wider">Funder Profiles</h3>
              <button 
                on:click={() => { profileForm = { name: '', funder_id: '', rule_ids: [] }; showProfileModal = true; }}
                class="text-[10px] text-blue-600 font-bold hover:underline"
              >
                + NEW PROFILE
              </button>
            </div>

            {#each profiles as profile}
              <button 
                on:click={() => { viewMode = 'profiles'; selectedProfileId = profile.id; }}
                class="w-full text-left p-4 rounded-xl border transition-all duration-200 {viewMode === 'profiles' && selectedProfileId === profile.id ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-200' : 'bg-white text-gray-700 border-gray-200 hover:border-blue-300'}"
              >
                <div class="font-semibold truncate">{profile.name}</div>
                <div class="text-xs mt-1 {viewMode === 'profiles' && selectedProfileId === profile.id ? 'text-blue-100' : 'text-gray-500'}">Funder: {profile.funder_id || 'Global'}</div>
                <div class="text-xs font-medium mt-2 {viewMode === 'profiles' && selectedProfileId === profile.id ? 'text-white' : 'text-gray-400'}">{profile.rules?.length || 0} Rules Active</div>
              </button>
            {/each}

            <div class="pt-4 pb-1">
              <h3 class="text-xs font-bold text-gray-400 uppercase tracking-wider">Compliance Ops</h3>
            </div>

            <button 
              on:click={() => { viewMode = 'approvals'; selectedProfileId = null; }}
              class="w-full text-left p-4 rounded-xl border transition-all duration-200 {viewMode === 'approvals' ? 'bg-purple-600 text-white border-purple-600 shadow-md' : 'bg-white text-gray-700 border-gray-200 hover:border-purple-300'}"
            >
              <div class="font-semibold flex items-center gap-2">
                <Icon name="statusWarn" size={18} /> Prior Approvals
              </div>
              <div class="text-xs mt-1 {viewMode === 'approvals' ? 'text-purple-100' : 'text-gray-500'}">Review & resolve requests</div>
            </button>

            <button 
              on:click={() => { viewMode = 'exemptions'; selectedProfileId = null; }}
              class="w-full text-left p-4 rounded-xl border transition-all duration-200 {viewMode === 'exemptions' ? 'bg-slate-700 text-white border-slate-700 shadow-md' : 'bg-white text-gray-700 border-gray-200 hover:border-slate-300'}"
            >
              <div class="font-semibold flex items-center gap-2">
                <Icon name="shield" size={18} /> Rule Exemptions
              </div>
              <div class="text-xs mt-1 {viewMode === 'exemptions' ? 'text-slate-200' : 'text-gray-500'}">Whitelist specific grants</div>
            </button>
          </div>
        {/if}
      </div>

      <!-- Center Panel -->
      <div class="md:col-span-3">
        {#if loading}
          <div class="h-full flex items-center justify-center p-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        {:else if viewMode === 'rules'}
          <!-- View All Rules -->
          <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-sm p-6 space-y-6 min-h-[500px]">
            <div class="flex items-center justify-between border-b border-gray-100 pb-4">
              <div>
                <h2 class="text-2xl font-bold text-gray-900 flex items-center gap-3">
                  Global Rules Library
                </h2>
                <p class="text-sm text-gray-500 mt-1">All compliance rules available in the system.</p>
              </div>
            </div>

            <div class="space-y-4">
              {#if rules.length === 0}
                <div class="text-center py-12 text-gray-500 bg-gray-50/50 rounded-2xl border border-dashed border-gray-200">
                  <p>No rules configured in the system yet.</p>
                  <button on:click={() => openRuleDrawer()} class="mt-4 px-4 py-2 bg-indigo-50 text-indigo-700 font-medium rounded-lg">Create First Rule</button>
                </div>
              {:else}
                {#each rules as rule}
                  <div class="group bg-white border border-gray-200 rounded-2xl p-5 hover:shadow-md hover:border-indigo-300 transition-all flex flex-col md:flex-row gap-4 items-start md:items-center justify-between shadow-sm">
                    <div class="flex-1">
                      <div class="flex items-center gap-3 mb-1">
                        <span class="w-10 h-10 rounded-full flex items-center justify-center
                          {rule.outcome === 'BLOCK' ? 'bg-red-100' : 
                           rule.outcome === 'PRIOR_APPROVAL' ? 'bg-amber-100' : 'bg-blue-100'}">
                          <Icon 
                            name={rule.outcome === 'BLOCK' ? 'statusCritical' : rule.outcome === 'PRIOR_APPROVAL' ? 'statusWarn' : 'info'} 
                            size={20} 
                            className={rule.outcome === 'BLOCK' ? 'text-red-600' : rule.outcome === 'PRIOR_APPROVAL' ? 'text-amber-600' : 'text-blue-600'}
                          />
                        </span>
                        <div>
                          <h3 class="font-bold text-gray-900">{rule.name}</h3>
                          <div class="flex items-center gap-2 text-xs font-medium mt-1">
                            <span class="text-gray-500 bg-gray-100 px-2 py-0.5 rounded-md">{rule.rule_type}</span>
                            <span class="text-gray-400">Prio: {rule.priority_level}</span>
                            <span class={rule.is_active ? "text-emerald-500" : "text-gray-400"}>
                              {rule.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                      </div>
                      <p class="text-sm text-gray-600 mt-3 ml-13">
                        {rule.guidance_text || "No guidance text provided."}
                      </p>
                    </div>

                    <div class="flex flex-col items-end gap-2 shrink-0">
                      <div class="font-mono text-xs text-gray-500 bg-gray-50 p-2 rounded-lg border border-gray-100 min-w-[200px] text-right">
                        {@html formatLogic(rule.logic_config)}
                      </div>
                      <button 
                        on:click={() => openRuleDrawer(rule)}
                        class="text-sm font-medium text-indigo-600 hover:text-indigo-800 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        Edit Rule →
                      </button>
                    </div>
                  </div>
                {/each}
              {/if}
            </div>
          </div>
        {:else if viewMode === 'profiles' && selectedProfile}
          <!-- View Profile Rules -->
          <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-sm p-6 space-y-6 min-h-[500px]">
            <div class="flex items-center justify-between border-b border-gray-100 pb-4">
              <div>
                <h2 class="text-2xl font-bold text-gray-900 flex items-center gap-3">
                  {selectedProfile.name} 
                  <span class="px-3 py-1 bg-gray-100 text-gray-600 text-xs rounded-full font-medium tracking-wider uppercase">
                    {selectedProfile.funder_id}
                  </span>
                </h2>
                <p class="text-sm text-gray-500 mt-1">Rules applied to grants initialized under this funder.</p>
              </div>
              <button 
                on:click={() => { profileForm = { ...selectedProfile, rule_ids: selectedProfile.rules.map(r => r.id) }; showProfileModal = true; }}
                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
              >
                Edit Profile
              </button>
            </div>

            <div class="space-y-4">
              {#if profileRules.length === 0}
                <div class="text-center py-12 text-gray-500 bg-gray-50/50 rounded-2xl border border-dashed border-gray-200">
                  <p>No rules assigned to this profile.</p>
                  <p class="text-sm mt-1">Create a new rule or edit the profile to add existing ones.</p>
                </div>
              {:else}
                {#each profileRules as rule}
                  <div class="group bg-white border border-gray-200 rounded-2xl p-5 hover:shadow-md hover:border-blue-200 transition-all flex flex-col md:flex-row gap-4 items-start md:items-center justify-between shadow-sm">
                    
                    <div class="flex-1">
                      <div class="flex items-center gap-3 mb-1">
                        <span class="w-10 h-10 rounded-full flex items-center justify-center
                          {rule.outcome === 'BLOCK' ? 'bg-red-100' : 
                           rule.outcome === 'PRIOR_APPROVAL' ? 'bg-amber-100' : 'bg-blue-100'}">
                          <Icon 
                            name={rule.outcome === 'BLOCK' ? 'statusCritical' : rule.outcome === 'PRIOR_APPROVAL' ? 'statusWarn' : 'info'} 
                            size={20} 
                            className={rule.outcome === 'BLOCK' ? 'text-red-600' : rule.outcome === 'PRIOR_APPROVAL' ? 'text-amber-600' : 'text-blue-600'}
                          />
                        </span>
                        <div>
                          <h3 class="font-bold text-gray-900">{rule.name}</h3>
                          <div class="flex items-center gap-2 text-xs font-medium mt-1">
                            <span class="text-gray-500 bg-gray-100 px-2 py-0.5 rounded-md">{rule.rule_type}</span>
                            <span class="text-gray-400">Prio: {rule.priority_level}</span>
                            <span class={rule.is_active ? "text-emerald-500" : "text-gray-400"}>
                              {rule.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                      </div>
                      <p class="text-sm text-gray-600 mt-3 ml-13">
                        {rule.guidance_text || "No guidance text provided."}
                      </p>
                    </div>

                    <div class="flex flex-col items-end gap-2 shrink-0">
                      <div class="font-mono text-xs text-gray-500 bg-gray-50 p-2 rounded-lg border border-gray-100 min-w-[200px]">
                        {@html formatLogic(rule.logic_config)}
                      </div>
                      <button 
                        on:click={() => openRuleDrawer(rule)}
                        class="text-sm font-medium text-blue-600 hover:text-blue-800 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        Edit Rule →
                      </button>
                    </div>

                  </div>
                {/each}
              {/if}
            </div>
          </div>
        {:else if viewMode === 'approvals'}
          <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-sm p-6 space-y-6 min-h-[500px]">
            <div>
              <h2 class="text-2xl font-bold text-gray-900">Prior Approval Queue</h2>
              <p class="text-sm text-gray-500">Manual review required for rule exceptions.</p>
            </div>
            
            <div class="space-y-4">
              {#each priorApprovals as req}
                <div class="p-6 bg-white border border-purple-100 rounded-2xl flex justify-between items-center shadow-sm">
                  <div>
                    <span class="px-2 py-0.5 bg-purple-100 text-purple-700 text-[10px] font-bold rounded uppercase">{req.request_type}</span>
                    <h3 class="font-bold text-lg text-gray-900 mt-1">{req.grant_title}</h3>
                    <p class="text-sm text-gray-600 mt-1">{req.justification}</p>
                    <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
                      <span>Requester: {req.requester_name}</span>
                      <span>Requested: {new Date(req.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div class="flex gap-2">
                    <button on:click={() => resolvePA(req.id, 'APPROVED')} class="px-4 py-2 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 transition-colors">Approve</button>
                    <button on:click={() => resolvePA(req.id, 'REJECTED')} class="px-4 py-2 bg-rose-600 text-white font-bold rounded-xl hover:bg-rose-700 transition-colors">Reject</button>
                  </div>
                </div>
              {:else}
                <div class="text-center py-20 text-gray-500 bg-gray-50 rounded-2xl border border-dashed">
                   No pending requests in the queue.
                </div>
              {/each}
            </div>
          </div>
        {:else if viewMode === 'exemptions'}
           <div class="bg-white/70 backdrop-blur-xl border border-white/60 rounded-3xl shadow-sm p-6 space-y-6 min-h-[500px]">
            <div class="flex justify-between items-center">
              <div>
                <h2 class="text-2xl font-bold text-gray-900">Rule Exemptions</h2>
                <p class="text-sm text-gray-500">Whitelist specific grants from global compliance rules.</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-50 p-6 rounded-2xl border border-slate-100">
               <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Grant ID</label>
                  <input type="number" bind:value={exemptionForm.grant_id} class="w-full px-4 py-2 border rounded-xl" placeholder="123">
               </div>
               <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Rule ID</label>
                  <input type="number" bind:value={exemptionForm.rule_id} class="w-full px-4 py-2 border rounded-xl" placeholder="45">
               </div>
               <div class="md:col-span-2 flex gap-3 items-end">
                  <div class="flex-1">
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Justification</label>
                    <input type="text" bind:value={exemptionForm.justification} class="w-full px-4 py-2 border rounded-xl" placeholder="Why is this exempt?">
                  </div>
                  <button on:click={saveExemption} class="px-6 py-2 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-900 h-[42px]">Add</button>
               </div>
            </div>

            <div class="space-y-3">
               <h3 class="text-sm font-bold text-gray-400 uppercase tracking-widest mt-6 mb-2">Active Whitelists</h3>
               {#each exemptions as ex}
                 <div class="p-4 bg-white border border-gray-200 rounded-2xl flex justify-between items-center shadow-sm">
                    <div>
                      <div class="flex items-center gap-2">
                         <span class="font-bold text-gray-900">Grant #{ex.grant_id}</span>
                         <span class="text-gray-400">→</span>
                         <span class="font-medium text-blue-600">Rule #{ex.rule_id}</span>
                      </div>
                      <p class="text-xs text-gray-500 mt-1 italic">"{ex.justification}"</p>
                    </div>
                    <div class="text-xs text-gray-400">
                       Created: {new Date(ex.created_at).toLocaleDateString()}
                    </div>
                 </div>
               {:else}
                 <div class="text-center py-10 text-gray-400">No active exemptions found.</div>
               {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Rule Drawer -->
  {#if showRuleDrawer}
    <div class="fixed inset-0 z-50 flex justify-end">
      <!-- Backdrop -->
      <div 
        class="absolute inset-0 bg-gray-900/20 backdrop-blur-sm transition-opacity"
        on:click={closeDrawer}
      ></div>
      
      <!-- Drawer Panel -->
      <div class="relative w-full max-w-md bg-white h-full shadow-2xl flex flex-col transform transition-transform border-l border-gray-200">
        <div class="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50">
          <h2 class="text-xl font-bold text-gray-900">{ruleForm.id ? 'Edit Rule' : 'New Rule Builder'}</h2>
          <button on:click={closeDrawer} class="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Rule Name</label>
            <input type="text" bind:value={ruleForm.name} class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500" placeholder="e.g. Equipment > $5k Block">
          </div>

          <!-- Outcome Selector -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Outcome</label>
            <div class="grid grid-cols-3 gap-2">
              <button 
                type="button"
                on:click={() => ruleForm.outcome = 'BLOCK'}
                class="p-3 border rounded-xl flex flex-col items-center justify-center gap-1 transition-all
                {ruleForm.outcome === 'BLOCK' ? 'border-red-500 bg-red-50 text-red-700 ring-1 ring-red-500' : 'border-gray-200 hover:bg-gray-50'}"
              >
                <span class="text-xl">⛔</span>
                <span class="text-xs font-bold">BLOCK</span>
              </button>
              <button 
                type="button"
                on:click={() => ruleForm.outcome = 'PRIOR_APPROVAL'}
                class="p-3 border rounded-xl flex flex-col items-center justify-center gap-1 transition-all text-center
                {ruleForm.outcome === 'PRIOR_APPROVAL' ? 'border-amber-500 bg-amber-50 text-amber-700 ring-1 ring-amber-500' : 'border-gray-200 hover:bg-gray-50'}"
              >
                <span class="text-xl">✋</span>
                <span class="text-[10px] sm:text-xs font-bold leading-tight">APPROVAL</span>
              </button>
              <button 
                type="button"
                on:click={() => ruleForm.outcome = 'WARN'}
                class="p-3 border rounded-xl flex flex-col items-center justify-center gap-1 transition-all
                {ruleForm.outcome === 'WARN' ? 'border-blue-500 bg-blue-50 text-blue-700 ring-1 ring-blue-500' : 'border-gray-200 hover:bg-gray-50'}"
              >
                <span class="text-xl">ℹ️</span>
                <span class="text-xs font-bold">WARN</span>
              </button>
            </div>
          </div>

          <!-- Logic Builder -->
          <div class="p-4 bg-gray-50 rounded-2xl border border-gray-200 space-y-4">
            <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
              <Icon name="setting" size={16} /> Logic Condition
            </h3>
            
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Module (Enforcement Area)</label>
                <select bind:value={ruleForm.logic_config.module} class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm">
                  <option value="finance">Finance / Expenses</option>
                  <option value="personnel">Personnel & Effort</option>
                  <option value="scope">Project Scope & KPIs</option>
                  <option value="reporting">Reporting & Deadlines</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Category</label>
                <select bind:value={ruleForm.logic_config.category} class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm">
                  {#if ruleForm.logic_config.module === 'finance'}
                    <option value="any">Any Category</option>
                    <option value="equipment">Equipment & Materials</option>
                    <option value="travel">Travel & Subsistence</option>
                    <option value="consultancy">Consultancy Fees</option>
                  {:else}
                    <option value="none">N/A (Module-Wide)</option>
                    <option value="critical">Critical Path</option>
                    <option value="ancillary">Ancillary</option>
                  {/if}
                </select>
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Operator</label>
                <select bind:value={ruleForm.logic_config.condition} class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm">
                  <optgroup label="Numerical (Finance/Scope)">
                    <option value="amount_greater_than">&gt; Greater Than</option>
                    <option value="amount_less_than">&lt; Less Than</option>
                    <option value="equals">== Equals</option>
                  </optgroup>
                  <optgroup label="Status/Text (Personnel/Reporting)">
                    <option value="is_missing">Is Missing/Incomplete</option>
                    <option value="contains">Contains String</option>
                    <option value="matches_role">Matches Role (Personnel)</option>
                    <option value="at_risk">At Risk (Deadline)</option>
                  </optgroup>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Value / Target</label>
                <input type="text" bind:value={ruleForm.logic_config.value} class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm" placeholder="5000 or 'manager'">
              </div>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Guidance Text (shown to PI)</label>
            <textarea bind:value={ruleForm.guidance_text} rows="3" class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 text-sm" placeholder="e.g. Equipment purchases over $5,000 require prior approval from the funder."></textarea>
          </div>

          <div class="flex items-center gap-6">
            <div class="flex-1">
              <label class="block text-sm font-medium text-gray-700 mb-1">Priority (1 = High)</label>
              <input type="number" min="1" max="5" bind:value={ruleForm.priority_level} class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white">
            </div>
            <div class="flex items-center gap-2 mt-6">
              <input type="checkbox" id="isActive" bind:checked={ruleForm.is_active} class="w-5 h-5 text-blue-600 rounded">
              <label for="isActive" class="text-sm font-medium text-gray-700">Active</label>
            </div>
          </div>

        </div>

        <div class="p-4 border-t border-gray-100 bg-gray-50 flex gap-3">
          <button on:click={closeDrawer} class="flex-1 px-4 py-2.5 bg-white border border-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-50">Cancel</button>
          <button on:click={saveRule} class="flex-1 px-4 py-2.5 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 shadow-sm shadow-blue-200">Save Rule</button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Profile Modal -->
  {#if showProfileModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" on:click={() => showProfileModal = false}></div>
      <div class="relative bg-white rounded-3xl shadow-2xl w-full max-w-lg p-8 transform transition-all">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Create Funder Profile</h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Profile Name</label>
            <input type="text" bind:value={profileForm.name} class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500" placeholder="e.g. USAID 2026 Standards">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Funder Code (matches grant config)</label>
            <input type="text" bind:value={profileForm.funder_id} class="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500" placeholder="e.g. usaid">
          </div>
          
          <div class="mt-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">Select Rules for Profile</label>
            <div class="max-h-60 overflow-y-auto space-y-2 border border-gray-100 rounded-xl p-2 bg-gray-50">
              {#each rules as rule}
                <label class="flex items-center gap-3 p-3 bg-white border border-gray-100 rounded-lg cursor-pointer hover:border-blue-300 transition-colors">
                  <input type="checkbox" checked={profileForm.rule_ids.includes(rule.id)} on:change={() => toggleProfileRule(rule.id)} class="w-5 h-5 text-blue-600 rounded border-gray-300">
                  <div>
                    <div class="font-semibold text-sm text-gray-900">{rule.name}</div>
                    <div class="text-xs text-gray-500">{rule.outcome} | Priority: {rule.priority_level}</div>
                  </div>
                </label>
              {/each}
            </div>
          </div>
        </div>

        <div class="mt-8 flex gap-3">
          <button on:click={() => showProfileModal = false} class="flex-1 px-4 py-2.5 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200">Cancel</button>
          <button on:click={saveProfile} class="flex-1 px-4 py-2.5 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800">Create Profile</button>
        </div>
      </div>
    </div>
  {/if}

</Layout>

<script context="module">
  export function formatLogic(logicStr) {
    if (!logicStr) return '';
    try {
      const parsed = typeof logicStr === 'string' ? JSON.parse(logicStr) : logicStr;
      let html = '';
      if (parsed.module) html += `<span class="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded mr-2 uppercase">${parsed.module}</span> `;
      if (parsed.category) html += `<span class="text-indigo-600 font-semibold">[${parsed.category}]</span> `;
      if (parsed.condition) html += `<span class="text-gray-600">${parsed.condition.replace(/_/g, ' ')}</span> `;
      if (parsed.value) html += `<span class="text-green-600 font-bold">${parsed.value}</span>`;
      return html;
    } catch {
      return String(logicStr);
    }
  }
</script>
