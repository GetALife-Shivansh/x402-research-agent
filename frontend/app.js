let totalAlgoSpent = 0.0;
let paymentCount = 0;

const queryForm = document.getElementById('query-form');
const queryInput = document.getElementById('query-input');
const submitBtn = document.getElementById('submit-btn');
const reportDiv = document.getElementById('report');
const paymentStream = document.getElementById('payment-stream');
const statTotalAlgo = document.getElementById('stat-total-algo');
const statCount = document.getElementById('stat-count');

queryForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;

  // Get HTML element references for top stat bar
  const statTruthfulnessVal = document.getElementById('stat-truthfulness-val');
  const statTruthfulnessBadge = document.getElementById('stat-truthfulness-badge');
  const statTruthfulnessFill = document.getElementById('stat-truthfulness-fill');
  const statTruthfulnessSubtext = document.getElementById('stat-truthfulness-subtext');

  if (statTruthfulnessBadge) {
    statTruthfulnessBadge.innerText = 'Analyzing...';
    statTruthfulnessBadge.style.background = 'rgba(56, 189, 248, 0.2)';
    statTruthfulnessBadge.style.color = '#38bdf8';
  }
  if (statTruthfulnessSubtext) {
    statTruthfulnessSubtext.innerText = 'Evaluating truthfulness claims...';
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span>Orchestrating & Fact-Checking...</span>';
  reportDiv.innerHTML = '<div style="text-align: center; padding: 60px 0; color: var(--algo-teal); font-family: var(--font-mono);"><p>⚡ Executing Agent Graph, Algorand x402 Settlement & Deep Truthfulness Verification...</p></div>';

  try {
    const resp = await fetch('/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    if (!resp.ok) {
      throw new Error('HTTP Error ' + resp.status);
    }

    const data = await resp.json();
    
    // Update Truthfulness stat card header if reliability summary is present
    const rel = data.reliability_summary;
    if (rel) {
      updateTruthfulnessStatCard(rel, statTruthfulnessVal, statTruthfulnessBadge, statTruthfulnessFill, statTruthfulnessSubtext);
    }

    // Render Markdown & pre-process raw LaTeX formulas
    let rawMarkdown = data.report_markdown || data.final_report || data.report || '';

    // 1. Convert block math \[ ... \] to $$ ... $$
    rawMarkdown = rawMarkdown.replace(/\\\[([\s\S]*?)\\\]/g, '\n\n$$$$ $1 $$$$\n\n');

    // 2. Convert \( ... \) to $ ... $
    rawMarkdown = rawMarkdown.replace(/\\\((.*?)\\\)/g, ' $$$1$ ');

    // 3. Convert parenthesized LaTeX expressions like (\operatorname{...}) or (\frac{...}) to $...$
    rawMarkdown = rawMarkdown.replace(/\(([^\n\)]*?\\[a-zA-Z]+[^\n\)]*?)\)/g, ' $$$1$ ');

    let reportHtml = marked.parse(rawMarkdown);

    // Build Overall Reliability & Fact-Check Verification Process section if present
    if (rel) {
      const processHtml = renderFactCheckProcessSection(rel);
      reportHtml = reportHtml + processHtml;
    }

    reportDiv.innerHTML = reportHtml;

    // Render LaTeX equations with KaTeX
    if (window.renderMathInElement) {
      renderMathInElement(reportDiv, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true }
        ],
        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
        throwOnError: false
      });
    }

    // Extract ledger payments if present
    const paymentData = data.payments || data.ledger;
    if (paymentData) {
      const list = Array.isArray(paymentData) ? paymentData : (paymentData.payments || []);
      list.forEach(p => addPaymentToSidebar(p));
    }

  } catch (err) {
    reportDiv.innerHTML = `<div style="color: #ef4444; padding: 20px; font-family: var(--font-mono);">Error running research: ${err.message}. Make sure start.py is running.</div>`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span>Run Research</span>';
  }
});

function getScoreColor(pct) {
  if (pct >= 81) return 'var(--status-supported)';
  if (pct >= 61) return 'var(--status-true)';
  if (pct >= 41) return 'var(--status-disputed)';
  if (pct >= 21) return 'var(--status-false)';
  return 'var(--status-very-false)';
}

function updateTruthfulnessStatCard(rel, valEl, badgeEl, fillEl, subtextEl) {
  if (!valEl) return;
  const scorePct = rel.overall_reliability_pct || 85;
  const color = getScoreColor(scorePct);

  let statusLabel = 'High Trust';
  if (scorePct < 40) statusLabel = 'Low Trust';
  else if (scorePct < 70) statusLabel = 'Moderate Trust';

  valEl.innerText = `${scorePct}%`;
  valEl.style.color = color;

  if (badgeEl) {
    badgeEl.innerText = statusLabel;
    badgeEl.style.background = `${color}25`;
    badgeEl.style.color = color;
  }

  if (fillEl) {
    fillEl.style.width = `${scorePct}%`;
    fillEl.style.background = color;
  }

  if (subtextEl) {
    const total = rel.total_claims_analyzed || 0;
    subtextEl.innerText = `${total} Claims Verified`;
  }
}

