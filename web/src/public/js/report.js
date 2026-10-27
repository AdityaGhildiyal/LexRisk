// LexRisk Report Page Interactions, Copy Utility, & Formatted Plain-Text Export

let currentFilter = 'all';

function filterClauses(filter, btn) {
  currentFilter = filter;
  document.querySelectorAll('.filter-chip').forEach(b => {
    b.classList.remove('active');
    b.setAttribute('aria-selected', 'false');
  });

  if (btn) {
    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');
  }

  applyFilterAndSearch();
}

function filterByTier(tier) {
  let chipId = 'chip-all';
  if (tier === 'critical') chipId = 'chip-critical';
  else if (tier === 'high') chipId = 'chip-high';
  else if (tier === 'moderate') {
    // Custom moderate filter
    currentFilter = 'moderate';
    document.querySelectorAll('.filter-chip').forEach(b => {
      b.classList.remove('active');
      b.setAttribute('aria-selected', 'false');
    });
    applyFilterAndSearch();
    showToast('Filtering: Moderate Risk clauses');
    return;
  } else if (tier === 'low') {
    currentFilter = 'low';
    document.querySelectorAll('.filter-chip').forEach(b => {
      b.classList.remove('active');
      b.setAttribute('aria-selected', 'false');
    });
    applyFilterAndSearch();
    showToast('Filtering: Low Risk clauses');
    return;
  }

  const chip = document.getElementById(chipId);
  if (chip) chip.click();
}

function searchClauses(query) {
  const clearBtn = document.getElementById('search-clear-btn');
  if (clearBtn) {
    if (query && query.trim().length > 0) {
      clearBtn.classList.remove('hidden');
    } else {
      clearBtn.classList.add('hidden');
    }
  }
  applyFilterAndSearch();
}

function clearSearch() {
  const input = document.getElementById('clause-search');
  if (input) {
    input.value = '';
    searchClauses('');
    input.focus();
  }
}

function applyFilterAndSearch() {
  const searchInput = document.getElementById('clause-search');
  const q = searchInput ? searchInput.value.toLowerCase().trim() : '';

  const allCards = document.querySelectorAll('.clause-row');
  let visibleCount = 0;

  allCards.forEach(card => {
    let matchesFilter = true;
    const rClass = card.dataset.riskClass;
    const isFlagged = card.dataset.flagged === 'true';

    if (currentFilter === 'critical') matchesFilter = (rClass === 'critical');
    else if (currentFilter === 'high') matchesFilter = (rClass === 'critical' || rClass === 'high');
    else if (currentFilter === 'moderate') matchesFilter = (rClass === 'moderate');
    else if (currentFilter === 'low') matchesFilter = (rClass === 'low');
    else if (currentFilter === 'flagged') matchesFilter = isFlagged;

    let matchesSearch = true;
    if (q) {
      const text = card.textContent.toLowerCase();
      matchesSearch = text.includes(q);
    }

    const show = matchesFilter && matchesSearch;
    card.style.display = show ? '' : 'none';
    if (show) visibleCount++;
  });

  const counterEl = document.getElementById('search-counter');
  if (counterEl) {
    if (q || currentFilter !== 'all') {
      counterEl.textContent = `Showing ${visibleCount} of ${allCards.length}`;
    } else {
      counterEl.textContent = '';
    }
  }
}

/**
 * Copies clause provision text to clipboard with micro-interaction feedback.
 */
