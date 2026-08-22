/**
 * x402 Research Orchestrator App JS (Material You MD3 Architecture)
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Element References
  const queryForm = document.getElementById('query-form');
  const queryInput = document.getElementById('query-input');
  const submitBtn = document.getElementById('submit-btn');
  const reportContainer = document.getElementById('report');
  const paymentStream = document.getElementById('payment-stream');

  // Stats Elements
  const statTotalAlgo = document.getElementById('stat-total-algo');
  const statCount = document.getElementById('stat-count');
  const statTruthfulnessVal = document.getElementById('stat-truthfulness-val');
  const statTruthfulnessBadge = document.getElementById('stat-truthfulness-badge');
  const statTruthfulnessFill = document.getElementById('stat-truthfulness-fill');
  const statTruthfulnessSubtext = document.getElementById('stat-truthfulness-subtext');

  // Drawer & Navigation Elements
  const historyDrawer = document.getElementById('history-drawer');
  const historyToggleBtn = document.getElementById('history-toggle-btn');
  const historyCloseBtn = document.getElementById('history-close-btn');
  const newChatBtn = document.getElementById('new-chat-btn');
  const historyList = document.getElementById('history-list');

  // Local Storage Key
  const HISTORY_STORAGE_KEY = 'x402_research_history_md3';

  // State Management
  let researchHistory = loadHistory();

  // Initialize marked parser options
  if (typeof marked !== 'undefined') {
    marked.setOptions({
      gfm: true,
      breaks: true
    });
  }

  // Render initial history drawer contents
  renderHistoryList();

  // Drawer Toggle Handlers
  historyToggleBtn?.addEventListener('click', () => {
    historyDrawer?.classList.add('open');
  });

  historyCloseBtn?.addEventListener('click', () => {
    historyDrawer?.classList.remove('open');
  });

  newChatBtn?.addEventListener('click', () => {
    resetView();
    historyDrawer?.classList.remove('open');
  });

  // Form Submit Listener
  queryForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    await runResearchQuery(query);
  });

  /**
   * Main Research Query Execution
   */
  async function runResearchQuery(query) {
    // Set UI to loading state
    setLoadingState(true);

    try {
      const response = await fetch('/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'HTTP Error ' + response.status }));
        throw new Error(errData.detail || 'Research request failed');
      }

      const data = await response.json();
      renderResearchResults(query, data);

      // Save to local history
      saveToHistory({
        id: data.task_id || Date.now().toString(),
        query,
        timestamp: new Date().toISOString(),
        data
      });

    } catch (err) {
      console.error('Research error:', err);
      renderErrorState(err.message);
    } finally {
      setLoadingState(false);
    }
  }

  /**
   * Render Research Results to DOM
   */
  function renderResearchResults(query, data) {
    // 1. Render Markdown & LaTeX Math Report
    const reportMarkdown = data.report_markdown || 'No report generated.';
    let htmlContent = typeof marked !== 'undefined' ? marked.parse(reportMarkdown) : reportMarkdown;

    reportContainer.innerHTML = `<div class="report-body">${htmlContent}</div>`;

    // Trigger KaTeX render if available
    if (window.renderMathInElement) {
      window.renderMathInElement(reportContainer, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false }
        ]
      });
    }

    // 2. Render Payment Ledger & Totals
    const payments = data.payments || {};
    const txs = payments.payments || payments.ledger || [];
    const totalAlgo = payments.total_algo || 0.0;

    statTotalAlgo.textContent = `₳ ${totalAlgo.toFixed(4)}`;
    statCount.textContent = `${txs.length} Micro-Transactions`;

    if (txs.length === 0) {
      paymentStream.innerHTML = '<div class="payment-empty">No transactions recorded for this query.</div>';
    } else {
      paymentStream.innerHTML = txs.map(tx => {
        const txHash = tx.tx || tx.txid || tx.transaction_id || '';
        const displayHash = txHash ? (txHash.length > 14 ? txHash.substring(0, 10) + '...' : txHash) : 'Internal Ledger';
        const displayTime = tx.timestamp ? new Date(typeof tx.timestamp === 'number' && tx.timestamp < 10000000000 ? tx.timestamp * 1000 : tx.timestamp).toLocaleTimeString() : 'Verified';
        const amount = tx.amount_algo ?? tx.amount_usdc ?? 0.0;
        return `
        <div class="tx-card">
          <div class="tx-top">
            <span class="tx-service">${escapeHtml(tx.service || tx.subtask || 'x402 Micro-Service')}</span>
            <span class="tx-algo">₳ ${amount.toFixed(4)}</span>
          </div>
          <div class="tx-bottom">
            <span class="tx-hash" title="${escapeHtml(txHash)}">${escapeHtml(displayHash)}</span>
            <span>${displayTime}</span>
          </div>
        </div>
      `;
      }).join('');
    }

    // 2.5 Render Sources Stream
    const sources = data.sources || [];
    const sourcesStream = document.getElementById('sources-stream');
    const sourcesCountChip = document.getElementById('sources-count-chip');

    if (sourcesCountChip) {
      sourcesCountChip.textContent = `${sources.length} Verified`;
    }

    if (sourcesStream) {
      if (sources.length === 0) {
        sourcesStream.innerHTML = '<div class="payment-empty">No sources cited for this query.</div>';
      } else {
        sourcesStream.innerHTML = sources.map(src => {
          let urlText = src;
          let isUrl = false;
          try {
            if (src.startsWith('http://') || src.startsWith('https://')) {
              isUrl = true;
            }
          } catch(e){}

          return `
            <div class="source-card">
              <div class="source-top">
                <span class="source-icon">🌐</span>
                ${isUrl ? `<a href="${escapeHtml(src)}" target="_blank" rel="noopener noreferrer" class="source-link">${escapeHtml(src)}</a>` : `<span class="source-title">${escapeHtml(src)}</span>`}
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // 3. Render Fact Truthfulness Score Stats
    const reliability = data.reliability_summary || {};
    // Check both overall_reliability_pct (from backend writer.py) and truthfulness_score
    let percentage = null;
    if (typeof reliability.overall_reliability_pct === 'number') {
      percentage = Math.round(reliability.overall_reliability_pct);
    } else if (typeof reliability.truthfulness_score === 'number') {
      percentage = Math.round(reliability.truthfulness_score <= 1 ? reliability.truthfulness_score * 100 : reliability.truthfulness_score);
    }

    if (percentage !== null) {
      statTruthfulnessVal.textContent = `${percentage}%`;
      statTruthfulnessFill.style.width = `${percentage}%`;
      const claimsChecked = reliability.total_claims || reliability.total_claims_checked || (reliability.verified_claims ? reliability.verified_claims.length : 0);
      const verifiedClaims = reliability.verified_count || reliability.verified_claims || (reliability.verified_claims ? reliability.verified_claims.length : 0);
      statTruthfulnessSubtext.textContent = claimsChecked ? `Based on ${claimsChecked} claims checked` : 'Fact verification complete';

      if (percentage >= 80) {
        statTruthfulnessBadge.textContent = 'High Truthfulness';
        statTruthfulnessBadge.className = 'chip chip-active';
        statTruthfulnessFill.style.backgroundColor = '#2E7D32';
      } else if (percentage >= 50) {
        statTruthfulnessBadge.textContent = 'Moderate Risk';
        statTruthfulnessBadge.className = 'chip';
        statTruthfulnessFill.style.backgroundColor = '#F57C00';
      } else {
        statTruthfulnessBadge.textContent = 'Low Accuracy';
        statTruthfulnessBadge.className = 'chip';
        statTruthfulnessFill.style.backgroundColor = '#C62828';
      }
    } else {
      statTruthfulnessVal.textContent = 'N/A';
      statTruthfulnessBadge.textContent = 'Unverified';
      statTruthfulnessBadge.className = 'chip';
      statTruthfulnessFill.style.width = '0%';
      statTruthfulnessSubtext.textContent = 'Fact-checker skipped or unavailable';
    }
  }

  /**
   * UI Loading & Reset Helper Methods
   */
  function setLoadingState(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `
        <div class="md3-spinner" style="width: 20px; height: 20px; border-width: 2px;"></div>
        <span>Orchestrating...</span>
      `;

      reportContainer.innerHTML = `
        <div class="loading-box">
          <div class="md3-spinner"></div>
          <h4 style="font-weight: 500; color: var(--md-on-surface);">Executing Agent Graph & ALGO Micro-Settlements</h4>
          <p style="color: var(--md-on-surface-variant); font-size: 0.9rem;">Dispatching dynamic HTTP 402 payment challenges to researcher, summarizer & fact-check nodes...</p>
        </div>
      `;
    } else {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `
        <span>Run Research</span>
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
        </svg>
      `;
    }
  }

  function renderErrorState(errorMsg) {
    reportContainer.innerHTML = `
      <div style="background-color: #FFEDEA; border-radius: var(--radius-md); padding: 24px; color: #C62828;">
        <h3 style="font-weight: 500; margin-bottom: 8px;">Orchestrator Execution Error</h3>
        <p style="font-size: 0.95rem;">${escapeHtml(errorMsg)}</p>
      </div>
    `;
  }

  function resetView() {
    queryInput.value = '';
    reportContainer.innerHTML = `
      <div class="report-placeholder">
        <div class="placeholder-icon-container">
          <svg class="placeholder-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"></path>
          </svg>
        </div>
        <h3>Start Your Research</h3>
        <p>Enter a topic in the floating search dock below to launch the autonomous agent graph & ALGO micro-settlement pipeline.</p>
      </div>
    `;
    paymentStream.innerHTML = '<div class="payment-empty">No transactions yet in this session.</div>';
    statTotalAlgo.textContent = '₳ 0.0000';
    statCount.textContent = '0 Micro-Transactions';
    statTruthfulnessVal.textContent = '--';
    statTruthfulnessBadge.textContent = 'Pending';
    statTruthfulnessBadge.className = 'chip chip-status';
    statTruthfulnessFill.style.width = '0%';
    statTruthfulnessSubtext.textContent = 'Waiting for query...';
  }

  /**
   * Local History Management
   */
  function loadHistory() {
    try {
      const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function saveToHistory(entry) {
    researchHistory.unshift(entry);
    if (researchHistory.length > 20) researchHistory.pop();
    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(researchHistory));
    } catch (e) {
      console.warn('LocalStorage save failed:', e);
    }
    renderHistoryList();
  }

  function renderHistoryList() {
    if (!historyList) return;
    if (researchHistory.length === 0) {
      historyList.innerHTML = '<div class="history-empty">No previous research sessions.</div>';
      return;
    }

    historyList.innerHTML = researchHistory.map((item, index) => `
      <div class="history-item" data-index="${index}">
        <div class="history-query">${escapeHtml(item.query)}</div>
        <div class="history-meta">
          <span>${new Date(item.timestamp).toLocaleDateString()}</span>
          <span>₳ ${(item.data?.payments?.total_algo || 0).toFixed(3)}</span>
        </div>
      </div>
    `).join('');

    historyList.querySelectorAll('.history-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.getAttribute('data-index'), 10);
        const item = researchHistory[idx];
        if (item) {
          queryInput.value = item.query;
          renderResearchResults(item.query, item.data);
          historyDrawer?.classList.remove('open');
        }
      });
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, (m) => {
      return { '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#039;' }[m];
    });
  }
});