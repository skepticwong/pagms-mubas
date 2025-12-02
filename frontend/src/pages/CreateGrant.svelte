<!-- frontend/src/pages/CreateGrant.svelte -->
<script>
    import axios from 'axios';
    import { tweened } from 'svelte/motion';
    import { cubicOut } from 'svelte/easing';
    import Layout from '../components/Layout.svelte';
    import { router } from '../stores/router.js';
    import { user } from '../stores/auth.js';

    const DEFAULT_CATEGORIES = [
      { name: 'Personnel / Salaries', allocated: '' },
      { name: 'Travel & Fieldwork', allocated: '' },
      { name: 'Equipment & Materials', allocated: '' },
      { name: 'Data Collection', allocated: '' },
      { name: 'Workshops & Training', allocated: '' },
      { name: 'Publications & Dissemination', allocated: '' },
      { name: 'Indirect Costs / Overheads', allocated: '' },
      { name: 'Contingency', allocated: '' }
    ];

    const FUNDERS = [
      { value: 'wb', label: 'World Bank' },
      { value: 'nrf', label: 'National Research Fund' },
      { value: 'usaid', label: 'USAID' },
      { value: 'dfid', label: 'DFID' },
      { value: 'gates', label: 'Gates Foundation' },
      { value: 'other', label: 'Other (specify below)' }
    ];

    const REPORT_FREQUENCIES = [
      { value: 'monthly', label: 'Monthly' },
      { value: 'quarterly', label: 'Quarterly' },
      { value: 'biannual', label: 'Bi-Annual' },
      { value: 'annual', label: 'Annual' }
    ];

    const TEAM_ROLES = [
      { value: 'researcher', label: 'Researcher' },
      { value: 'assistant', label: 'Field Assistant' },
      { value: 'analyst', label: 'Data Analyst' },
      { value: 'admin', label: 'Admin Support' }
    ];

    // Step 1: Basic Info
    let title = '';
    let funder = '';
    let funderOther = '';
    let grant_code = '';
    let funderReferenceNumber = '';
    let principalInvestigator = '';
    let start_date = '';
    let end_date = '';

    // Step 2: Financial Details
    let currency = 'usd';
    let total_budget = '';
    let usdToMwkRate = 1700;
    const mwkValue = tweened(0, { duration: 250, easing: cubicOut });

    // Step 3: Budget Categories
    let budgetCategories = [...DEFAULT_CATEGORIES];

    // Step 4: Compliance
    let financialReportingFrequency = 'quarterly';
    let progressReportingFrequency = 'biannual';
    let milestones = [];
    let specialRequirements = '';

    // Step 5: Documents
    let agreement_file = null;
    let budgetBreakdownFile = null;
    let awardLetterFile = null;
    let ethicalApprovalFile = null;

    // Step 6: Team Members
    let teamMembers = [];

    // Step 7: Review & Submit
    let currentStep = 1;
    let error = '';
    let success = '';
    let isLoading = false;
    let validationErrors = {};
    let showPage = false;
    let hasInteracted = false;

    $: totalBudgetNumber = parseFloat(total_budget) || 0;
    $: mwkValue.set(totalBudgetNumber * usdToMwkRate);
    $: projectDuration = calculateDuration(start_date, end_date);
    $: totalAllocated = budgetCategories.reduce((sum, cat) => sum + (parseFloat(cat.allocated) || 0), 0);
    $: budgetBalance = totalBudgetNumber - totalAllocated;
    $: isBudgetBalanced = Math.abs(budgetBalance) < 0.01;
    
    $: isFormValid = Object.keys(validationErrors).length === 0 &&
      title && funder && grant_code && start_date && end_date && total_budget && agreement_file;

    $: showPage = $user?.role === 'PI';

    // Auto-fill PI name from user
    $: if ($user) {
      principalInvestigator = $user.name || '';
    }

    function calculateDuration(start, end) {
      if (!start || !end) return '';
      const startDate = new Date(start);
      const endDate = new Date(end);
      const months = Math.round((endDate - startDate) / (1000 * 60 * 60 * 24 * 30));
      return `${months} months`;
    }

    function getReportingPeriods(start, end) {
      if (!start || !end) return [];
      
      const startDate = new Date(start);
      const endDate = new Date(end);
      const months = Math.round((endDate - startDate) / (1000 * 60 * 60 * 24 * 30));
      
      const periods = [];
      
      // Always include Final Report
      periods.push({ 
        value: 'final', 
        label: 'Final Report',
        dueDate: end
      });
      
      // For grants 3 months or less, only Final Report
      if (months <= 3) {
        return periods;
      }
      
      // For grants 4-11 months, add Interim and Final
      if (months >= 4 && months <= 11) {
        const midDate = new Date(startDate.getTime() + (endDate.getTime() - startDate.getTime()) / 2);
        periods.unshift({ 
          value: 'interim', 
          label: 'Interim Report',
          dueDate: midDate.toISOString().split('T')[0]
        });
        return periods;
      }
      
      // For grants 12-23 months, add Annual and Final
      if (months >= 12 && months <= 23) {
        const annualDate = new Date(startDate);
        annualDate.setFullYear(annualDate.getFullYear() + 1);
        periods.unshift({ 
          value: 'annual_1', 
          label: 'Annual Report Year 1',
          dueDate: annualDate.toISOString().split('T')[0]
        });
        return periods;
      }
      
      // For grants 24+ months, add multiple annual reports and quarterly options
      if (months >= 24) {
        const years = Math.floor(months / 12);
        
        // Add annual reports
        for (let i = 1; i <= years; i++) {
          const annualDate = new Date(startDate);
          annualDate.setFullYear(annualDate.getFullYear() + i);
          if (annualDate < endDate) {
            periods.unshift({ 
              value: `annual_${i}`, 
              label: `Annual Report Year ${i}`,
              dueDate: annualDate.toISOString().split('T')[0]
            });
          }
        }
        
        // Add quarterly options for the first year
        for (let q = 1; q <= 4; q++) {
          const quarterDate = new Date(startDate);
          quarterDate.setMonth(quarterDate.getMonth() + (q * 3));
          if (quarterDate < endDate) {
            periods.push({ 
              value: `q${q}_year1`, 
              label: `Q${q} Year 1`,
              dueDate: quarterDate.toISOString().split('T')[0]
            });
          }
        }
        
        return periods;
      }
      
      return periods;
    }

    $: reportingPeriods = getReportingPeriods(start_date, end_date);

    function getCategoryPercentage(allocated) {
      if (!totalBudgetNumber || !allocated) return 0;
      return ((parseFloat(allocated) / totalBudgetNumber) * 100).toFixed(1);
    }

    function addCategory() {
      budgetCategories = [...budgetCategories, { name: '', allocated: '' }];
      markInteracted();
    }

    function removeCategory(index) {
      if (budgetCategories.length === 1) return;
      budgetCategories = budgetCategories.filter((_, i) => i !== index);
      markInteracted();
    }

    function updateCategory(index, key, value) {
      budgetCategories = budgetCategories.map((cat, i) =>
        i === index ? { ...cat, [key]: value } : cat
      );
      markInteracted();
    }

    function addTeamMember() {
      teamMembers = [...teamMembers, {
        name: '',
        email: '',
        role: 'researcher',
        dailyRate: ''
      }];
      markInteracted();
    }

    function removeTeamMember(index) {
      teamMembers = teamMembers.filter((_, i) => i !== index);
      markInteracted();
    }

    function updateTeamMember(index, key, value) {
      teamMembers = teamMembers.map((member, i) =>
        i === index ? { ...member, [key]: value } : member
      );
      markInteracted();
    }

    function addMilestone() {
      milestones = [...milestones, {
        title: '',
        description: '',
        dueDate: '',
        reportingPeriod: '',
        status: 'not_started',
        completionDate: '',
        completedBy: '',
        evidenceFile: null
      }];
      markInteracted();
    }

    function removeMilestone(index) {
      milestones = milestones.filter((_, i) => i !== index);
      markInteracted();
    }

    function updateMilestone(index, key, value) {
      milestones = milestones.map((milestone, i) =>
        i === index ? { ...milestone, [key]: value } : milestone
      );
      markInteracted();
    }

    function handleMilestoneFileChange(index, e) {
      const file = e.target.files[0];
      if (file) {
        updateMilestone(index, 'evidenceFile', file);
      }
    }

    function removeMilestoneFile(index) {
      updateMilestone(index, 'evidenceFile', null);
    }

    function markInteracted() {
      if (!hasInteracted) hasInteracted = true;
      validateForm();
    }

    function nextStep() {
      if (validateCurrentStep()) {
        currentStep = Math.min(currentStep + 1, 7);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }

    function prevStep() {
      currentStep = Math.max(currentStep - 1, 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function goToStep(step) {
      if (step <= currentStep || validateStepsUpTo(step - 1)) {
        currentStep = step;
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }

    function validateStepsUpTo(step) {
      // Simplified validation - you can make this more granular
      return true;
    }

    function validateCurrentStep() {
      validationErrors = {};
      
      switch(currentStep) {
        case 1: // Basic Info
          if (!title.trim()) validationErrors.title = 'Grant Title is required';
          if (!funder) validationErrors.funder = 'Funder is required';
          if (funder === 'other' && !funderOther.trim()) {
            validationErrors.funderOther = 'Please specify the funder';
          }
          if (!grant_code.trim()) validationErrors.grant_code = 'Grant Code is required';
          if (!funderReferenceNumber.trim()) {
            validationErrors.funderReferenceNumber = 'Funder Reference Number is required';
          }
          if (!start_date) validationErrors.start_date = 'Start Date is required';
          if (!end_date) validationErrors.end_date = 'End Date is required';
          
          if (start_date && end_date) {
            const start = new Date(start_date);
            const end = new Date(end_date);
            if (end <= start) {
              validationErrors.end_date = 'End date must be after start date';
            }
          }
          break;
          
        case 2: // Financial Details
          if (!total_budget || parseFloat(total_budget) <= 0) {
            validationErrors.total_budget = 'Total Budget must be greater than 0';
          }
          if (!usdToMwkRate || parseFloat(usdToMwkRate) <= 0) {
            validationErrors.usdToMwkRate = 'Exchange rate must be greater than 0';
          }
          break;
          
        case 3: // Budget Categories
          if (budgetCategories.length === 0) {
            validationErrors.budgetCategories = 'At least one budget category is required';
          } else {
            budgetCategories.forEach((cat, i) => {
              if (!cat.name.trim()) {
                validationErrors[`category_${i}_name`] = 'Category name is required';
              }
              if (!cat.allocated || parseFloat(cat.allocated) < 0) {
                validationErrors[`category_${i}_allocated`] = 'Valid allocated amount is required';
              }
            });
          }
          
          if (total_budget && budgetCategories.length > 0) {
            if (!isBudgetBalanced) {
              validationErrors.budgetSum = 'Budget allocations must equal total budget';
            }
          }
          break;
          
        case 4: // Compliance - optional fields, minimal validation
          milestones.forEach((milestone, i) => {
            if (milestone.title || milestone.dueDate || milestone.reportingPeriod) {
              if (!milestone.title.trim()) {
                validationErrors[`milestone_${i}_title`] = 'Milestone title is required';
              }
              if (!milestone.dueDate) {
                validationErrors[`milestone_${i}_dueDate`] = 'Due date is required';
              }
            }
          });
          break;
          
        case 5: // Documents
          if (!agreement_file) {
            validationErrors.agreement = 'Grant Agreement PDF is required';
          }
          if (!budgetBreakdownFile) {
            validationErrors.budgetBreakdown = 'Budget Breakdown is required';
          }
          if (!awardLetterFile) {
            validationErrors.awardLetter = 'Award Letter is required';
          }
          break;
          
        case 6: // Team Members - optional but validate if provided
          teamMembers.forEach((member, i) => {
            if (member.name || member.email || member.role || member.dailyRate) {
              if (!member.name.trim()) {
                validationErrors[`team_${i}_name`] = 'Team member name is required';
              }
              if (!member.email.trim()) {
                validationErrors[`team_${i}_email`] = 'Team member email is required';
              } else if (!member.email.includes('@mubas.ac.mw')) {
                validationErrors[`team_${i}_email`] = 'Email must be a MUBAS domain';
              }
            }
          });
          break;
      }
      
      return Object.keys(validationErrors).length === 0;
    }

    const fieldError = (key) => (hasInteracted ? validationErrors[key] : null);
  
    function validateForm() {
      // Run validation for all steps
      const currentStepCache = currentStep;
      let allValid = true;
      
      for (let i = 1; i <= 6; i++) {
        currentStep = i;
        if (!validateCurrentStep()) {
          allValid = false;
          break;
        }
      }
      
      currentStep = currentStepCache;
      return allValid;
    }

    async function handleSubmit(e) {
      e.preventDefault();
      error = '';
      success = '';
      isLoading = true;

      // Final validation
      if (!validateForm()) {
        error = 'Please fix the validation errors in all steps';
        isLoading = false;
        return;
      }

      try {
        const formData = new FormData();
        formData.append('title', title.trim());
        formData.append('funder', funder === 'other' ? funderOther.trim() : FUNDERS.find(f => f.value === funder)?.label || funder);
        formData.append('grant_code', grant_code.trim());
        formData.append('funder_reference_number', funderReferenceNumber.trim());
        formData.append('start_date', start_date);
        formData.append('end_date', end_date);
        formData.append('currency', currency);
        formData.append('total_budget', parseFloat(total_budget));
        formData.append('exchange_rate', parseFloat(usdToMwkRate));
        formData.append('budget_categories', JSON.stringify(
          budgetCategories.map(cat => ({
            name: cat.name.trim(),
            allocated: parseFloat(cat.allocated || 0)
          }))
        ));
        formData.append('financial_reporting_frequency', financialReportingFrequency);
        formData.append('progress_reporting_frequency', progressReportingFrequency);
        
        // Add milestones
        if (milestones.length > 0) {
          const milestonesData = milestones
            .filter(m => m.title && m.dueDate)
            .map(m => ({
              title: m.title.trim(),
              description: m.description.trim(),
              due_date: m.dueDate,
              reporting_period: m.reportingPeriod,
              status: m.status
            }));
          formData.append('milestones', JSON.stringify(milestonesData));
          
          // Add evidence files separately with milestone index
          milestones.forEach((m, i) => {
            if (m.evidenceFile) {
              formData.append(`milestone_evidence_${i}`, m.evidenceFile);
            }
          });
        }
        
        formData.append('special_requirements', specialRequirements.trim());
        formData.append('agreement', agreement_file);
        if (budgetBreakdownFile) formData.append('budget_breakdown', budgetBreakdownFile);
        if (awardLetterFile) formData.append('award_letter', awardLetterFile);
        if (ethicalApprovalFile) formData.append('ethical_approval', ethicalApprovalFile);
        
        if (teamMembers.length > 0) {
          formData.append('team_members', JSON.stringify(
            teamMembers
              .filter(m => m.name && m.email)
              .map(m => ({
                name: m.name.trim(),
                email: m.email.trim(),
                role: m.role,
                daily_rate: parseFloat(m.dailyRate || 0)
              }))
          ));
        }

        await axios.post('http://localhost:5000/api/grants', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          withCredentials: true
        });

        success = 'Grant created successfully! Redirecting...';
        
        setTimeout(() => {
          router.goToGrants();
        }, 2000);
      } catch (err) {
        error = err.response?.data?.error || 'Failed to create grant';
        if (err.response?.data?.details) {
          error += ': ' + err.response.data.details;
        }
        currentStep = 1; // Go back to first step on error
      } finally {
        isLoading = false;
      }
    }

    function handleFileChange(fileType, e) {
      const file = e.target.files[0];
      if (!file) return;
      
      const isPdfRequired = ['agreement', 'awardLetter'].includes(fileType);
      const isPdf = file.name.toLowerCase().endsWith('.pdf');
      
      if (isPdfRequired && !isPdf) {
        validationErrors[fileType] = 'This file must be a PDF';
        return;
      }
      
      delete validationErrors[fileType];
      
      switch(fileType) {
        case 'agreement':
          agreement_file = file;
          break;
        case 'budgetBreakdown':
          budgetBreakdownFile = file;
          break;
        case 'awardLetter':
          awardLetterFile = file;
          break;
        case 'ethicalApproval':
          ethicalApprovalFile = file;
          break;
      }
      
      markInteracted();
    }

    function removeFile(fileType) {
      switch(fileType) {
        case 'agreement':
          agreement_file = null;
          break;
        case 'budgetBreakdown':
          budgetBreakdownFile = null;
          break;
        case 'awardLetter':
          awardLetterFile = null;
          break;
        case 'ethicalApproval':
          ethicalApprovalFile = null;
          break;
      }
      markInteracted();
    }
</script>

<style>
  .step-indicator {
    @apply relative flex items-center justify-center w-10 h-10 rounded-full transition-all duration-300;
  }
  
  .step-indicator.completed {
    @apply bg-emerald-500 text-white;
  }
  
  .step-indicator.active {
    @apply bg-blue-600 text-white ring-4 ring-blue-200;
  }
  
  .step-indicator.pending {
    @apply bg-gray-200 text-gray-500;
  }
  
  .progress-line {
    @apply absolute top-5 h-0.5 bg-gray-200 -z-10;
  }
  
  .progress-line.completed {
    @apply bg-emerald-500;
  }
</style>

{#if showPage}
  <Layout>
    <div class="max-w-6xl mx-auto space-y-6 pb-12">
      <!-- Header -->
      <div class="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl shadow-lg p-6">
        <h1 class="text-3xl font-bold mb-2">🎓 Grant Initialization & Setup</h1>
        <p class="text-blue-100">Principal Investigator Module | Create New Grant Project</p>
      </div>

      <!-- Progress Steps -->
      <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-6">
        <div class="relative">
          <div class="flex justify-between items-start mb-2">
            {#each Array(7) as _, i}
              {@const stepNum = i + 1}
              {@const isCompleted = stepNum < currentStep}
              {@const isActive = stepNum === currentStep}
              {@const isPending = stepNum > currentStep}
              
              <div class="flex flex-col items-center flex-1 relative">
                {#if i < 6}
                  <div class="progress-line {isCompleted ? 'completed' : ''}" style="left: 50%; right: -50%; width: 100%;"></div>
                {/if}
                
                <button
                  type="button"
                  on:click={() => goToStep(stepNum)}
                  class="step-indicator {isCompleted ? 'completed' : isActive ? 'active' : 'pending'} relative z-10"
                  disabled={stepNum > currentStep && !validateStepsUpTo(stepNum - 1)}
                >
                  {#if isCompleted}
                    ✓
                  {:else}
                    {stepNum}
                  {/if}
                </button>
                
                <span class="text-xs mt-2 text-center font-medium max-w-[80px] {isActive ? 'text-blue-600' : 'text-gray-600'}">
                  {['Basic Info', 'Financial', 'Budget', 'Compliance', 'Documents', 'Team', 'Review'][i]}
                </span>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <!-- Info Alert -->
      <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 flex gap-3">
        <span class="text-2xl">ℹ️</span>
        <div class="text-sm text-blue-900">
          <strong>Before you begin:</strong> Ensure you have your official grant award letter, approved budget breakdown, 
          and all required documents ready for upload. This process takes approximately 30 minutes.
        </div>
      </div>

      {#if error}
        <div class="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-start gap-2">
          <span class="text-xl">⚠️</span>
          <span>{error}</span>
        </div>
      {/if}
      
      {#if success}
        <div class="p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl flex items-start gap-2">
          <span class="text-xl">✓</span>
          <span>{success}</span>
        </div>
      {/if}

      <form on:submit={handleSubmit} class="space-y-6">
        <!-- Step 1: Basic Grant Information -->
        {#if currentStep === 1}
          <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-8">
            <div class="border-l-4 border-blue-600 pl-4 mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Basic Grant Information</h2>
              <p class="text-sm text-gray-600 mt-1">Enter the fundamental details of your grant award as they appear in your official award letter.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="md:col-span-2">
                <label for="title" class="block text-sm font-medium text-gray-700 mb-2">
                  Grant Title <span class="text-red-500">*</span>
                </label>
                <input
                  id="title"
                  type="text"
                  placeholder="e.g., Climate Resilience in Southern Malawi 2024"
                  class="w-full px-4 py-2.5 border {fieldError('title') ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={title}
                  on:input={markInteracted}
                />
                {#if fieldError('title')}
                  <p class="mt-1 text-sm text-red-600">{fieldError('title')}</p>
                {:else}
                  <p class="mt-1 text-xs text-gray-500">Use the official project title from your award letter</p>
                {/if}
              </div>

              <div>
                <label for="funder" class="block text-sm font-medium text-gray-700 mb-2">
                  Funder Name <span class="text-red-500">*</span>
                </label>
                <select
                  id="funder"
                  class="w-full px-4 py-2.5 border {fieldError('funder') ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={funder}
                  on:change={markInteracted}
                >
                  <option value="">Select Funder</option>
                  {#each FUNDERS as funderOption}
                    <option value={funderOption.value}>{funderOption.label}</option>
                  {/each}
                </select>
                {#if fieldError('funder')}
                  <p class="mt-1 text-sm text-red-600">{fieldError('funder')}</p>
                {/if}
              </div>

              {#if funder === 'other'}
                <div>
                  <label for="funderOther" class="block text-sm font-medium text-gray-700 mb-2">
                    Specify Funder <span class="text-red-500">*</span>
                  </label>
                  <input
                    id="funderOther"
                    type="text"
                    placeholder="Enter funder name"
                    class="w-full px-4 py-2.5 border {fieldError('funderOther') ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    bind:value={funderOther}
                    on:input={markInteracted}
                  />
                  {#if fieldError('funderOther')}
                    <p class="mt-1 text-sm text-red-600">{fieldError('funderOther')}</p>
                  {/if}
                </div>
              {/if}

              <div>
                <label for="grant_code" class="block text-sm font-medium text-gray-700 mb-2">
                  Unique Grant Code <span class="text-red-500">*</span>
                </label>
                <input
                  id="grant_code"
                  type="text"
                  placeholder="e.g., MUBAS-CLIM-2024-001"
                  class="w-full px-4 py-2.5 border {fieldError('grant_code') ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={grant_code}
                  on:input={markInteracted}
                />
                {#if fieldError('grant_code')}
                  <p class="mt-1 text-sm text-red-600">{fieldError('grant_code')}</p>
                {:else}
                  <p class="mt-1 text-xs text-gray-500">System will validate uniqueness</p>
                {/if}
              </div>

              <div>
                <label for="funderRef" class="block text-sm font-medium text-gray-700 mb-2">
                  Funder Reference Number <span class="text-red-500">*</span>
                </label>
                <input
                  id="funderRef"
                  type="text"
                  placeholder="As shown on award letter"
                  class="w-full px-4 py-2.5 border {fieldError('funderReferenceNumber') ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={funderReferenceNumber}
                  on:input={markInteracted}
                />
                {#if fieldError('funderReferenceNumber')}
                  <p class="mt-1 text-sm text-red-600">{fieldError('funderReferenceNumber')}</p>
                {/if}
              </div>

              <div>
                <label for="pi" class="block text-sm font-medium text-gray-700 mb-2">
                  Principal Investigator <span class="text-red-500">*</span>
                </label>
                <input
                  id="pi"
                  type="text"
                  class="w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50"
                  value={principalInvestigator}
                  readonly
                />
                <p class="mt-1 text-xs text-gray-500">Auto-filled from your profile</p>
              </div>

              <div>
                <label for="start_date" class="block text-sm font-medium text-gray-700 mb-2">
                  Project Start Date <span class="text-red-500">*</span>
                </label>
                <input
                  id="start_date"
                  type="date"
                  class="w-full px-4 py-2.5 border {fieldError('start_date') ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={start_date}
                  on:input={markInteracted}
                />
                {#if fieldError('start_date')}
                  <p class="mt-1 text-sm text-red-600">{fieldError('start_date')}</p>
                {/if}
              </div>

              <div>
                <label for="end_date" class="block text-sm font-medium text-gray-700 mb-2">
                  Project End Date <span class="text-red-500">*</span>
                </label>
                <input
                  id="end_date"
                  type="date"
                  class="w-full px-4 py-2.5 border {fieldError('end_date') ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={end_date}
                  on:input={markInteracted}
                />
                {#if fieldError('end_date')}
                  <p class="mt-1 text-sm text-red-600">{fieldError('end_date')}</p>
                {:else if projectDuration}
                  <p class="mt-1 text-xs text-gray-500">Duration: {projectDuration}</p>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        <!-- Step 2: Financial Details & Currency -->
        {#if currentStep === 2}
          <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-8">
            <div class="border-l-4 border-blue-600 pl-4 mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Financial Details & Currency</h2>
              <p class="text-sm text-gray-600 mt-1">Set the total award amount and fixed exchange rate for the entire project duration.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label for="currency" class="block text-sm font-medium text-gray-700 mb-2">
                  Award Currency <span class="text-red-500">*</span>
                </label>
                <select
                  id="currency"
                  class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={currency}
                  on:change={markInteracted}
                >
                  <option value="usd">USD - US Dollar</option>
                  <option value="eur">EUR - Euro</option>
                  <option value="gbp">GBP - British Pound</option>
                  <option value="mwk">MWK - Malawi Kwacha</option>
                </select>
              </div>

              <div>
                <label for="total_budget" class="block text-sm font-medium text-gray-700 mb-2">
                  Total Award Amount <span class="text-red-500">*</span>
                </label>
                <div class="flex">
                  <span class="inline-flex items-center px-4 bg-gray-100 border border-r-0 border-gray-300 rounded-l-lg text-gray-600 font-medium">
                    $
                  </span>
                  <input
                    id="total_budget"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="50000.00"
                    class="flex-1 px-4 py-2.5 border {fieldError('total_budget') ? 'border-red-500' : 'border-gray-300'} rounded-r-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    bind:value={total_budget}
                    on:input={markInteracted}
                  />
                </div>
                {#if fieldError('total_budget')}
                  <p class="mt-1 text-sm text-red-600">{fieldError('total_budget')}</p>
                {/if}
              </div>

              <div>
                <label for="exchangeRate" class="block text-sm font-medium text-gray-700 mb-2">
                  Fixed Exchange Rate (USD to MWK) <span class="text-red-500">*</span>
                </label>
                <div class="flex items-center gap-2">
                  <span class="text-sm text-gray-600 whitespace-nowrap">1 USD =</span>
                  <input
                    id="exchangeRate"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="1700.00"
                    class="flex-1 px-4 py-2.5 border {fieldError('usdToMwkRate') ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    bind:value={usdToMwkRate}
                    on:input={markInteracted}
                  />
                  <span class="text-sm text-gray-600">MWK</span>
                </div>
                {#if fieldError('usdToMwkRate')}
                  <p class="mt-1 text-sm text-red-600">{fieldError('usdToMwkRate')}</p>
                {:else}
                  <p class="mt-1 text-xs text-amber-600">⚠️ This rate will be locked for the entire project</p>
                {/if}
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Total in Malawi Kwacha (Auto-calculated)
                </label>
                <input
                  type="text"
                  class="w-full px-4 py-2.5 border border-emerald-300 rounded-lg bg-emerald-50 font-semibold text-emerald-900"
                  value="MWK {Math.round($mwkValue).toLocaleString()}"
                  readonly
                />
              </div>
            </div>
          </div>
        {/if}

        <!-- Step 3: Budget Allocation -->
        {#if currentStep === 3}
          <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-8">
            <div class="border-l-4 border-blue-600 pl-4 mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Budget Allocation by Category</h2>
              <p class="text-sm text-gray-600 mt-1">Break down your total award into standard budget categories. The sum must equal your total award amount.</p>
            </div>

            {#if fieldError('budgetSum')}
              <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                <span class="text-red-600">⚠️</span>
                <p class="text-sm text-red-700">{fieldError('budgetSum')}</p>
              </div>
            {/if}

            <div class="overflow-x-auto">
              <table class="w-full border-collapse">
                <thead>
                  <tr class="bg-gray-50">
                    <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b-2 border-gray-200">Budget Category</th>
                    <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b-2 border-gray-200">Amount (USD)</th>
                    <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b-2 border-gray-200">Amount (MWK)</th>
                    <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b-2 border-gray-200">%</th>
                  </tr>
                </thead>
                <tbody>
                  {#each budgetCategories as cat, i}
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3 border-b border-gray-200">
                        <input
                          type="text"
                          placeholder="Category name"
                          class="w-full px-3 py-2 border {fieldError(`category_${i}_name`) ? 'border-red-500' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          value={cat.name}
                          on:input={(e) => updateCategory(i, 'name', e.target.value)}
                        />
                        {#if fieldError(`category_${i}_name`)}
                          <p class="mt-1 text-xs text-red-600">{fieldError(`category_${i}_name`)}</p>
                        {/if}
                      </td>
                      <td class="px-4 py-3 border-b border-gray-200">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          placeholder="0.00"
                          class="w-full px-3 py-2 border {fieldError(`category_${i}_allocated`) ? 'border-red-500' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          value={cat.allocated}
                          on:input={(e) => updateCategory(i, 'allocated', e.target.value)}
                        />
                        {#if fieldError(`category_${i}_allocated`)}
                          <p class="mt-1 text-xs text-red-600">{fieldError(`category_${i}_allocated`)}</p>
                        {/if}
                      </td>
                      <td class="px-4 py-3 border-b border-gray-200">
                        <input
                          type="text"
                          class="w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50"
                          value={(parseFloat(cat.allocated || 0) * usdToMwkRate).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          readonly
                        />
                      </td>
                      <td class="px-4 py-3 border-b border-gray-200">
                        <span class="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                          {getCategoryPercentage(cat.allocated)}%
                        </span>
                      </td>
                    </tr>
                  {/each}
                  <tr class="bg-blue-50 font-semibold">
                    <td class="px-4 py-3 border-t-2 border-blue-600">TOTAL</td>
                    <td class="px-4 py-3 border-t-2 border-blue-600">$ {totalAllocated.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="px-4 py-3 border-t-2 border-blue-600">MWK {(totalAllocated * usdToMwkRate).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="px-4 py-3 border-t-2 border-blue-600">
                      <span class="inline-block px-3 py-1 {isBudgetBalanced ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'} rounded-full text-xs font-semibold">
                        {((totalAllocated / totalBudgetNumber) * 100 || 0).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="mt-4 flex items-center justify-between">
              <button
                type="button"
                on:click={addCategory}
                class="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm font-medium"
              >
                + Add Category
              </button>
              
              {#if isBudgetBalanced && totalBudgetNumber > 0}
                <div class="flex items-center gap-2 text-emerald-700 text-sm font-medium">
                  <span class="text-lg">✓</span>
                  <span>Budget allocation is balanced and equals total award amount</span>
                </div>
              {:else if totalBudgetNumber > 0}
                <div class="flex items-center gap-2 text-amber-700 text-sm font-medium">
                  <span>Balance: ${Math.abs(budgetBalance).toFixed(2)} {budgetBalance > 0 ? 'remaining' : 'over budget'}</span>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Step 4: Compliance & Reporting -->
        {#if currentStep === 4}
          <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-8">
            <div class="border-l-4 border-blue-600 pl-4 mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Compliance Rules & Reporting Schedule</h2>
              <p class="text-sm text-gray-600 mt-1">Configure reporting requirements, milestones, and special funder conditions.</p>
            </div>

            <!-- Reporting Frequencies -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div>
                <label for="financialFreq" class="block text-sm font-medium text-gray-700 mb-2">
                  Financial Reporting Frequency <span class="text-red-500">*</span>
                </label>
                <select
                  id="financialFreq"
                  class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={financialReportingFrequency}
                  on:change={markInteracted}
                >
                  {#each REPORT_FREQUENCIES as freq}
                    <option value={freq.value}>{freq.label}</option>
                  {/each}
                </select>
              </div>

              <div>
                <label for="progressFreq" class="block text-sm font-medium text-gray-700 mb-2">
                  Progress Reporting Frequency <span class="text-red-500">*</span>
                </label>
                <select
                  id="progressFreq"
                  class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  bind:value={progressReportingFrequency}
                  on:change={markInteracted}
                >
                  {#each REPORT_FREQUENCIES as freq}
                    <option value={freq.value}>{freq.label}</option>
                  {/each}
                </select>
              </div>
            </div>

            <!-- Milestones Section -->
            <div class="mb-8">
              <div class="flex justify-between items-start mb-4">
                <div>
                  <h3 class="text-lg font-semibold text-gray-900">Key Milestones & Deliverables</h3>
                  <p class="text-xs text-gray-600 mt-1">
                    Define project milestones with reporting periods based on your grant timeline 
                    {#if projectDuration}
                      ({projectDuration})
                    {/if}
                  </p>
                  {#if reportingPeriods.length > 0}
                    <div class="flex flex-wrap gap-2 mt-2">
                      <span class="text-xs text-gray-500">Available reporting periods:</span>
                      {#each reportingPeriods as period}
                        <span class="inline-block px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                          {period.label}
                        </span>
                      {/each}
                    </div>
                  {/if}
                </div>
                <button
                  type="button"
                  on:click={addMilestone}
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium whitespace-nowrap"
                  disabled={!start_date || !end_date}
                >
                  + Add Milestone
                </button>
              </div>

              {#if !start_date || !end_date}
                <div class="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                  ℹ️ Please set project start and end dates first to enable milestone creation with reporting periods.
                </div>
              {/if}

              {#if milestones.length === 0 && start_date && end_date}
                <div class="p-8 border-2 border-dashed border-gray-300 rounded-lg text-center text-gray-500">
                  <p class="text-sm">No milestones added yet. Click "Add Milestone" to get started.</p>
                </div>
              {/if}

              {#if milestones.length > 0}
                <div class="space-y-4">
                  {#each milestones as milestone, i}
                    <div class="border border-gray-200 rounded-lg p-6 bg-gray-50 space-y-4">
                      <div class="flex justify-between items-start">
                        <h4 class="text-sm font-semibold text-gray-900">Milestone {i + 1}</h4>
                        <button
                          type="button"
                          on:click={() => removeMilestone(i)}
                          class="text-red-600 hover:text-red-700 text-sm font-medium"
                        >
                          Remove
                        </button>
                      </div>

                      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <!-- Title -->
                        <div class="md:col-span-2">
                          <label class="block text-xs font-medium text-gray-700 mb-1">
                            Milestone Title <span class="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            placeholder="e.g., Fieldwork Phase 1 Complete"
                            class="w-full px-3 py-2 border {fieldError(`milestone_${i}_title`) ? 'border-red-500' : 'border-gray-300'} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={milestone.title}
                            on:input={(e) => updateMilestone(i, 'title', e.target.value)}
                          />
                          {#if fieldError(`milestone_${i}_title`)}
                            <p class="mt-1 text-xs text-red-600">{fieldError(`milestone_${i}_title`)}</p>
                          {/if}
                        </div>

                        <!-- Description -->
                        <div class="md:col-span-2">
                          <label class="block text-xs font-medium text-gray-700 mb-1">
                            Description (Optional)
                          </label>
                          <textarea
                            rows="2"
                            placeholder="Detailed description of the milestone and expected deliverables..."
                            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={milestone.description}
                            on:input={(e) => updateMilestone(i, 'description', e.target.value)}
                          ></textarea>
                        </div>

                        <!-- Due Date -->
                        <div>
                          <label class="block text-xs font-medium text-gray-700 mb-1">
                            Due Date <span class="text-red-500">*</span>
                          </label>
                          <input
                            type="date"
                            min={start_date}
                            max={end_date}
                            class="w-full px-3 py-2 border {fieldError(`milestone_${i}_dueDate`) ? 'border-red-500' : 'border-gray-300'} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={milestone.dueDate}
                            on:input={(e) => updateMilestone(i, 'dueDate', e.target.value)}
                          />
                          {#if fieldError(`milestone_${i}_dueDate`)}
                            <p class="mt-1 text-xs text-red-600">{fieldError(`milestone_${i}_dueDate`)}</p>
                          {/if}
                        </div>

                        <!-- Reporting Period -->
                        <div>
                          <label class="block text-xs font-medium text-gray-700 mb-1">
                            Reporting Period (Optional)
                          </label>
                          <select
                            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={milestone.reportingPeriod}
                            on:change={(e) => updateMilestone(i, 'reportingPeriod', e.target.value)}
                          >
                            <option value="">Select period (optional)</option>
                            {#each reportingPeriods as period}
                              <option value={period.value}>{period.label}</option>
                            {/each}
                          </select>
                          <p class="mt-1 text-xs text-gray-500">
                            Links this milestone to a reporting cycle for grouping and filtering
                          </p>
                        </div>

                        <!-- Status -->
                        <div>
                          <label class="block text-xs font-medium text-gray-700 mb-1">
                            Status
                          </label>
                          <select
                            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={milestone.status}
                            on:change={(e) => updateMilestone(i, 'status', e.target.value)}
                          >
                            <option value="not_started">Not Started</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                          </select>
                        </div>

                        <!-- Evidence File -->
                        <div class="md:col-span-2">
                          <label class="block text-xs font-medium text-gray-700 mb-1">
                            Evidence File (Optional)
                          </label>
                          {#if !milestone.evidenceFile}
                            <label class="flex items-center justify-center w-full h-20 border-2 border-dashed border-gray-300 rounded-md cursor-pointer hover:bg-gray-50 transition-colors">
                              <div class="text-center">
                                <p class="text-xs text-gray-600">
                                  <span class="font-semibold">Click to upload</span> evidence document
                                </p>
                                <p class="text-xs text-gray-400">PDF, DOC, DOCX, JPG, PNG (Max 5MB)</p>
                              </div>
                              <input
                                type="file"
                                class="hidden"
                                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                                on:change={(e) => handleMilestoneFileChange(i, e)}
                              />
                            </label>
                          {:else}
                            <div class="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-md">
                              <div class="flex items-center gap-2">
                                <span class="text-lg">📎</span>
                                <div>
                                  <p class="text-xs font-medium text-gray-900">{milestone.evidenceFile.name}</p>
                                  <p class="text-xs text-gray-500">{(milestone.evidenceFile.size / 1024).toFixed(1)} KB</p>
                                </div>
                              </div>
                              <button
                                type="button"
                                on:click={() => removeMilestoneFile(i)}
                                class="text-red-600 hover:text-red-700 text-sm font-bold"
                              >
                                ✕
                              </button>
                            </div>
                          {/if}
                        </div>

                        <!-- Auto-filled fields (shown when status is completed) -->
                        {#if milestone.status === 'completed'}
                          <div class="md:col-span-2 p-3 bg-emerald-50 border border-emerald-200 rounded-md">
                            <p class="text-xs font-medium text-emerald-900 mb-2">Completion Information</p>
                            <div class="grid grid-cols-2 gap-3 text-xs text-emerald-800">
                              <div>
                                <span class="font-medium">Completed on:</span>
                                <span class="ml-1">{milestone.completionDate || 'Auto-filled on save'}</span>
                              </div>
                              <div>
                                <span class="font-medium">Completed by:</span>
                                <span class="ml-1">{milestone.completedBy || 'Auto-filled from user'}</span>
                              </div>
                            </div>
                          </div>
                        {/if}
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>

            <!-- Special Requirements -->
            <div>
              <label for="specialReq" class="block text-sm font-medium text-gray-700 mb-2">
                Special Funder Requirements
              </label>
              <textarea
                id="specialReq"
                rows="4"
                placeholder="Enter any specific rules, e.g.:&#10;- All expenses over $500 require prior approval&#10;- Equipment purchases require 3 quotations&#10;- Field evidence must include GPS coordinates"
                class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                bind:value={specialRequirements}
                on:input={markInteracted}
              ></textarea>
            </div>
          </div>
        {/if}

        <!-- Step 5: Required Documents -->
        {#if currentStep === 5}
          <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-8">
            <div class="border-l-4 border-blue-600 pl-4 mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Required Documents</h2>
              <p class="text-sm text-gray-600 mt-1">Upload all mandatory documents to activate your grant.</p>
            </div>

            <div class="space-y-6">
              <!-- Official Grant Agreement -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Official Grant Agreement / Contract <span class="text-red-500">*</span>
                </label>
                {#if !agreement_file}
                  <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed {validationErrors.agreement ? 'border-red-500 bg-red-50' : 'border-gray-300 bg-gray-50'} rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
                    <div class="flex flex-col items-center justify-center pt-5 pb-6">
                      <span class="text-4xl mb-2">📄</span>
                      <p class="mb-1 text-sm text-gray-600"><span class="font-semibold">Click to upload</span> or drag and drop</p>
                      <p class="text-xs text-gray-500">PDF, DOC, DOCX (Max 10MB)</p>
                    </div>
                    <input
                      type="file"
                      class="hidden"
                      accept=".pdf,.doc,.docx"
                      on:change={(e) => handleFileChange('agreement', e)}
                    />
                  </label>
                {:else}
                  <div class="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <div class="flex items-center gap-3">
                      <span class="text-2xl">📄</span>
                      <div>
                        <p class="font-medium text-gray-900">{agreement_file.name}</p>
                        <p class="text-xs text-gray-500">{(agreement_file.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      on:click={() => removeFile('agreement')}
                      class="text-red-600 hover:text-red-700 text-xl font-bold"
                    >
                      ✕
                    </button>
                  </div>
                {/if}
                {#if validationErrors.agreement}
                  <p class="mt-1 text-sm text-red-600">{validationErrors.agreement}</p>
                {/if}
              </div>

              <!-- Budget Breakdown -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Approved Budget Breakdown <span class="text-red-500">*</span>
                </label>
                {#if !budgetBreakdownFile}
                  <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed {validationErrors.budgetBreakdown ? 'border-red-500 bg-red-50' : 'border-gray-300 bg-gray-50'} rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
                    <div class="flex flex-col items-center justify-center pt-5 pb-6">
                      <span class="text-4xl mb-2">📊</span>
                      <p class="mb-1 text-sm text-gray-600"><span class="font-semibold">Click to upload</span> or drag and drop</p>
                      <p class="text-xs text-gray-500">PDF, XLSX, XLS (Max 10MB)</p>
                    </div>
                    <input
                      type="file"
                      class="hidden"
                      accept=".pdf,.xlsx,.xls"
                      on:change={(e) => handleFileChange('budgetBreakdown', e)}
                    />
                  </label>
                {:else}
                  <div class="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <div class="flex items-center gap-3">
                      <span class="text-2xl">📊</span>
                      <div>
                        <p class="font-medium text-gray-900">{budgetBreakdownFile.name}</p>
                        <p class="text-xs text-gray-500">{(budgetBreakdownFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      on:click={() => removeFile('budgetBreakdown')}
                      class="text-red-600 hover:text-red-700 text-xl font-bold"
                    >
                      ✕
                    </button>
                  </div>
                {/if}
                {#if validationErrors.budgetBreakdown}
                  <p class="mt-1 text-sm text-red-600">{validationErrors.budgetBreakdown}</p>
                {/if}
              </div>

              <!-- Award Letter -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Award Letter <span class="text-red-500">*</span>
                </label>
                {#if !awardLetterFile}
                  <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed {validationErrors.awardLetter ? 'border-red-500 bg-red-50' : 'border-gray-300 bg-gray-50'} rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
                    <div class="flex flex-col items-center justify-center pt-5 pb-6">
                      <span class="text-4xl mb-2">📧</span>
                      <p class="mb-1 text-sm text-gray-600"><span class="font-semibold">Click to upload</span> or drag and drop</p>
                      <p class="text-xs text-gray-500">PDF (Max 5MB)</p>
                    </div>
                    <input
                      type="file"
                      class="hidden"
                      accept=".pdf"
                      on:change={(e) => handleFileChange('awardLetter', e)}
                    />
                  </label>
                {:else}
                  <div class="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <div class="flex items-center gap-3">
                      <span class="text-2xl">📧</span>
                      <div>
                        <p class="font-medium text-gray-900">{awardLetterFile.name}</p>
                        <p class="text-xs text-gray-500">{(awardLetterFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      on:click={() => removeFile('awardLetter')}
                      class="text-red-600 hover:text-red-700 text-xl font-bold"
                    >
                      ✕
                    </button>
                  </div>
                {/if}
                {#if validationErrors.awardLetter}
                  <p class="mt-1 text-sm text-red-600">{validationErrors.awardLetter}</p>
                {/if}
              </div>

              <!-- Ethical Approval (optional) -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Ethical Approval Certificate (if applicable)
                </label>
                {#if !ethicalApprovalFile}
                  <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors">
                    <div class="flex flex-col items-center justify-center pt-5 pb-6">
                      <span class="text-4xl mb-2">🔒</span>
                      <p class="mb-1 text-sm text-gray-600"><span class="font-semibold">Click to upload</span> or drag and drop</p>
                      <p class="text-xs text-gray-500">PDF (Max 5MB)</p>
                    </div>
                    <input
                      type="file"
                      class="hidden"
                      accept=".pdf"
                      on:change={(e) => handleFileChange('ethicalApproval', e)}
                    />
                  </label>
                {:else}
                  <div class="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <div class="flex items-center gap-3">
                      <span class="text-2xl">🔒</span>
                      <div>
                        <p class="font-medium text-gray-900">{ethicalApprovalFile.name}</p>
                        <p class="text-xs text-gray-500">{(ethicalApprovalFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      on:click={() => removeFile('ethicalApproval')}
                      class="text-red-600 hover:text-red-700 text-xl font-bold"
                    >
                      ✕
                    </button>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        <!-- Step 6: Team Members -->
        {#if currentStep === 6}
          <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-8">
            <div class="border-l-4 border-blue-600 pl-4 mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Team Members & Pre-registration</h2>
              <p class="text-sm text-gray-600 mt-1">Add team members who will work on this grant. They will receive invitation links to join the project.</p>
            </div>

            <div class="space-y-4">
              {#each teamMembers as member, i}
                <div class="grid grid-cols-1 md:grid-cols-5 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Full Name <span class="text-red-500">*</span></label>
                    <input
                      type="text"
                      placeholder="e.g., John Phiri"
                      class="w-full px-3 py-2 border {fieldError(`team_${i}_name`) ? 'border-red-500' : 'border-gray-300'} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={member.name}
                      on:input={(e) => updateTeamMember(i, 'name', e.target.value)}
                    />
                    {#if fieldError(`team_${i}_name`)}
                      <p class="mt-1 text-xs text-red-600">{fieldError(`team_${i}_name`)}</p>
                    {/if}
                  </div>

                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">MUBAS Email <span class="text-red-500">*</span></label>
                    <input
                      type="email"
                      placeholder="j.phiri@mubas.ac.mw"
                      class="w-full px-3 py-2 border {fieldError(`team_${i}_email`) ? 'border-red-500' : 'border-gray-300'} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={member.email}
                      on:input={(e) => updateTeamMember(i, 'email', e.target.value)}
                    />
                    {#if fieldError(`team_${i}_email`)}
                      <p class="mt-1 text-xs text-red-600">{fieldError(`team_${i}_email`)}</p>
                    {/if}
                  </div>

                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Role <span class="text-red-500">*</span></label>
                    <select
                      class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={member.role}
                      on:change={(e) => updateTeamMember(i, 'role', e.target.value)}
                    >
                      {#each TEAM_ROLES as role}
                        <option value={role.value}>{role.label}</option>
                      {/each}
                    </select>
                  </div>

                  <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Daily Rate (MWK)</label>
                    <input
                      type="number"
                      placeholder="5000"
                      min="0"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={member.dailyRate}
                      on:input={(e) => updateTeamMember(i, 'dailyRate', e.target.value)}
                    />
                  </div>

                  <div class="flex items-end">
                    <button
                      type="button"
                      on:click={() => removeTeamMember(i)}
                      class="w-full px-3 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 text-sm font-medium"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              {/each}

              <button
                type="button"
                on:click={addTeamMember}
                class="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium border-2 border-dashed border-gray-300"
              >
                + Add Team Member
              </button>
            </div>
          </div>
        {/if}

        <!-- Step 7: Review & Submit -->
        {#if currentStep === 7}
          <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-8">
            <div class="border-l-4 border-blue-600 pl-4 mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Review & Submit</h2>
              <p class="text-sm text-gray-600 mt-1">Please review all information before submitting for RSU approval.</p>
            </div>

            <div class="space-y-6">
              <!-- Basic Info Summary -->
              <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Basic Information</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><span class="font-medium">Title:</span> {title}</div>
                  <div><span class="font-medium">Funder:</span> {funder === 'other' ? funderOther : FUNDERS.find(f => f.value === funder)?.label || funder}</div>
                  <div><span class="font-medium">Grant Code:</span> {grant_code}</div>
                  <div><span class="font-medium">Duration:</span> {start_date} to {end_date}</div>
                </div>
              </div>

              <!-- Financial Summary -->
              <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Financial Details</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><span class="font-medium">Total Budget:</span> ${parseFloat(total_budget).toLocaleString()}</div>
                  <div><span class="font-medium">In MWK:</span> MWK {Math.round($mwkValue).toLocaleString()}</div>
                  <div><span class="font-medium">Exchange Rate:</span> 1 USD = {usdToMwkRate} MWK</div>
                  <div><span class="font-medium">Budget Status:</span> 
                    <span class="{isBudgetBalanced ? 'text-emerald-600' : 'text-red-600'}">
                      {isBudgetBalanced ? '✓ Balanced' : '⚠️ Not Balanced'}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Documents Summary -->
              <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Uploaded Documents</h3>
                <div class="space-y-2 text-sm">
                  <div class="flex items-center gap-2">
                    {#if agreement_file}
                      <span class="text-emerald-600">✓</span> Agreement: {agreement_file.name}
                    {:else}
                      <span class="text-red-600">✗</span> Agreement: Not uploaded
                    {/if}
                  </div>
                  <div class="flex items-center gap-2">
                    {#if budgetBreakdownFile}
                      <span class="text-emerald-600">✓</span> Budget Breakdown: {budgetBreakdownFile.name}
                    {:else}
                      <span class="text-red-600">✗</span> Budget Breakdown: Not uploaded
                    {/if}
                  </div>
                  <div class="flex items-center gap-2">
                    {#if awardLetterFile}
                      <span class="text-emerald-600">✓</span> Award Letter: {awardLetterFile.name}
                    {:else}
                      <span class="text-red-600">✗</span> Award Letter: Not uploaded
                    {/if}
                  </div>
                  {#if ethicalApprovalFile}
                    <div class="flex items-center gap-2">
                      <span class="text-emerald-600">✓</span> Ethical Approval: {ethicalApprovalFile.name}
                    </div>
                  {/if}
                </div>
              </div>

              <!-- Milestones Summary -->
              {#if milestones.length > 0}
                <div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-3">Milestones & Deliverables</h3>
                  <div class="space-y-3">
                    {#each milestones.filter(m => m.title && m.dueDate) as milestone, i}
                      <div class="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <div class="flex justify-between items-start mb-2">
                          <div class="font-medium text-sm text-gray-900">{milestone.title}</div>
                          <span class="px-2 py-1 text-xs rounded-full {
                            milestone.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                            milestone.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                            'bg-gray-100 text-gray-700'
                          }">
                            {milestone.status === 'completed' ? 'Completed' :
                             milestone.status === 'in_progress' ? 'In Progress' :
                             'Not Started'}
                          </span>
                        </div>
                        {#if milestone.description}
                          <p class="text-xs text-gray-600 mb-2">{milestone.description}</p>
                        {/if}
                        <div class="flex flex-wrap gap-3 text-xs text-gray-600">
                          <div><span class="font-medium">Due:</span> {new Date(milestone.dueDate).toLocaleDateString()}</div>
                          {#if milestone.reportingPeriod}
                            <div>
                              <span class="font-medium">Period:</span> 
                              {reportingPeriods.find(p => p.value === milestone.reportingPeriod)?.label || milestone.reportingPeriod}
                            </div>
                          {/if}
                          {#if milestone.evidenceFile}
                            <div class="text-emerald-600">📎 Evidence attached</div>
                          {/if}
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Team Summary -->
              {#if teamMembers.length > 0}
                <div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-3">Team Members</h3>
                  <div class="text-sm space-y-1">
                    {#each teamMembers.filter(m => m.name && m.email) as member}
                      <div>{member.name} ({member.email}) - {TEAM_ROLES.find(r => r.value === member.role)?.label}</div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          </div>

          <!-- Compliance Reminder -->
          <div class="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <p class="font-semibold text-blue-900 mb-3">Compliance reminder</p>
            <ul class="list-disc list-inside space-y-2 text-sm text-blue-900">
              <li>Grant Code must exactly match the agreement for audit traceability.</li>
              <li>Upload the fully executed PDF agreement—drafts are not acceptable.</li>
              <li>Budget allocations must equal the total USD ceiling (±$0.01 tolerance).</li>
              <li>Use the displayed conversion as guidance when reconciling MWK payments.</li>
            </ul>
          </div>
        {/if}

        <!-- Navigation Buttons -->
        <div class="flex items-center justify-between pt-6 border-t border-gray-200">
          <div class="flex gap-3">
            {#if currentStep > 1}
              <button
                type="button"
                on:click={prevStep}
                class="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium"
              >
                ← Previous
              </button>
            {/if}
          </div>

          <div class="flex gap-3">
            <button
              type="button"
              on:click={() => router.goToGrants()}
              class="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium"
              disabled={isLoading}
            >
              Cancel
            </button>

            {#if currentStep < 7}
              <button
                type="button"
                on:click={nextStep}
                class="px-6 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium shadow-md"
              >
                Next →
              </button>
            {:else}
              <button
                type="submit"
                class="px-8 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 font-medium shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isLoading}
              >
                {isLoading ? 'Submitting...' : 'Submit for RSU Approval'}
              </button>
            {/if}
          </div>
        </div>
      </form>

      {#if error}
         <!-- Show detailed validation errors if they exist -->
         <div class="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
           <h4 class="font-bold text-red-800 mb-2">Submission Failed</h4>
           <p class="text-red-700 mb-2">{error}</p>
           {#if Object.keys(validationErrors).length > 0}
             <ul class="list-disc list-inside text-sm text-red-600">
               {#each Object.entries(validationErrors) as [field, msg]}
                 <li><span class="font-medium capitalize">{field.replace(/_/g, ' ')}:</span> {msg}</li>
               {/each}
             </ul>
           {/if}
         </div>
      {/if}

      <!-- What Happens Next -->
      <div class="bg-blue-50 border border-blue-200 rounded-xl p-6 flex gap-4">
        <span class="text-3xl">💡</span>
        <div class="text-sm text-blue-900">
          <strong class="block mb-2">What happens next?</strong>
          <p>Once submitted, the Research Support Unit (RSU) will review your grant initialization within 2 business days. 
          You'll receive an email notification when it's approved, and your grant will become ACTIVE in the system.</p>
        </div>
      </div>
    </div>
  </Layout>
{/if}