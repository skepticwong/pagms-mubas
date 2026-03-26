<!-- frontend/src/components/BudgetAmendmentHistory.svelte -->
<!-- Audit-critical: shows immutable BEFORE/AFTER snapshots for every budget amendment -->
<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  export let grantId;
  export let grantCode = '';
  export let grantTitle = '';
  export let onClose = () => {};

  let history = [];
  let loading = true;
  let error = '';
  let faRate = 0;
  let totalAmendments = 0;
  let exporting = false;

  onMount(async () => {
    await loadHistory();
  });

  async function loadHistory() {
    loading = true;
    error = '';
    try {
      const res = await axios.get(`/api/grants/${grantId}/budget-snapshot-history`, {
        withCredentials: true
      });
      history = res.data.history || [];
      faRate = res.data.fa_rate || 0;
      totalAmendments = res.data.total_amendments || 0;
    } catch (err) {
      error = err.response?.data?.error || 'Failed to load amendment history';
    } finally {
      loading = false;
    }
  }

  async function exportCSV() {
    exporting = true;
    try {
      const res = await axios.get(`/api/grants/${grantId}/budget-snapshot-history/export`, {
        withCredentials: true,
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${grantCode}_Amendment_History.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      error = 'Failed to export CSV';
    } finally {
      exporting = false;
    }
  }

  function fmt(num) {
    if (num == null) return 'N/A';
    return new Intl.NumberFormat('en-MW', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(num);
  }

  function fmtDate(ds) {
    if (!ds) return 'N/A';
    return new Date(ds).toLocaleDateString('en-GB', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }

  function deltaClass(change) {
    if (change > 0) return 'positive';
    if (change < 0) return 'negative';
    return '';
  }

  function statusBadge(status) {
    const map = {
      baseline: { bg: '#e0f2fe', color: '#0369a1', text: 'Baseline' },
      approved: { bg: '#dcfce7', color: '#15803d', text: 'Approved ✅' },
      pending:  { bg: '#fef9c3', color: '#854d0e', text: 'Pending ⏳' },
      rejected: { bg: '#fee2e2', color: '#b91c1c', text: 'Rejected ❌' }
    };
    return map[status] || { bg: '#f3f4f6', color: '#374151', text: status };
  }
</script>

<style>
  .overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.55);
    display: flex; align-items: center; justify-content: center;
    z-index: 1050; padding: 1rem;
  }
  .modal {
    background: #fff;
    border-radius: 1.25rem;
    width: 100%; max-width: 960px;
    max-height: 90vh; overflow-y: auto;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  }
  .header {
    background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
    color: #fff; padding: 1.5rem 2rem;
    border-radius: 1.25rem 1.25rem 0 0;
    display: flex; justify-content: space-between; align-items: flex-start;
  }
  .header h2 { margin: 0; font-size: 1.35rem; font-weight: 700; }
  .header p  { margin: 0.25rem 0 0; font-size: 0.85rem; opacity: 0.8; }
  .close-btn {
    background: rgba(255,255,255,0.15); border: none; color: #fff;
    width: 2rem; height: 2rem; border-radius: 50%; cursor: pointer;
    font-size: 1.1rem; display: flex; align-items: center; justify-content: center;
    transition: background 0.2s;
  }
  .close-btn:hover { background: rgba(255,255,255,0.3); }
  .toolbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 2rem; border-bottom: 1px solid #e5e7eb; gap: 1rem;
  }
  .stats { display: flex; gap: 1.5rem; }
  .stat { text-align: center; }
  .stat .val { font-size: 1.25rem; font-weight: 800; color: #1e3a8a; }
  .stat .lbl { font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
  .export-btn {
    background: #1e3a8a; color: #fff; border: none;
    padding: 0.55rem 1.1rem; border-radius: 0.5rem;
    cursor: pointer; font-size: 0.85rem; font-weight: 600;
    display: flex; align-items: center; gap: 0.4rem;
    transition: background 0.2s;
  }
  .export-btn:hover:not(:disabled) { background: #1d4ed8; }
  .export-btn:disabled { opacity: 0.6; cursor: not-allowed; }
  .body { padding: 1.5rem 2rem; }
  .entry { margin-bottom: 1.5rem; }
  .entry-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.75rem;
  }
  .entry-num {
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: #374151;
  }
  .badge {
    font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.65rem;
    border-radius: 999px;
  }
  .entry-meta {
    font-size: 0.78rem; color: #6b7280; margin-bottom: 0.5rem;
    display: flex; flex-wrap: wrap; gap: 1rem;
  }
  .reason-box {
    background: #f8fafc; border-left: 3px solid #3b82f6;
    padding: 0.6rem 0.9rem; border-radius: 0 0.4rem 0.4rem 0;
    font-size: 0.83rem; color: #374151; margin-bottom: 0.75rem;
    font-style: italic;
  }
  /* diff table */
  .diff-table {
    width: 100%; border-collapse: collapse; font-size: 0.82rem;
    border: 1px solid #e5e7eb; border-radius: 0.5rem; overflow: hidden;
  }
  .diff-table th {
    background: #f1f5f9; text-align: left; padding: 0.5rem 0.75rem;
    font-weight: 700; color: #374151; font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.04em;
  }
  .diff-table td { padding: 0.45rem 0.75rem; border-top: 1px solid #e5e7eb; color: #374151; }
  .diff-table tr:hover td { background: #f8fafc; }
  .positive { color: #15803d; font-weight: 700; }
  .negative { color: #b91c1c; font-weight: 700; }
  .indirect-row td { background: #fef9c3 !important; }
  .indirect-tag {
    font-size: 0.68rem; background: #fde68a; color: #92400e;
    padding: 0.1rem 0.4rem; border-radius: 999px; margin-left: 0.4rem;
    font-weight: 700;
  }
  .baseline-after {
    font-size: 0.8rem; color: #6b7280; margin-top: 0.35rem;
    font-style: italic;
  }
  .divider { border: none; border-top: 2px dashed #e5e7eb; margin: 1.5rem 0; }
  .loading-box { text-align: center; padding: 3rem; color: #6b7280; }
  .spinner {
    display: inline-block; width: 1.5rem; height: 1.5rem;
    border: 3px solid #e5e7eb; border-top-color: #1d4ed8;
    border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 0.75rem;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .err { background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c;
    padding: 0.75rem; border-radius: 0.5rem; margin: 1rem 2rem; }
  .empty { text-align: center; padding: 3rem; color: #9ca3af; }
  .empty-icon { font-size: 3rem; margin-bottom: 0.75rem; }
</style>

<div
  class="overlay"
  role="presentation"
  on:click={(e) => e.target === e.currentTarget && onClose()}
  on:keydown={(e) => e.key === 'Escape' && onClose()}
>
  <div class="modal" role="dialog" aria-label="Budget Amendment History">

    <!-- Header -->
    <div class="header">
      <div>
        <h2>📋 Budget Amendment History</h2>
        <p>{grantTitle} · {grantCode}{faRate > 0 ? ` · F&A Rate: ${(faRate * 100).toFixed(0)}%` : ''}</p>
      </div>
      <button class="close-btn" on:click={onClose} aria-label="Close">✕</button>
    </div>

    <!-- Error -->
    {#if error}
      <div class="err"><strong>Error:</strong> {error}</div>
    {/if}

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="stats">
        <div class="stat">
          <div class="val">{totalAmendments}</div>
          <div class="lbl">Total Amendments</div>
        </div>
        {#if faRate > 0}
          <div class="stat">
            <div class="val">{(faRate * 100).toFixed(0)}%</div>
            <div class="lbl">F&amp;A Overhead Rate</div>
          </div>
        {/if}
      </div>
      <button class="export-btn" on:click={exportCSV} disabled={exporting || loading}>
        {#if exporting}
          ⏳ Exporting…
        {:else}
          ⬇️ Export Audit CSV
        {/if}
      </button>
    </div>

    <!-- Body -->
    <div class="body">
      {#if loading}
        <div class="loading-box">
          <div class="spinner"></div>
          <p>Loading amendment history…</p>
        </div>
      {:else if history.length === 0}
        <div class="empty">
          <div class="empty-icon">📁</div>
          <p>No amendment history found for this grant.</p>
          <p style="font-size: 0.8rem; margin-top: 0.5rem;">Amendments will appear here once budget reallocations are submitted and approved.</p>
        </div>
      {:else}
        {#each history as entry, i}
          {#if i > 0}
            <hr class="divider" />
          {/if}

          <div class="entry">
            <!-- Entry Header -->
            <div class="entry-header">
              <span class="entry-num">
                {entry.entry_type === 'baseline' ? '🏁 Initial Budget (Baseline)' : `Amendment #${entry.amendment_number}`}
              </span>
              {#if entry.status}
                {@const badge = statusBadge(entry.status)}
                <span class="badge" style="background:{badge.bg};color:{badge.color}">{badge.text}</span>
              {/if}
            </div>

            <!-- Meta -->
            <div class="entry-meta">
              <span>📅 {fmtDate(entry.date)}</span>
              {#if entry.requested_by}
                <span>👤 Requested by: <strong>{entry.requested_by}</strong></span>
              {/if}
              {#if entry.approved_by}
                <span>✅ Approved by: <strong>{entry.approved_by}</strong> on {fmtDate(entry.approved_at)}</span>
              {/if}
              {#if entry.amount}
                <span>💰 Amount: <strong>{fmt(entry.amount)}</strong></span>
              {/if}
            </div>

            <!-- Reason -->
            {#if entry.reason}
              <div class="reason-box">"{entry.reason}"</div>
            {/if}

            <!-- Baseline: show initial state -->
            {#if entry.entry_type === 'baseline' && entry.after}
              <p class="baseline-after">Initial budget allocation at grant creation:</p>
              <table class="diff-table">
                <thead>
                  <tr>
                    <th>Budget Category</th>
                    <th>Initial Allocation</th>
                    <th>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {#each entry.after as cat}
                    <tr class="{cat.is_indirect ? 'indirect-row' : ''}">
                      <td>
                        {cat.name}
                        {#if cat.is_indirect}<span class="indirect-tag">🔒 F&A Overhead</span>{/if}
                      </td>
                      <td>{fmt(cat.allocated)}</td>
                      <td style="font-size:0.75rem;color:{cat.is_indirect ? '#92400e' : '#374151'}">
                        {cat.is_indirect ? 'Indirect (Locked)' : 'Direct (Spendable)'}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>

            <!-- Amendment: show BEFORE / AFTER diff -->
            {:else if entry.before && entry.after}
              <table class="diff-table">
                <thead>
                  <tr>
                    <th>Budget Category</th>
                    <th>BEFORE</th>
                    <th>AFTER</th>
                    <th>Change</th>
                  </tr>
                </thead>
                <tbody>
                  {#each entry.before as beforeCat}
                    {@const afterCat = entry.after.find(a => a.name === beforeCat.name)}
                    {@const change = afterCat ? afterCat.allocated - beforeCat.allocated : 0}
                    {#if Math.abs(change) > 0.01 || beforeCat.is_indirect}
                      <tr class="{beforeCat.is_indirect ? 'indirect-row' : ''}">
                        <td>
                          {beforeCat.name}
                          {#if beforeCat.is_indirect}<span class="indirect-tag">🔒 F&A</span>{/if}
                        </td>
                        <td>{fmt(beforeCat.allocated)}</td>
                        <td>{fmt(afterCat?.allocated ?? beforeCat.allocated)}</td>
                        <td class="{deltaClass(change)}">
                          {change > 0 ? '+' : ''}{fmt(change)}
                        </td>
                      </tr>
                    {/if}
                  {/each}
                </tbody>
              </table>

            {:else if entry.before && !entry.after}
              <!-- Pending/Rejected: show BEFORE only -->
              <p style="font-size:0.8rem;color:#6b7280;margin-bottom:0.5rem;">
                {entry.status === 'pending' ? '⏳ Pending — changes not yet applied.' : '❌ Rejected — budget unchanged.'}
              </p>
              <table class="diff-table">
                <thead>
                  <tr>
                    <th>Budget Category</th>
                    <th>Current Allocation (unchanged)</th>
                  </tr>
                </thead>
                <tbody>
                  {#each entry.before as cat}
                    <tr>
                      <td>{cat.name}</td>
                      <td>{fmt(cat.allocated)}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  </div>
</div>