function renderFactCheckProcessSection(rel) {
  const scorePct = rel.overall_reliability_pct || 85;
  const badgeColor = getScoreColor(scorePct);

  let verdictText = "Verified True & Strongly Supported";
  if (scorePct < 40) verdictText = "Unverified / Debunked";
  else if (scorePct < 70) verdictText = "Partially True / Disputed";

  return `
    <div style="margin-top: 40px; padding-top: 24px; border-top: 1px solid var(--border-card);">
      <div class="reliability-banner" style="margin-bottom: 16px;">
        <div class="reliability-header" style="align-items: center;">
          <div class="reliability-title-group">
            <span style="font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; color: #ffffff;">
              Final Process Step: x402 Fact Truthfulness Audit
            </span>
            <span class="reliability-score-badge" style="background: ${badgeColor}; font-size: 1rem; padding: 4px 12px;">
              Overall Truthfulness: ${scorePct}% (${verdictText})
            </span>
          </div>
          <div style="font-size: 0.85rem; font-family: var(--font-mono); color: var(--text-dim); margin-top: 6px;">
            Automated truthfulness evaluation completed at graph completion.
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderFactTruthfulnessSection(rel) {
  if (!rel.claims || rel.claims.length === 0) return '';

  let html = `
    <div style="margin-top: 36px; padding-top: 24px; border-top: 1px solid var(--border-card);">
      <h2 style="font-family: var(--font-display); font-size: 1.35rem; color: #ffffff; margin-bottom: 8px;">
        🔍 Fact Truthfulness Verification & Evidence Audits
      </h2>
      <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 20px;">
        Evaluated through independent x402-paid web cross-references, probing both supporting and disconfirming evidence.
      </p>
  `;

  rel.claims.forEach((item, idx) => {
    const scorePct = Math.round(item.truthfulness_score * 100);
    const color = getScoreColor(scorePct);

    html += `
      <div class="truthfulness-card">
        <div class="claim-header">
          <div class="claim-text">"${item.claim}"</div>
          <div class="claim-percentage" style="color: ${color};">
            Truthfulness: ${scorePct}%
          </div>
        </div>

        <div class="slider-container">
          <div class="slider-track">
            <div class="slider-fill" style="width: ${scorePct}%; background: ${color};"></div>
          </div>
          <div class="slider-thumb" style="left: ${scorePct}%;"></div>
          <div class="slider-labels">
            <span>Likely False (0%)</span>
            <span>Uncertain / Disputed (50%)</span>
            <span>Likely True (100%)</span>
          </div>
        </div>

        <div class="claim-meta-row">
          <div>
            <span style="font-weight: 600; color: ${color}; margin-right: 10px;">
              ${item.status || 'Verified'}
            </span>
            <span>Evidence confidence: <strong>${item.evidence_confidence || 'Medium'}</strong></span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span class="x402-spent-badge">
              ⚡ x402 cost: ₳ ${parseFloat(item.x402_spent_usdc || 0.0015).toFixed(4)}
            </span>
            <button class="toggle-evidence-btn" onclick="toggleEvidence(${idx})">
              Show Evidence Breakdown ▼
            </button>
          </div>
        </div>

        <div class="evidence-panel" id="evidence-panel-${idx}">
          ${item.summary ? `<p style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 12px;"><strong>Summary:</strong> ${item.summary}</p>` : ''}
          
          <div class="evidence-section">
            <div class="evidence-section-title supporting">
              ✓ Evidence Supporting the Claim
            </div>
            ${renderEvidenceList(item.supporting_evidence, 'supporting')}
          </div>

          <div class="evidence-section">
            <div class="evidence-section-title contradicting">
              ⚠ Evidence Contradicting or Weakening the Claim
            </div>
            ${renderEvidenceList(item.contradicting_evidence, 'contradicting')}
          </div>
        </div>
      </div>
    `;
  });

  html += `</div>`;
  return html;
}

function renderEvidenceList(list, type) {
  if (!list || list.length === 0) {
    if (type === 'contradicting') {
      return `<div class="empty-evidence">No significant contradictory evidence found during verification.</div>`;
    }
    return `<div class="empty-evidence">No direct supporting sources retrieved.</div>`;
  }

  return list.map(item => `
    <div class="evidence-item ${type}">
      <div class="evidence-item-explanation">${item.explanation}</div>
      <div class="evidence-item-meta">
        <span><strong>Source:</strong> ${item.source || 'Web Source'}</span>
        <span><strong>Strength:</strong> ${item.strength || 'Moderate'}</span>
        ${item.citation ? `<span><strong>Citation:</strong> <a href="${item.citation.startsWith('http') ? item.citation : '#'}" target="_blank" rel="noopener">${item.citation}</a></span>` : ''}
        ${item.date && item.date !== 'N/A' ? `<span><strong>Date:</strong> ${item.date}</span>` : ''}
      </div>
    </div>
  `).join('');
}

window.toggleEvidence = function(idx) {
  const panel = document.getElementById(`evidence-panel-${idx}`);
  if (panel) {
    panel.classList.toggle('active');
  }
};

function addPaymentToSidebar(p) {
  if (paymentCount === 0) {
    paymentStream.innerHTML = '';
  }
  paymentCount++;
  const amount = p.amount_algo || p.amount_usdc || 0.001;
  totalAlgoSpent += parseFloat(amount);

  statTotalAlgo.innerText = `₳ ${totalAlgoSpent.toFixed(4)}`;
  statCount.innerText = `${paymentCount} Micro-Transactions`;

  const item = document.createElement('div');
  item.className = 'payment-item';
  item.innerHTML = `
    <div class="payment-item-header">
      <span class="payment-service-name">${p.service || 'service'}</span>
      <span class="payment-amount">₳ ${parseFloat(amount).toFixed(4)}</span>
    </div>
    <div class="payment-tx-hash">tx: ${p.tx || 'algo_tx_mock'}</div>
    <div class="payment-net">${p.network || 'algorand-testnet'}</div>
  `;
  paymentStream.prepend(item);
}