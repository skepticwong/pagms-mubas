<!-- frontend/src/pages/CreateGrant.svelte -->
<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    import { tweened } from 'svelte/motion';
    import { cubicOut } from 'svelte/easing';
    import Layout from '../components/Layout.svelte';
    import Icon from '../components/Icon.svelte';
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

    let funderProfiles = [];
    
    onMount(async () => {
      try {
        const response = await axios.get('/api/rule-profiles/active', { withCredentials: true });
        funderProfiles = response.data.profiles || [];
      } catch (err) {
        console.error("Failed to fetch funder profiles", err);
      }
    });

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
    let currentStep = 1;
    let error = '';
    let success = '';
    let isLoading = false;
    let validationErrors = {};
    let showPage = true;
    let hasInteracted = false;

    // Step 2: Financial Details
    let currency = 'usd';
    let total_budget = '';
    let usdToMwkRate = 1700;
    const mwkValue = tweened(0, { duration: 250, easing: cubicOut });
    
    // Budget calculations
    $: totalBudgetNumber = parseFloat(total_budget) || 0;
    $: totalAllocated = budgetCategories.reduce((sum, cat) => sum + (parseFloat(cat.allocated) || 0), 0);
    $: budgetBalance = totalBudgetNumber - totalAllocated;
    $: isBudgetBalanced = Math.abs(budgetBalance) <= 0.01;
    
    // Auto-calculate MWK Value
    $: {
      if (totalBudgetNumber && usdToMwkRate) {
        mwkValue.set(totalBudgetNumber * usdToMwkRate);
      } else {
        mwkValue.set(0);
      }
    }

    // Step 3: Budget Categories
    let budgetCategories = [...DEFAULT_CATEGORIES];

    // Step 4: Compliance
    let financialReportingFrequency = 'quarterly';
    let progressReportingFrequency = 'biannual';
    
    // Ethics Compliance
    let ethicsRequired = false;
    let ethicsApprovalNumber = '';
    let ethicsExpiryDate = '';
    
    let milestones = [];
    let specialRequirements = '';
    let reportingTemplateFile = null;
    
    // Rule profile variables
    let selectedRuleProfile = null;
    let ruleGuidanceHighlights = [];
    
    // Milestone KPI allocation state
    let showMilestoneKPIAllocation = false;
    let selectedMilestoneIndex = null;

    // Step 5: Documents
    let agreement_file = null;
    let budgetBreakdownFile = null;
    let awardLetterFile = null;
    let ethicalApprovalFile = null;

    // Step 6: Team Members
    let teamMembers = [];

    // Disbursement Model (New)
    let disbursementType = 'single';
    let manualTranches = [
      { amount: '', expectedDate: '', status: 'pending' }
    ];

    // Step 7: Impact Framework (KPI Definition)
    let grantKPIs = [];
    let showAddKPI = false;
    let newKPI = {
        name: '',
        description: '',
        unit: 'count',
        category: 'research',
        grant_wide_target: '',
        baseline_value: '0'
    };

    // KPI Templates for quick setup
    const KPI_TEMPLATES = [
        { name: 'Publications', description: 'Research papers published in peer-reviewed journals', unit: 'papers', category: 'research', target: 5 },
        { name: 'Students Trained', description: 'Graduate students supervised and trained', unit: 'students', category: 'training', target: 3 },
        { name: 'Workshops Conducted', description: 'Training workshops and seminars delivered', unit: 'sessions', category: 'training', target: 2 },
        { name: 'Equipment Procured', description: 'Research equipment and instruments purchased', unit: 'items', category: 'infrastructure', target: 3 },
        { name: 'Beneficiaries Reached', description: 'People directly impacted by the project', unit: 'people', category: 'community', target: 100 },
        { name: 'Policy Briefs', description: 'Policy briefs submitted to government', unit: 'briefs', category: 'research', target: 2 },
        { name: 'Data Sets', description: 'Research data sets created and shared', unit: 'datasets', category: 'research', target: 5 },
        { name: 'Partnerships Formed', description: 'Strategic partnerships established', unit: 'partnerships', category: 'community', target: 3 }
    ];

    // KPI Management Functions
    function addKPI() {
      grantKPIs = [...grantKPIs, { ...newKPI }];
      newKPI = {
        name: '',
        description: '',
        unit: 'count',
        category: 'research',
        grant_wide_target: '',
        baseline_value: '0'
      };
      showAddKPI = false;
      markInteracted();
    }

    function removeKPI(index) {
      grantKPIs = grantKPIs.filter((_, i) => i !== index);
      markInteracted();
    }

    function updateKPI(index, key, value) {
      grantKPIs = grantKPIs.map((kpi, i) =>
        i === index ? { ...kpi, [key]: value } : kpi
      );
      markInteracted();
    }

    function applyTemplate(template) {
      newKPI = {
        name: template.name,
        description: template.description,
        unit: template.unit,
        category: template.category,
        grant_wide_target: template.target.toString(),
        baseline_value: '0'
      };
      markInteracted();
    }

    function applyCategoryTemplate(category) {
      const categoryTemplates = KPI_TEMPLATES.filter(t => t.category === category);
      categoryTemplates.forEach(template => {
        grantKPIs = [...grantKPIs, {
          name: template.name,
          description: template.description,
          unit: template.unit,
          category: template.category,
          grant_wide_target: template.target.toString(),
          baseline_value: '0'
        }];
      });
      markInteracted();
    }

    // Milestone KPI Allocation Functions
    function openMilestoneKPIAllocation(index) {
      selectedMilestoneIndex = index;
      showMilestoneKPIAllocation = true;
      
      // Initialize KPI allocations for this milestone if not already done
      if (!milestones[index].kpiAllocations) {
        milestones[index].kpiAllocations = grantKPIs.map(kpi => ({
          grantKpiId: kpi.id || Math.random().toString(36).substr(2, 9), // Temporary ID
          kpiName: kpi.name,
          kpiUnit: kpi.unit,
          milestoneTarget: '',
          allocationPercentage: 0
        }));
      }
    }

    function closeMilestoneKPIAllocation() {
      showMilestoneKPIAllocation = false;
      selectedMilestoneIndex = null;
    }

    function updateMilestoneKPI(milestoneIndex, kpiIndex, field, value) {
      milestones[milestoneIndex].kpiAllocations[kpiIndex][field] = value;
      
      // Auto-calculate allocation percentage if milestone target is set
      if (field === 'milestoneTarget' && value) {
        const grantKPI = grantKPIs.find(k => k.name === milestones[milestoneIndex].kpiAllocations[kpiIndex].kpiName);
        if (grantKPI && grantKPI.grant_wide_target) {
          const allocationPct = (parseFloat(value) / parseFloat(grantKPI.grant_wide_target)) * 100;
          milestones[milestoneIndex].kpiAllocations[kpiIndex].allocationPercentage = allocationPct;
        }
      }
      
      milestones = milestones; // Trigger reactivity
    }

    function autoDistributeKPIs(milestoneIndex) {
      const milestone = milestones[milestoneIndex];
      const totalMilestones = milestones.filter(m => m.title && m.dueDate).length;
      
      milestone.kpiAllocations.forEach((allocation, kpiIndex) => {
        const grantKPI = grantKPIs.find(k => k.name === allocation.kpiName);
        if (grantKPI && grantKPI.grant_wide_target) {
          // Equal distribution across all milestones
          const targetPerMilestone = parseFloat(grantKPI.grant_wide_target) / totalMilestones;
          allocation.milestoneTarget = targetPerMilestone.toFixed(2);
          allocation.allocationPercentage = (1 / totalMilestones) * 100;
        }
      });
      
      milestones = milestones; // Trigger reactivity
    }

    function initializeMilestoneKPIs(milestoneIndex) {
      // Initialize KPI allocations for this milestone if not already done
      if (!milestones[milestoneIndex].kpiAllocations || milestones[milestoneIndex].kpiAllocations.length === 0) {
        milestones[milestoneIndex].kpiAllocations = grantKPIs.map(kpi => ({
          grantKpiId: kpi.id || Math.random().toString(36).substr(2, 9), // Temporary ID
          kpiName: kpi.name,
          kpiUnit: kpi.unit,
          milestoneTarget: '',
          allocationPercentage: 0,
          notes: ''
        }));
      }
      milestones = milestones; // Trigger reactivity
    }

    function removeMilestoneKPI(milestoneIndex, kpiIndex) {
      if (milestones[milestoneIndex].kpiAllocations) {
        milestones[milestoneIndex].kpiAllocations = milestones[milestoneIndex].kpiAllocations.filter((_, i) => i !== kpiIndex);
        milestones = milestones; // Trigger reactivity
      }
    }

    // Step 8: Review & Submit
    $: if ($user) {
      principalInvestigator = $user.name || '';
    }
    
    $: projectDuration = calculateDuration(start_date, end_date);

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

    // Disbursement Helpers
    function addTranche() {
      manualTranches = [...manualTranches, { amount: '', expectedDate: '', status: 'pending' }];
      markInteracted();
    }

    function removeTranche(index) {
      if (manualTranches.length === 1) return;
      manualTranches = manualTranches.filter((_, i) => i !== index);
      markInteracted();
    }

    function updateTranche(index, key, value) {
      manualTranches = manualTranches.map((t, i) => 
        i === index ? { ...t, [key]: value } : t
      );
      markInteracted();
    }

    function markInteracted() {
      if (!hasInteracted) hasInteracted = true;
      validateForm();
    }

    async function handleFunderChange() {
      markInteracted();
      
      if (!funder || funder === 'other') {
        selectedRuleProfile = null;
        ruleGuidanceHighlights = [];
        return;
      }

      const profile = funderProfiles.find(p => p.id.toString() === funder.toString());
      if (profile) {
        selectedRuleProfile = profile;
        // Extract active limits and guidance
        ruleGuidanceHighlights = (profile.rules || [])
          .filter(r => r.is_active && r.guidance_text)
          .map(r => ({ text: r.guidance_text, outcome: r.outcome }));
      } else {
        selectedRuleProfile = null;
        ruleGuidanceHighlights = [];
      }
      
      reportingTemplateFile = null;
    }

    function nextStep() {
      if (validateCurrentStep()) {
        currentStep = Math.min(currentStep + 1, 8);
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

    function validateCurrentStep(step = currentStep) {
      // Don't clear validationErrors here if we are checking all steps via validateForm
      const stepErrors = {};
      
      switch(step) {
        case 1: // Basic Info
          if (!title.trim()) stepErrors.title = 'Grant Title is required';
          if (!funder) stepErrors.funder = 'Funder is required';
          if (funder === 'other' && !funderOther.trim()) {
            stepErrors.funderOther = 'Please specify the funder';
          }
          if (!grant_code.trim()) stepErrors.grant_code = 'Grant Code is required';
          if (!funderReferenceNumber.trim()) {
            stepErrors.funderReferenceNumber = 'Funder Reference Number is required';
          }
          if (!start_date) stepErrors.start_date = 'Start Date is required';
          if (!end_date) stepErrors.end_date = 'End Date is required';
          
          if (start_date && end_date) {
            const start = new Date(start_date);
            const end = new Date(end_date);
            if (end <= start) {
              stepErrors.end_date = 'End date must be after start date';
            }
          }
          break;
          
        case 2: // Financial Details
          if (!total_budget || parseFloat(total_budget) <= 0) {
            stepErrors.total_budget = 'Total Budget must be greater than 0';
          }
          if (!usdToMwkRate || parseFloat(usdToMwkRate) <= 0) {
            stepErrors.usdToMwkRate = 'Exchange rate must be greater than 0';
          }
          break;
          
        case 3: // Budget Categories
          if (budgetCategories.length === 0) {
            stepErrors.budgetCategories = 'At least one budget category is required';
          } else {
            budgetCategories.forEach((cat, i) => {
              if (!cat.name.trim()) {
                stepErrors[`category_${i}_name`] = 'Category name is required';
              }
              if (!cat.allocated || parseFloat(cat.allocated) < 0) {
                stepErrors[`category_${i}_allocated`] = 'Valid allocated amount is required';
              }
            });
          }
          
          if (total_budget && budgetCategories.length > 0) {
            if (!isBudgetBalanced) {
              stepErrors.budgetSum = 'Budget allocations must equal total budget';
            }
          }
          break;
          
        case 4: // Compliance
          // Ethics details no longer required during initialization (handled by RSU meeting)
          break;

          milestones.forEach((milestone, i) => {
            // Validate if any field is filled
            if (milestone.title || milestone.dueDate || milestone.reportingPeriod || milestone.description) {
              if (!milestone.title || !milestone.title.trim()) {
                stepErrors[`milestone_${i}_title`] = 'Milestone title is required';
              }
              if (!milestone.dueDate) {
                stepErrors[`milestone_${i}_dueDate`] = 'Due date is required';
              }
              if (disbursementType === 'milestone_based') {
                if (!milestone.fundingAmount || parseFloat(milestone.fundingAmount) <= 0) {
                  stepErrors[`milestone_${i}_fundingAmount`] = 'Funding amount is required';
                }
              }
            }
          });

          if (disbursementType === 'milestone_based') {
             const totalMilestoneFunding = milestones.reduce((sum, m) => sum + (parseFloat(m.fundingAmount) || 0), 0);
             if (Math.abs(totalMilestoneFunding - totalBudgetNumber) > 0.01) {
               stepErrors.milestoneFundingSum = 'Total milestone funding must equal grant budget';
             }
          }

          if (disbursementType === 'tranches') {
            manualTranches.forEach((tranche, i) => {
              if (!tranche.amount || parseFloat(tranche.amount) <= 0) {
                stepErrors[`tranche_${i}_amount`] = 'Tranche amount is required';
              }
              if (!tranche.expectedDate) {
                stepErrors[`tranche_${i}_expectedDate`] = 'Expected date is required';
              }
            });
            const totalTrancheFunding = manualTranches.reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0);
            if (Math.abs(totalTrancheFunding - total_budget) > 0.01) {
              stepErrors.trancheFundingSum = 'Total tranche funding must equal grant budget';
            }
          }
          break;
          
        case 5: // Documents
          if (!agreement_file) {
            stepErrors.agreement = 'Grant Agreement PDF is required';
          }
          if (!budgetBreakdownFile) {
            stepErrors.budgetBreakdown = 'Budget Breakdown is required';
          }
          if (!awardLetterFile) {
            stepErrors.awardLetter = 'Award Letter is required';
          }
          break;
          
        case 6: // Team Members
          teamMembers.forEach((member, i) => {
            if (member.name || member.email || member.role || member.dailyRate) {
              if (!member.name.trim()) {
                stepErrors[`team_${i}_name`] = 'Team member name is required';
              }
              if (!member.email.trim()) {
                stepErrors[`team_${i}_email`] = 'Team member email is required';
              } else if (!member.email.includes('@mubas.ac.mw')) {
                stepErrors[`team_${i}_email`] = 'Email must be a MUBAS domain';
              }
            }
          });
          break;
          
        case 7: // Impact Framework (KPI Definition)
          if (grantKPIs.length === 0) {
            stepErrors.grantKPIs = 'At least one KPI is required for grant tracking';
          } else {
            grantKPIs.forEach((kpi, i) => {
              if (!kpi.name.trim()) {
                stepErrors[`kpi_${i}_name`] = 'KPI name is required';
              }
              if (!kpi.grant_wide_target || parseFloat(kpi.grant_wide_target) <= 0) {
                stepErrors[`kpi_${i}_target`] = 'Grant-wide target must be greater than 0';
              }
              if (!kpi.unit) {
                stepErrors[`kpi_${i}_unit`] = 'Unit is required';
              }
            });
          }
          break;
      }
      
      // Update global validationErrors for the current step
      if (step === currentStep) {
        validationErrors = stepErrors;
      }
      
      return Object.keys(stepErrors).length === 0;
    }

    const fieldError = (key) => (hasInteracted ? validationErrors[key] : null);
  
    function validateForm() {
      // Run validation for all steps without modifying currentStep UI state
      let allValid = true;
      let newValidationErrors = {};
      
      for (let i = 1; i <= 7; i++) {
        // We need a version of validateCurrentStep that doesn't touch global validationErrors
        // or we just call it and it updates it. Since validateForm is called only at the end
        // or on interaction, we should be careful.
        if (!validateCurrentStep(i)) {
          allValid = false;
          // Note: validateCurrentStep(currentStep) will have updated the global validationErrors
          // for the UI. If the error is in a different step, it won't be shown yet.
          break;
        }
      }
      
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
        formData.append('funder_id', funder);
        if (funder === 'other') {
            formData.append('funder_name_other', funderOther.trim());
        }
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
        
        // Add Ethics Fields
        formData.append('ethics_required', ethicsRequired);
        formData.append('ethics_approval_number', ethicsApprovalNumber);
        formData.append('ethics_expiry_date', ethicsExpiryDate);
        
        formData.append('disbursement_type', disbursementType);
        
        if (disbursementType === 'tranches') {
          formData.append('manual_tranches', JSON.stringify(manualTranches));
        }
        
        if (selectedRuleProfile) {
          formData.append('rule_profile_id', selectedRuleProfile.id);
        }
        
        // Add milestones
        if (milestones.length > 0) {
          const milestonesData = milestones
            .filter(m => m.title && m.dueDate)
            .map(m => ({
              title: m.title.trim(),
              description: m.description.trim(),
              due_date: m.dueDate,
              reporting_period: m.reportingPeriod,
              funding_amount: parseFloat(m.fundingAmount || 0),
              status: m.status,
              kpi_allocations: m.kpiAllocations || []
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
        if (reportingTemplateFile) formData.append('reporting_template', reportingTemplateFile);

        // Add KPI data
        if (grantKPIs.length > 0) {
          formData.append('grant_kpis', JSON.stringify(
            grantKPIs.map(kpi => ({
              name: kpi.name.trim(),
              description: kpi.description.trim(),
              unit: kpi.unit,
              category: kpi.category,
              grant_wide_target: parseFloat(kpi.grant_wide_target),
              baseline_value: parseFloat(kpi.baseline_value || 0)
            }))
          ));
        }

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
        case 'reportingTemplate':
          reportingTemplateFile = file;
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
        case 'reportingTemplate':
          reportingTemplateFile = null;
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
            {#each Array(8) as _, i}
              {@const stepNum = i + 1}
              {@const isCompleted = stepNum < currentStep}
              {@const isActive = stepNum === currentStep}
              {@const isPending = stepNum > currentStep}
              
              <div class="flex flex-col items-center flex-1 relative">
                {#if i < 7}
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
                  {['Basic Info', 'Financial', 'Budget', 'Compliance', 'Documents', 'Team', 'KPIs', 'Review'][i]}
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
                  on:change={handleFunderChange}
                >
                  <option value="">Select Funder</option>
                  {#each funderProfiles as profile}
                    <option value={profile.id}>{profile.name}</option>
                  {/each}
                  <option value="other">Other</option>
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
            
            <!-- Dynamic Rule Guidance -->
            {#if selectedRuleProfile && ruleGuidanceHighlights.length > 0}
              <div class="mb-8 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6 shadow-sm">
                <h3 class="flex items-center gap-2 text-blue-900 font-bold mb-3">
                  <Icon name="compliance" size={24} /> {selectedRuleProfile.name} Compliance Guidelines
                </h3>
                <p class="text-sm text-blue-800 mb-4">The following rules will be actively enforced for all expenses submitted under this grant:</p>
                <ul class="space-y-3">
                  {#each ruleGuidanceHighlights as guidance}
                    <li class="flex items-start gap-3 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm">
                      <span class="mt-0.5">
                        <Icon 
                          name={guidance.outcome === 'BLOCK' ? 'statusCritical' : guidance.outcome === 'PRIOR_APPROVAL' ? 'statusWarn' : 'info'} 
                          size={18} 
                          className={guidance.outcome === 'BLOCK' ? 'text-red-500' : guidance.outcome === 'PRIOR_APPROVAL' ? 'text-amber-500' : 'text-blue-500'}
                        />
                      </span>
                      <span class="text-sm text-gray-800 font-medium">{guidance.text}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}

            <!-- Ethics Declaration (New) -->
            <div class="mb-8 p-6 bg-amber-50 border border-amber-200 rounded-2xl">
              <h3 class="text-lg font-semibold text-amber-900 mb-4 flex items-center gap-2">
                <span class="text-xl">⚖️</span> Ethics & Compliance Declaration
              </h3>
              
              <div class="space-y-4">
                <p class="text-sm text-amber-800 leading-relaxed">
                  Does this research project involve any of the following: <strong>Human Subjects</strong>, 
                  <strong>Animal Research</strong>, or <strong>Hazardous Materials</strong>?
                </p>
                
                <div class="flex flex-col gap-3">
                  <label class="flex items-center gap-3 px-4 py-3 bg-white border border-amber-200 rounded-xl cursor-pointer hover:bg-amber-100 transition-colors shadow-sm">
                    <input type="radio" value={false} bind:group={ethicsRequired} on:change={markInteracted} class="w-4 h-4 text-amber-600 focus:ring-amber-500" />
                    <div class="flex flex-col">
                      <span class="text-sm font-bold text-amber-900">No, no REC needed</span>
                      <span class="text-xs text-amber-700">Project does not involve human subjects, animals, or hazardous materials.</span>
                    </div>
                  </label>
                  <label class="flex items-center gap-3 px-4 py-3 bg-white border border-amber-200 rounded-xl cursor-pointer hover:bg-amber-100 transition-colors shadow-sm">
                    <input type="radio" value={true} bind:group={ethicsRequired} on:change={markInteracted} class="w-4 h-4 text-amber-600 focus:ring-amber-500" />
                    <div class="flex flex-col">
                      <span class="text-sm font-bold text-amber-900">Yes, involves human/animal subjects or hazardous materials</span>
                      <span class="text-xs text-amber-700">An REC Meeting will be scheduled by the RSU to review and approve the project ethics.</span>
                    </div>
                  </label>
                </div>
                
                {#if ethicsRequired}
                  <div class="mt-4 p-4 bg-amber-100/50 border border-amber-200 rounded-xl flex items-start gap-3">
                    <div class="p-2 bg-amber-200 rounded-lg text-amber-700">
                      <Icon name="info" size={18} />
                    </div>
                    <div class="text-xs text-amber-800 leading-relaxed">
                      <strong>Important:</strong> Your grant will be created with <strong>PENDING_ETHICS</strong> status. 
                      All financial and task modules will be locked until the RSU conducts an REC meeting and verifies the compliance requirements.
                    </div>
                  </div>
                {/if}
              </div>
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

              <!-- Funder Reporting Template Upload -->
              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Funder Reporting Template (Optional)
                </label>
                
                {#if selectedRuleProfile?.reporting_template_filename && !reportingTemplateFile}
                  <div class="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="p-2 bg-emerald-100 rounded-lg text-emerald-600">
                        <Icon name="document" size={20} />
                      </div>
                      <div>
                        <p class="text-sm font-medium text-emerald-900">System Template Detected</p>
                        <p class="text-xs text-emerald-700">{selectedRuleProfile.reporting_template_filename}</p>
                      </div>
                    </div>
                    <label class="px-4 py-2 bg-white border border-emerald-200 text-emerald-700 rounded-lg hover:bg-emerald-50 text-xs font-medium cursor-pointer transition-colors">
                      Upload Different Version
                      <input 
                        type="file" 
                        class="hidden" 
                        accept=".pdf,.doc,.docx"
                        on:change={(e) => handleFileChange('reportingTemplate', e)}
                      />
                    </label>
                  </div>
                {:else}
                  <div class="flex items-center justify-center w-full">
                    <label class="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-xl cursor-pointer bg-gray-50 hover:bg-blue-50 hover:border-blue-300 transition-colors">
                      <div class="flex flex-col items-center justify-center pt-5 pb-6">
                        <Icon name="document" size={32} className="mb-2 text-gray-400" />
                        <p class="mb-2 text-sm text-gray-500">
                          <span class="font-semibold text-blue-600">Click to upload</span> or drag and drop
                        </p>
                        <p class="text-xs text-gray-400">Word or PDF (MAX. 10MB)</p>
                        {#if reportingTemplateFile}
                          <p class="mt-2 text-sm font-medium text-emerald-600 truncate max-w-[250px]">
                            ✓ {reportingTemplateFile.name}
                          </p>
                        {/if}
                      </div>
                      <input 
                        type="file" 
                        class="hidden" 
                        accept=".pdf,.doc,.docx"
                        on:change={(e) => handleFileChange('reportingTemplate', e)}
                      />
                    </label>
                  </div>
                {/if}
              </div>
            </div>

            <!-- Disbursement Model Selection (New) -->
            <div class="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-2xl">
              <h3 class="text-lg font-semibold text-blue-900 mb-4 flex items-center gap-2">
                <span class="text-xl">💰</span> Disbursement & Funding Model
              </h3>
              
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <!-- Single Payment -->
                <label class="relative flex flex-col p-4 bg-white border {disbursementType === 'single' ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'} rounded-xl cursor-pointer hover:border-blue-300 transition-all">
                  <input type="radio" name="disbursementType" value="single" class="sr-only" bind:group={disbursementType} />
                  <span class="text-sm font-bold text-gray-900 mb-1">Single Payment</span>
                  <span class="text-xs text-gray-500">Full amount received at once upon project start.</span>
                  {#if disbursementType === 'single'}
                    <div class="absolute top-2 right-2 text-blue-600 font-bold text-lg">✓</div>
                  {/if}
                </label>

                <!-- Tranches -->
                <label class="relative flex flex-col p-4 bg-white border {disbursementType === 'tranches' ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'} rounded-xl cursor-pointer hover:border-blue-300 transition-all">
                  <input type="radio" name="disbursementType" value="tranches" class="sr-only" bind:group={disbursementType} />
                  <span class="text-sm font-bold text-gray-900 mb-1">Tranches</span>
                  <span class="text-xs text-gray-500">Manual installments defined by expected dates.</span>
                  {#if disbursementType === 'tranches'}
                    <div class="absolute top-2 right-2 text-blue-600 font-bold text-lg">✓</div>
                  {/if}
                </label>

                <!-- Milestone Based -->
                <label class="relative flex flex-col p-4 bg-white border {disbursementType === 'milestone_based' ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'} rounded-xl cursor-pointer hover:border-blue-300 transition-all">
                  <input type="radio" name="disbursementType" value="milestone_based" class="sr-only" bind:group={disbursementType} />
                  <span class="text-sm font-bold text-gray-900 mb-1">Milestone-based</span>
                  <span class="text-xs text-gray-500">Funding released upon completion of specific milestones.</span>
                  {#if disbursementType === 'milestone_based'}
                    <div class="absolute top-2 right-2 text-blue-600 font-bold text-lg">✓</div>
                  {/if}
                </label>
              </div>

              {#if disbursementType === 'tranches'}
                <div class="space-y-4">
                  <div class="flex justify-between items-center">
                    <h4 class="text-sm font-bold text-blue-900 uppercase tracking-wider">Payment Schedule Configuration</h4>
                    <button type="button" on:click={addTranche} class="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1">
                      <Icon name="plus" size={14} />
                      Add Installment
                    </button>
                  </div>
                  
                  {#each manualTranches as tranche, i}
                    <div class="bg-white p-4 rounded-xl border border-blue-100 shadow-sm">
                      <!-- Header -->
                      <div class="flex justify-between items-center mb-4">
                        <h5 class="text-sm font-bold text-gray-900 flex items-center gap-2">
                          <Icon name="money" size={16} class="text-blue-600" />
                          Installment {i + 1}
                        </h5>
                        <button type="button" on:click={() => removeTranche(i)} class="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors" disabled={manualTranches.length === 1}>
                          <Icon name="trash" size={18} />
                        </button>
                      </div>
                      
                      <!-- Basic Info Grid -->
                      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div>
                          <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Description</label>
                          <input 
                             type="text" 
                             class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 transition-all"
                             placeholder="e.g., Initial Mobilization"
                             value={tranche.description || ''}
                             on:input={(e) => updateTranche(i, 'description', e.target.value)}
                          />
                        </div>
                        <div>
                          <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Amount (USD)</label>
                          <input 
                             type="number" 
                             class="w-full px-3 py-2 border {fieldError(`tranche_${i}_amount`) ? 'border-red-500' : 'border-gray-200'} rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 transition-all"
                             placeholder="0.00"
                             value={tranche.amount}
                             on:input={(e) => updateTranche(i, 'amount', e.target.value)}
                          />
                        </div>
                        <div>
                          <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Expected Date</label>
                          <input 
                             type="date" 
                             class="w-full px-3 py-2 border {fieldError(`tranche_${i}_expectedDate`) ? 'border-red-500' : 'border-gray-200'} rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 transition-all"
                             value={tranche.expectedDate}
                             on:input={(e) => updateTranche(i, 'expectedDate', e.target.value)}
                          />
                        </div>
                      </div>
                      
                      <!-- NEW: Trigger Configuration -->
                      <div class="border-t border-gray-100 pt-4">
                        <div class="flex items-center gap-2 mb-3">
                          <Icon name="setting" size={16} class="text-gray-600" />
                          <label class="text-sm font-bold text-gray-900">Release Trigger</label>
                        </div>
                        
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                          <!-- Trigger Type -->
                          <div>
                            <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Trigger Type</label>
                            <select 
                              class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 transition-all"
                              value={tranche.trigger_type || 'milestone'}
                              on:change={(e) => updateTranche(i, 'trigger_type', e.target.value)}
                            >
                              <option value="milestone">Milestone Completion</option>
                              <option value="report">Report Submission</option>
                              <option value="date">Specific Date</option>
                              <option value="manual">Manual Release</option>
                            </select>
                          </div>
                          
                          <!-- Conditional Trigger Fields -->
                          {#if tranche.trigger_type === 'milestone'}
                            <div class="md:col-span-3">
                              <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Required Milestone</label>
                              <select 
                                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 transition-all"
                                value={tranche.triggering_milestone_id || ''}
                                on:change={(e) => updateTranche(i, 'triggering_milestone_id', e.target.value)}
                              >
                                <option value="">Select milestone...</option>
                                {#each milestones as milestone}
                                  <option value={milestone.id}>{milestone.title}</option>
                                {/each}
                              </select>
                            </div>
                          {:else if tranche.trigger_type === 'report'}
                            <div class="md:col-span-3">
                              <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Required Report Type</label>
                              <select 
                                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 transition-all"
                                value={tranche.required_report_type || ''}
                                on:change={(e) => updateTranche(i, 'required_report_type', e.target.value)}
                              >
                                <option value="">Select report type...</option>
                                <option value="financial">Financial Report</option>
                                <option value="progress">Progress Report</option>
                                <option value="technical">Technical Report</option>
                              </select>
                            </div>
                          {:else if tranche.trigger_type === 'date'}
                            <div class="md:col-span-3">
                              <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Release Date</label>
                              <input 
                                type="date" 
                                class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-200 transition-all"
                                value={tranche.trigger_date || ''}
                                on:input={(e) => updateTranche(i, 'trigger_date', e.target.value)}
                              />
                            </div>
                          {:else if tranche.trigger_type === 'manual'}
                            <div class="md:col-span-3">
                              <div class="p-3 bg-gray-50 rounded-lg border border-gray-200">
                                <p class="text-sm text-gray-600 flex items-center gap-2">
                                  <Icon name="setting" size={16} />
                                  This tranche will be released manually by RSU/Finance staff
                                </p>
                              </div>
                            </div>
                          {/if}
                        </div>
                      </div>
                    </div>
                  {/each}
                  
                  {#if fieldError('trancheFundingSum')}
                    <p class="text-xs text-red-600 font-bold">{fieldError('trancheFundingSum')}</p>
                  {/if}
                  
                  <div class="flex justify-between items-center p-3 bg-blue-100/50 rounded-lg">
                    <span class="text-xs font-bold text-blue-800">Total Scheduled:</span>
                    <span class="text-sm font-bold text-blue-900">
                      ${manualTranches.reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0).toLocaleString()} 
                      / ${totalBudgetNumber.toLocaleString()}
                    </span>
                  </div>
                </div>
              {/if}

              {#if disbursementType === 'single'}
                <div class="p-4 bg-white rounded-xl border border-blue-100 shadow-sm">
                  <p class="text-sm text-gray-700">
                    The full amount of <span class="font-bold text-blue-600">${totalBudgetNumber.toLocaleString()}</span> will be released in a single installment.
                  </p>
                </div>
              {/if}
              
              {#if disbursementType === 'milestone_based'}
                <div class="p-4 bg-white rounded-xl border border-blue-100 shadow-sm">
                  <p class="text-sm text-gray-700 mb-1">
                    You've selected milestone-based release. <span class="font-bold">Next Step:</span> Assign a funding amount to each milestone below.
                  </p>
                  {#if fieldError('milestoneFundingSum')}
                    <p class="text-xs text-red-600 font-bold">{fieldError('milestoneFundingSum')}</p>
                  {/if}
                  <div class="flex justify-between items-center p-2 bg-blue-50 rounded-lg mt-2">
                    <span class="text-xs font-bold text-blue-800">Total Assigned:</span>
                    <span class="text-sm font-bold text-blue-900">
                      ${milestones.reduce((sum, m) => sum + (parseFloat(m.fundingAmount) || 0), 0).toLocaleString()} 
                      / ${totalBudgetNumber.toLocaleString()}
                    </span>
                  </div>
                </div>
              {/if}
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
                        <div class="flex gap-2">
                          {#if grantKPIs.length > 0}
                            <button
                              type="button"
                              on:click={() => openMilestoneKPIAllocation(i)}
                              class="px-3 py-1 bg-purple-100 text-purple-700 rounded hover:bg-purple-200 text-xs font-medium transition-colors"
                            >
                              📊 Allocate KPIs
                            </button>
                          {/if}
                          <button
                            type="button"
                            on:click={() => removeMilestone(i)}
                            class="text-red-600 hover:text-red-700 text-sm font-medium"
                          >
                            Remove
                          </button>
                        </div>
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

                        {#if disbursementType === 'milestone_based'}
                          <div>
                            <label class="block text-xs font-medium text-gray-700 mb-1">
                              Funding Amount (USD) <span class="text-red-500">*</span>
                            </label>
                            <div class="relative">
                              <span class="absolute left-3 top-2 text-gray-500 font-medium">$</span>
                              <input
                                type="number"
                                placeholder="0.00"
                                class="w-full pl-7 pr-3 py-2 border {fieldError(`milestone_${i}_fundingAmount`) ? 'border-red-500' : 'border-gray-300'} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={milestone.fundingAmount}
                                on:input={(e) => updateMilestone(i, 'fundingAmount', e.target.value)}
                              />
                            </div>
                            {#if fieldError(`milestone_${i}_fundingAmount`)}
                              <p class="mt-1 text-xs text-red-600">{fieldError(`milestone_${i}_fundingAmount`)}</p>
                            {/if}
                          </div>
                        {/if}

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

                        <!-- Milestone KPIs -->
                        <div class="md:col-span-2">
                          <div class="flex justify-between items-center mb-3">
                            <label class="block text-xs font-medium text-gray-700">
                              Milestone KPIs & Deliverables
                            </label>
                            {#if grantKPIs.length > 0}
                              <button
                                type="button"
                                on:click={() => initializeMilestoneKPIs(i)}
                                class="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-xs font-medium transition-colors"
                              >
                                📊 Auto-Add Grant KPIs
                              </button>
                            {/if}
                          </div>
                          
                          {#if grantKPIs.length === 0}
                            <div class="p-3 bg-amber-50 border border-amber-200 rounded-md text-xs text-amber-800">
                              ⚠️ Define grant KPIs in Step 7 first, then add them to milestones here
                            </div>
                          {:else}
                            <!-- Milestone-specific KPIs -->
                            <div class="space-y-3">
                              {#each (milestone.kpiAllocations || []) as allocation, kpiIndex}
                                <div class="p-3 bg-white border border-gray-200 rounded-md">
                                  <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    <div class="md:col-span-1">
                                      <label class="block text-xs font-medium text-gray-700 mb-1">KPI</label>
                                      <div class="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-xs font-medium">
                                        {allocation.kpiName}
                                        <span class="text-gray-500 ml-1">({allocation.kpiUnit})</span>
                                      </div>
                                    </div>
                                    <div>
                                      <label class="block text-xs font-medium text-gray-700 mb-1">Target</label>
                                      <input
                                        type="number"
                                        placeholder="0"
                                        step="0.01"
                                        class="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                                        value={allocation.milestoneTarget}
                                        on:input={(e) => updateMilestoneKPI(i, kpiIndex, 'milestoneTarget', e.target.value)}
                                      />
                                    </div>
                                    <div>
                                      <label class="block text-xs font-medium text-gray-700 mb-1">Deliverable Details</label>
                                      <textarea
                                        rows="1"
                                        placeholder="What will be delivered/achieved..."
                                        class="w-full px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                                        value={allocation.notes || ''}
                                        on:input={(e) => updateMilestoneKPI(i, kpiIndex, 'notes', e.target.value)}
                                      ></textarea>
                                    </div>
                                  </div>
                                  <div class="mt-2 flex justify-between items-center">
                                    <div class="text-xs text-gray-500">
                                      {#if allocation.milestoneTarget && grantKPIs.find(k => k.name === allocation.kpiName)?.grant_wide_target}
                                        {((parseFloat(allocation.milestoneTarget) / parseFloat(grantKPIs.find(k => k.name === allocation.kpiName).grant_wide_target)) * 100).toFixed(1)}% of grant target
                                      {/if}
                                    </div>
                                    <button
                                      type="button"
                                      on:click={() => removeMilestoneKPI(i, kpiIndex)}
                                      class="text-red-600 hover:text-red-700 text-xs font-medium"
                                    >
                                      Remove
                                    </button>
                                  </div>
                                </div>
                              {/each}
                              
                              {#if (milestone.kpiAllocations || []).length === 0}
                                <div class="p-4 border-2 border-dashed border-gray-300 rounded-md text-center text-gray-500">
                                  <p class="text-xs">No KPIs assigned to this milestone.</p>
                                  <p class="text-xs text-gray-400 mt-1">Click "Auto-Add Grant KPIs" to get started</p>
                                </div>
                              {/if}
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

            {#if hasInteracted && Object.keys(validationErrors).length > 0 && currentStep === 4}
              <div class="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
                <p class="text-sm text-red-700 font-medium">Please correct the errors above in the compliance section before proceeding.</p>
              </div>
            {/if}
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

        <!-- Step 7: Impact Framework (KPI Definition) -->
        {#if currentStep === 7}
          <div class="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl shadow-lg p-8">
            <div class="border-l-4 border-blue-600 pl-4 mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Impact Framework (KPI Definition)</h2>
              <p class="text-sm text-gray-600 mt-1">Define Key Performance Indicators that will measure grant success and impact throughout the project lifecycle.</p>
            </div>

            <!-- Quick Templates -->
            <div class="mb-6">
              <h3 class="text-lg font-semibold text-gray-800 mb-3">🚀 Quick Setup Templates</h3>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button 
                  type="button"
                  on:click={() => applyCategoryTemplate('research')}
                  class="px-3 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 text-sm font-medium transition-colors"
                >
                  📊 Research Metrics
                </button>
                <button 
                  type="button"
                  on:click={() => applyCategoryTemplate('training')}
                  class="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm font-medium transition-colors"
                >
                  👥 Training Metrics
                </button>
                <button 
                  type="button"
                  on:click={() => applyCategoryTemplate('infrastructure')}
                  class="px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm font-medium transition-colors"
                >
                  🏗️ Infrastructure
                </button>
                <button 
                  type="button"
                  on:click={() => applyCategoryTemplate('community')}
                  class="px-3 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 text-sm font-medium transition-colors"
                >
                  🌍 Community Impact
                </button>
              </div>
              <p class="text-xs text-gray-500 mt-2">Click to add pre-configured KPI sets for each category</p>
            </div>

            <!-- KPI List -->
            <div class="mb-6">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-gray-800">📋 Grant KPIs</h3>
                <span class="text-sm text-gray-600">{grantKPIs.length} KPI{grantKPIs.length !== 1 ? 's' : ''} defined</span>
              </div>

              {#if grantKPIs.length === 0}
                <div class="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
                  <span class="text-4xl mb-2 block">🎯</span>
                  <p class="text-gray-600 mb-2">No KPIs defined yet</p>
                  <p class="text-sm text-gray-500">Add your first KPI below or use quick templates above</p>
                </div>
              {:else}
                <div class="space-y-3">
                  {#each grantKPIs as kpi, i}
                    <div class="border border-gray-200 rounded-lg p-4 bg-white">
                      <div class="grid grid-cols-1 md:grid-cols-6 gap-4">
                        <div class="md:col-span-2">
                          <label class="block text-xs font-medium text-gray-700 mb-1">KPI Name *</label>
                          <input
                            type="text"
                            placeholder="e.g., Publications"
                            class="w-full px-3 py-2 border {fieldError(`kpi_${i}_name`) ? 'border-red-500' : 'border-gray-300'} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={kpi.name}
                            on:input={(e) => updateKPI(i, 'name', e.target.value)}
                          />
                          {#if fieldError(`kpi_${i}_name`)}
                            <p class="mt-1 text-xs text-red-600">{fieldError(`kpi_${i}_name`)}</p>
                          {/if}
                        </div>

                        <div>
                          <label class="block text-xs font-medium text-gray-700 mb-1">Unit *</label>
                          <select
                            class="w-full px-3 py-2 border {fieldError(`kpi_${i}_unit`) ? 'border-red-500' : 'border-gray-300'} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={kpi.unit}
                            on:change={(e) => updateKPI(i, 'unit', e.target.value)}
                          >
                            <option value="count">Count</option>
                            <option value="percentage">Percentage</option>
                            <option value="currency">Currency</option>
                            <option value="papers">Papers</option>
                            <option value="students">Students</option>
                            <option value="people">People</option>
                            <option value="items">Items</option>
                            <option value="sessions">Sessions</option>
                            <option value="datasets">Datasets</option>
                            <option value="briefs">Briefs</option>
                            <option value="partnerships">Partnerships</option>
                          </select>
                          {#if fieldError(`kpi_${i}_unit`)}
                            <p class="mt-1 text-xs text-red-600">{fieldError(`kpi_${i}_unit`)}</p>
                          {/if}
                        </div>

                        <div>
                          <label class="block text-xs font-medium text-gray-700 mb-1">Grant Target *</label>
                          <input
                            type="number"
                            placeholder="100"
                            min="0"
                            step="0.01"
                            class="w-full px-3 py-2 border {fieldError(`kpi_${i}_target`) ? 'border-red-500' : 'border-gray-300'} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={kpi.grant_wide_target}
                            on:input={(e) => updateKPI(i, 'grant_wide_target', e.target.value)}
                          />
                          {#if fieldError(`kpi_${i}_target`)}
                            <p class="mt-1 text-xs text-red-600">{fieldError(`kpi_${i}_target`)}</p>
                          {/if}
                        </div>

                        <div>
                          <label class="block text-xs font-medium text-gray-700 mb-1">Category</label>
                          <select
                            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={kpi.category}
                            on:change={(e) => updateKPI(i, 'category', e.target.value)}
                          >
                            <option value="research">Research</option>
                            <option value="training">Training</option>
                            <option value="infrastructure">Infrastructure</option>
                            <option value="community">Community</option>
                            <option value="financial">Financial</option>
                          </select>
                        </div>

                        <div>
                          <label class="block text-xs font-medium text-gray-700 mb-1">Baseline</label>
                          <input
                            type="number"
                            placeholder="0"
                            min="0"
                            step="0.01"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={kpi.baseline_value}
                            on:input={(e) => updateKPI(i, 'baseline_value', e.target.value)}
                          />
                        </div>
                      </div>

                      <div class="mt-3">
                        <label class="block text-xs font-medium text-gray-700 mb-1">Description</label>
                        <textarea
                          placeholder="Brief description of this KPI and how it will be measured"
                          class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows="2"
                          value={kpi.description}
                          on:input={(e) => updateKPI(i, 'description', e.target.value)}
                        ></textarea>
                      </div>

                      <div class="mt-3 flex justify-end">
                        <button
                          type="button"
                          on:click={() => removeKPI(i)}
                          class="px-3 py-1 bg-red-100 text-red-700 rounded-md hover:bg-red-200 text-sm font-medium"
                        >
                          Remove KPI
                        </button>
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}

              {#if fieldError('grantKPIs')}
                <p class="mt-2 text-sm text-red-600">{fieldError('grantKPIs')}</p>
              {/if}
            </div>

            <!-- Add New KPI -->
            <div class="border-t pt-6">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-gray-800">➕ Add New KPI</h3>
                <button
                  type="button"
                  on:click={() => showAddKPI = !showAddKPI}
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                >
                  {showAddKPI ? 'Cancel' : 'Add KPI'}
                </button>
              </div>

              {#if showAddKPI}
                <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Quick Templates</label>
                      <div class="grid grid-cols-2 gap-2">
                        {#each KPI_TEMPLATES.slice(0, 4) as template}
                          <button
                            type="button"
                            on:click={() => applyTemplate(template)}
                            class="px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-xs"
                          >
                            {template.name}
                          </button>
                        {/each}
                      </div>
                    </div>
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">KPI Name *</label>
                      <input
                        type="text"
                        placeholder="e.g., Publications"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        bind:value={newKPI.name}
                      />
                    </div>

                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Unit *</label>
                      <select
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        bind:value={newKPI.unit}
                      >
                        <option value="count">Count</option>
                        <option value="percentage">Percentage</option>
                        <option value="currency">Currency</option>
                        <option value="papers">Papers</option>
                        <option value="students">Students</option>
                        <option value="people">People</option>
                        <option value="items">Items</option>
                        <option value="sessions">Sessions</option>
                        <option value="datasets">Datasets</option>
                        <option value="briefs">Briefs</option>
                        <option value="partnerships">Partnerships</option>
                      </select>
                    </div>

                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Grant Target *</label>
                      <input
                        type="number"
                        placeholder="100"
                        min="0"
                        step="0.01"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        bind:value={newKPI.grant_wide_target}
                      />
                    </div>

                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
                      <select
                        class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        bind:value={newKPI.category}
                      >
                        <option value="research">Research</option>
                        <option value="training">Training</option>
                        <option value="infrastructure">Infrastructure</option>
                        <option value="community">Community</option>
                        <option value="financial">Financial</option>
                      </select>
                    </div>
                  </div>

                  <div class="mt-4">
                    <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      placeholder="Brief description of this KPI and how it will be measured"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows="3"
                      bind:value={newKPI.description}
                    ></textarea>
                  </div>

                  <div class="mt-4 flex justify-end">
                    <button
                      type="button"
                      on:click={addKPI}
                      disabled={!newKPI.name || !newKPI.grant_wide_target}
                      class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Add KPI
                    </button>
                  </div>
                </div>
              {/if}
            </div>

            <!-- Info Box -->
            <div class="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div class="flex gap-3">
                <span class="text-2xl">💡</span>
                <div class="text-sm text-blue-900">
                  <strong class="block mb-2">Why Define KPIs Now?</strong>
                  <ul class="list-disc list-inside space-y-1 text-blue-800">
                    <li>KPIs become part of your contractual agreement with the funder</li>
                    <li>They provide clear targets for milestone allocation and tracking</li>
                    <li>Enables automatic progress calculation and reporting</li>
                    <li>Ensures accountability and audit compliance throughout the project</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        {/if}

        <!-- Step 8: Review & Submit -->
        {#if currentStep === 8}
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

              <!-- KPI Summary -->
              {#if grantKPIs.length > 0}
                <div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-3">Key Performance Indicators</h3>
                  <div class="space-y-2">
                    {#each grantKPIs as kpi}
                      <div class="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
                        <div>
                          <span class="font-medium">{kpi.name}</span>
                          <span class="text-gray-500 text-xs ml-2">({kpi.category})</span>
                        </div>
                        <div class="text-right">
                          <div class="font-medium">{kpi.grant_wide_target} {kpi.unit}</div>
                          <div class="text-xs text-gray-500">Target</div>
                        </div>
                      </div>
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

            {#if currentStep < 8}
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

<!-- Milestone KPI Allocation Modal -->
{#if showMilestoneKPIAllocation && selectedMilestoneIndex !== null}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div class="border-b border-gray-200 p-6">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="text-lg font-semibold text-gray-900">KPI Allocation - {milestones[selectedMilestoneIndex]?.title || 'Milestone ' + (selectedMilestoneIndex + 1)}</h3>
            <p class="text-sm text-gray-600 mt-1">Allocate grant KPIs to this milestone with specific targets</p>
          </div>
          <button
            type="button"
            on:click={closeMilestoneKPIAllocation}
            class="text-gray-400 hover:text-gray-600 text-xl"
          >
            ✕
          </button>
        </div>
      </div>

      <div class="p-6">
        {#if milestones[selectedMilestoneIndex]?.kpiAllocations}
          <div class="space-y-4">
            <!-- Auto-distribute button -->
            <div class="flex justify-between items-center mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div>
                <p class="text-sm font-medium text-blue-900">Quick Distribution</p>
                <p class="text-xs text-blue-700">Distribute KPI targets equally across all milestones</p>
              </div>
              <button
                type="button"
                on:click={() => autoDistributeKPIs(selectedMilestoneIndex)}
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                Auto-Distribute All KPIs
              </button>
            </div>

            <!-- KPI Allocation List -->
            {#each milestones[selectedMilestoneIndex].kpiAllocations as allocation, kpiIndex}
              <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">KPI Name</label>
                    <div class="px-3 py-2 bg-white border border-gray-200 rounded-md text-sm">
                      <span class="font-medium">{allocation.kpiName}</span>
                      <span class="text-gray-500 text-xs ml-2">({allocation.kpiUnit})</span>
                    </div>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Milestone Target *</label>
                    <input
                      type="number"
                      placeholder="0"
                      min="0"
                      step="0.01"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={allocation.milestoneTarget}
                      on:input={(e) => updateMilestoneKPI(selectedMilestoneIndex, kpiIndex, 'milestoneTarget', e.target.value)}
                    />
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Allocation %</label>
                    <div class="px-3 py-2 bg-white border border-gray-200 rounded-md text-sm">
                      <span class="{allocation.allocationPercentage > 100 ? 'text-red-600' : 'text-gray-900'}">
                        {allocation.allocationPercentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                <div class="mt-3">
                  <label class="block text-sm font-medium text-gray-700 mb-1">Target Notes</label>
                  <textarea
                    rows="2"
                    placeholder="Notes on how this KPI will be measured or achieved for this milestone..."
                    class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={allocation.notes || ''}
                    on:input={(e) => updateMilestoneKPI(selectedMilestoneIndex, kpiIndex, 'notes', e.target.value)}
                  ></textarea>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-center py-8">
            <span class="text-4xl mb-2 block">📊</span>
            <p class="text-gray-600 mb-2">No KPIs defined yet</p>
            <p class="text-sm text-gray-500">Please define KPIs in Step 7 first</p>
          </div>
        {/if}
      </div>

      <div class="border-t border-gray-200 p-6">
        <div class="flex justify-end gap-3">
          <button
            type="button"
            on:click={closeMilestoneKPIAllocation}
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
          >
            Cancel
          </button>
          <button
            type="button"
            on:click={closeMilestoneKPIAllocation}
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            Save Allocations
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}