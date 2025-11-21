const drop = document.getElementById('drop');
const filesInput = document.getElementById('files');
const runBtn = document.getElementById('run');
const statusEl = document.getElementById('status');

function gatherConfig() {
  const form = new FormData(document.getElementById('cfg'));
  return form;
}

function captureFiles() {
  const dtFiles = filesInput.files;
  return Array.from(dtFiles);
}

drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('hover'); });
drop.addEventListener('dragleave', e => { drop.classList.remove('hover'); });
drop.addEventListener('drop', e => {
  e.preventDefault();
  drop.classList.remove('hover');
  const items = e.dataTransfer.items;
  const files = [];
  for (const it of items) {
    if (it.kind === 'file') files.push(it.getAsFile());
  }
  const dt = new DataTransfer();
  for (const f of files) dt.items.add(f);
  filesInput.files = dt.files;
});

drop.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') {
    filesInput.click();
    e.preventDefault();
  }
});

async function optimize() {
  statusEl.textContent = 'Processando...';
  const cfg = gatherConfig();
  const files = captureFiles();
  const form = new FormData();
  for (const [k, v] of cfg.entries()) form.append(k, v);
  for (const f of files) form.append('files', f, f.name);
  runBtn.disabled = true;
  runBtn.setAttribute('aria-busy', 'true');
  document.querySelector('.progress')?.classList.add('active');
  const res = await fetch('/api/optimize', { method: 'POST', body: form });
  if (!res.ok) {
    statusEl.textContent = 'Falha ao otimizar';
    runBtn.disabled = false;
    runBtn.removeAttribute('aria-busy');
    return;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'optimized.zip';
  a.textContent = 'Baixar ZIP';
  statusEl.innerHTML = '';
  statusEl.appendChild(a);
  runBtn.disabled = false;
  runBtn.removeAttribute('aria-busy');
}

runBtn.addEventListener('click', optimize);

const previewBtn = document.getElementById('preview');
previewBtn.addEventListener('click', async () => {
  const files = captureFiles();
  if (!files.length) {
    statusEl.textContent = 'Selecione um arquivo para preview';
    return;
  }
  const form = new FormData(document.getElementById('cfg'));
  form.append('file', files[0], files[0].name);
  statusEl.textContent = 'Calculando preview...';
  const res = await fetch('/api/preview', { method: 'POST', body: form });
  if (!res.ok) { statusEl.textContent = 'Falha no preview'; return; }
  const data = await res.json();
  const fmt = (b) => {
    if (b < 1024) return `${b} bytes`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(2)} KB`;
    return `${(b / (1024 * 1024)).toFixed(2)} MB`;
  };
  statusEl.textContent = `Original: ${fmt(data.original_size)}\nEstimado: ${fmt(data.estimated_new_size)}\nRedução: ${data.percent_saved}%`;
});