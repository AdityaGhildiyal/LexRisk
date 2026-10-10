// Clean Upload Interaction Script

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.add('drag-over');
}

function handleDragLeave(e) {
  document.getElementById('drop-zone').classList.remove('drag-over');
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) setFile(file);
}

function setFile(file) {
  const allowed = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain'
  ];
  if (!allowed.includes(file.type) && !file.name.match(/\.(pdf|docx|doc|txt)$/i)) {
    alert('Please select a PDF, DOCX, or TXT file.');
    return;
  }

  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-selected').classList.remove('hidden');
  document.getElementById('drop-zone').style.display = 'none';

  const btn = document.getElementById('submit-btn');
  btn.disabled = false;
  document.getElementById('btn-text').textContent = `Review Document (${file.name})`;

  const dt = new DataTransfer();
  dt.items.add(file);
  document.getElementById('contract-file').files = dt.files;
}

function clearFile() {
  document.getElementById('contract-file').value = '';
  document.getElementById('file-selected').classList.add('hidden');
  document.getElementById('drop-zone').style.display = 'block';
  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  document.getElementById('btn-text').textContent = 'Select a contract to review';
}

document.getElementById('upload-form').addEventListener('submit', function(e) {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.remove('hidden');
  }
});
