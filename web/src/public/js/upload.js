// LexRisk Upload Interaction & Staged Pipeline Script

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.add('drag-over');
}

function handleDragLeave(e) {
  // Prevent flickering when dragging over child elements
  if (e.currentTarget.contains(e.relatedTarget)) return;
  document.getElementById('drop-zone').classList.remove('drag-over');
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('drag-over');
  if (e.dataTransfer && e.dataTransfer.files.length > 0) {
    setFile(e.dataTransfer.files[0]);
  }
}

function handleFileSelect(e) {
  if (e.target.files && e.target.files.length > 0) {
    setFile(e.target.files[0]);
  }
}

function formatBytes(bytes, decimals = 1) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function setFile(file) {
  const allowedExts = ['pdf', 'docx', 'doc', 'txt'];
  const extMatch = file.name.match(/\.([0-9a-z]+)$/i);
  const ext = extMatch ? extMatch[1].toLowerCase() : '';

  if (!allowedExts.includes(ext) && !file.type.match(/(pdf|word|plain)/i)) {
    alert('Please select a PDF, DOCX, or TXT file.');
    return;
  }

  // Populate file preview card
  const nameEl = document.getElementById('file-name');
  const sizeEl = document.getElementById('file-size');
  const extEl = document.getElementById('file-ext');

  if (nameEl) nameEl.textContent = file.name;
  if (sizeEl) sizeEl.textContent = formatBytes(file.size);
  if (extEl) extEl.textContent = ext.toUpperCase() || 'DOC';

  document.getElementById('file-selected').classList.remove('hidden');
  document.getElementById('drop-zone').style.display = 'none';

  const btn = document.getElementById('submit-btn');
  btn.disabled = false;
  document.getElementById('btn-text').textContent = `Review Document (${file.name})`;

  // Ensure file is attached to the input
  const contractInput = document.getElementById('contract-file');
  try {
    const dt = new DataTransfer();
    dt.items.add(file);
    contractInput.files = dt.files;
  } catch (err) {
    // Fallback for older browsers
  }
}

function clearFile() {
  const contractInput = document.getElementById('contract-file');
  if (contractInput) contractInput.value = '';

  document.getElementById('file-selected').classList.add('hidden');
  document.getElementById('drop-zone').style.display = 'block';

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  document.getElementById('btn-text').textContent = 'Select a contract to review';
}

/**
 * Loads the Delaware sample contract from /sample_contract.txt
 * so users can test immediately without searching for files.
 */
async function loadSampleContract() {
  try {
    const res = await fetch('/sample_contract.txt');
    if (!res.ok) throw new Error('Failed to load sample contract');
    const text = await res.text();
    const file = new File([text], 'sample_agreement_delaware.txt', { type: 'text/plain' });
    setFile(file);
  } catch (err) {
    console.error('Error loading sample contract:', err);
    alert('Could not load sample contract. Please select a local file.');
  }
}

// Progress simulator for staged pipeline overlay
document.getElementById('upload-form').addEventListener('submit', function(e) {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.remove('hidden');
  }

  const detailEl = document.getElementById('loading-detail');
  const steps = [
    { id: 'step-1', text: 'Partitioning operative clause boundaries...' },
    { id: 'step-2', text: 'Extracting provisions & structured summaries...' },
    { id: 'step-3', text: 'Auditing premise entailment via DeBERTa-v3...' },
    { id: 'step-4', text: 'Benchmarking k-NN anomaly against CUAD index...' }
  ];

  let currentStep = 0;
  const interval = setInterval(() => {
    currentStep++;
    if (currentStep < steps.length) {
      document.querySelectorAll('.step-item').forEach(s => s.classList.remove('active'));
      const activeEl = document.getElementById(steps[currentStep].id);
      if (activeEl) activeEl.classList.add('active');
      if (detailEl) detailEl.textContent = steps[currentStep].text;
    } else {
      clearInterval(interval);
    }
  }, 2200);
});