async function copyClauseText(btn, text) {
  try {
    await navigator.clipboard.writeText(text);
    const label = btn.querySelector('.copy-label');
    const originalLabel = label ? label.textContent : 'Copy';
    
    btn.classList.add('copied');
    if (label) label.textContent = 'Copied';

    showToast('Provision copied to clipboard');

    setTimeout(() => {
      btn.classList.remove('copied');
      if (label) label.textContent = originalLabel;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy clause:', err);
    showToast('Unable to copy to clipboard');
  }
}

/**
 * Ephemeral toast notification.
 */
function showToast(message) {
  const toast = document.getElementById('toast');
  if (!toast) return;

  toast.textContent = message;
  toast.classList.remove('hidden');
  toast.classList.add('visible');

  if (window._toastTimeout) clearTimeout(window._toastTimeout);
  window._toastTimeout = setTimeout(() => {
    toast.classList.remove('visible');
    setTimeout(() => toast.classList.add('hidden'), 250);
  }, 2200);
}

/**
 * Generates an elegantly formatted ASCII / Plain-Text Contract Audit Report
 * and triggers a client-side .txt download.
 */
function downloadTextReport() {
  const dataEl = document.getElementById('report-json-data');
  if (!dataEl) {
    showToast('Report data unavailable for download.');
    return;
  }

  let report;
  try {
    report = JSON.parse(dataEl.textContent);
  } catch (e) {
    console.error('Failed to parse report data:', e);
    showToast('Could not generate text report.');
    return;
  }

  const generatedDate = new Date(report.generated_at).toLocaleString('en-US', {
    dateStyle: 'full',
    timeStyle: 'short'
  });
  const contractId = report.contract_id || 'N/A';

  const critical = report.clauses.filter(c => c.risk_score >= 0.80).length;
  const high = report.clauses.filter(c => c.risk_score >= 0.65 && c.risk_score < 0.80).length;
  const moderate = report.clauses.filter(c => c.risk_score >= 0.35 && c.risk_score < 0.65).length;
  const low = report.clauses.filter(c => c.risk_score < 0.35).length;

  const lineW = 78;
  const sepDbl = '='.repeat(lineW);
  const sepSgl = '-'.repeat(lineW);
  const sepDsh = '.'.repeat(lineW);

  let out = [];

  out.push(sepDbl);
  out.push('  LEXRISK CONTRACT REVIEW & RISK AUDIT REPORT');
  out.push(sepDbl);
  out.push(`Report ID        : ${contractId}`);
  out.push(`Generated At     : ${generatedDate}`);
  out.push(`Corpus Precedent : CUAD & LEDGAR Reference Index Partition`);
  out.push(`Entailment Model : cross-encoder/nli-deberta-v3-small (Local CPU)`);
  out.push(sepSgl);
  out.push('EXECUTIVE AUDIT SUMMARY:');
  out.push(`  * Total Clauses Analyzed : ${report.total_clauses}`);
  out.push(`  * High-Risk Clauses      : ${report.high_risk_count}`);
  out.push(`  * Flagged Summaries      : ${report.faithfulness_flags}`);
  out.push(`  * Risk Breakdown         : Critical (${critical}) | High (${high}) | Moderate (${moderate}) | Low (${low})`);
  out.push(sepDbl);
  out.push('');

  report.clauses.forEach((c, idx) => {
    let riskTier = 'LOW';
    if (c.risk_score >= 0.80) riskTier = 'CRITICAL';
    else if (c.risk_score >= 0.65) riskTier = 'HIGH';
    else if (c.risk_score >= 0.35) riskTier = 'MODERATE';

    const clauseType = (c.clause_type || 'other').replace(/_/g, ' ').toUpperCase();
    const riskPct = (c.risk_score * 100).toFixed(0) + '%';
    const num = String(idx + 1).padStart(2, '0');

    out.push(`[${num}] CLAUSE TYPE: ${clauseType}  |  RISK LEVEL: ${riskTier} (${riskPct})`);
    out.push(sepSgl);

    // Operative Provision
    out.push('ORIGINAL CONTRACT PROVISION:');
    const rawLines = wrapText(c.text.trim(), lineW - 4);
    rawLines.forEach(l => out.push('  ' + l));
    out.push('');

    // Summary Matrix
    if (c.summary) {
      out.push('PLAIN-LANGUAGE INTERPRETATION:');
      out.push(`  * Plain English : ${c.summary.meaning || '—'}`);
      out.push(`  * Obligated Party: ${c.summary.obligor || '—'}`);
      out.push(`  * Trigger Event : ${c.summary.trigger || '—'}`);
      out.push(`  * Legal Remedy  : ${c.summary.consequence || '—'}`);
      
      if (c.summary.faithfulness_flag) {
        const fScore = (c.summary.faithfulness_score * 100).toFixed(0);
        out.push(`  ! ENTAILMENT NOTICE: Score ${fScore}%. Summary may not fully match the exact text.`);
      }
      out.push('');
    }

    // Scoring & Deviation Audit
    out.push('AUDIT RATIONALE & METRICS:');
    const devStr = (c.deviation_score !== null && c.deviation_score !== undefined)
      ? `${(c.deviation_score * 100).toFixed(1)}%`
      : 'Uncomputed (Phase 3 Reference Index Pending)';
    out.push(`  * Corpus Anomaly: ${devStr}`);
    out.push(`  * Scoring Logic : ${c.risk_rationale}`);
    out.push(sepDsh);
    out.push('');
  });

  out.push(sepDbl);
  out.push('END OF AUDIT REPORT — Generated by LexRisk');
  out.push(sepDbl);

  const textContent = out.join('\n');
  const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `LexRisk_Audit_${contractId.slice(0, 8)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Audit report downloaded');
}

function wrapText(str, maxW) {
  const words = str.split(/\s+/);
  const lines = [];
  let cur = '';
  for (let w of words) {
    if ((cur + ' ' + w).trim().length <= maxW) {
      cur = (cur + ' ' + w).trim();
    } else {
      if (cur) lines.push(cur);
      cur = w;
    }
  }
  if (cur) lines.push(cur);
  return lines;
}
