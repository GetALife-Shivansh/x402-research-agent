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

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span>Orchestrating...</span>';
  reportDiv.innerHTML = '<div style="text-align: center; padding: 60px 0; color: var(--algo-teal); font-family: var(--font-mono);"><p>⚡ Executing Agent Graph & Algorand x402 Settlement...</p></div>';

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
    
    // Render Markdown & pre-process raw LaTeX formulas
    let rawMarkdown = data.report_markdown || data.final_report || data.report || '';

    // 1. Convert block math \[ ... \] to $$ ... $$
    rawMarkdown = rawMarkdown.replace(/\\\[([\s\S]*?)\\\]/g, '\n\n$$$$ $1 $$$$\n\n');

    // 2. Convert \( ... \) to $ ... $
    rawMarkdown = rawMarkdown.replace(/\\\((.*?)\\\)/g, ' $$$1$ ');

    // 3. Convert parenthesized LaTeX expressions like (\operatorname{...}) or (\frac{...}) or (s=\tfrac12) to $...$
    rawMarkdown = rawMarkdown.replace(/\(([^\n\)]*?\\[a-zA-Z]+[^\n\)]*?)\)/g, ' $$$1$ ');

    reportDiv.innerHTML = marked.parse(rawMarkdown);

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