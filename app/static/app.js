const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
const outputSection = document.getElementById('output-section');
const outputTitle = document.getElementById('output-title');
const outputMeta = document.getElementById('output-meta');
const outputContent = document.getElementById('output-content');
const warningBox = document.getElementById('warning');
const downloadButton = document.getElementById('download-docx');
let latestOutput = null;

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.remove('active'));
    panels.forEach((panel) => panel.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.target).classList.add('active');
  });
});

async function submitForm(form, endpoint) {
  const button = form.querySelector('button[type="submit"]');
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = 'Processing…';

  try {
    const response = await fetch(endpoint, { method: 'POST', body: new FormData(form) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'The request failed.');

    latestOutput = payload;
    outputTitle.textContent = payload.title;
    outputMeta.textContent = `${payload.source_filename} · ${payload.extracted_characters.toLocaleString()} extracted characters${payload.ai_enabled ? '' : ' · Development preview'}`;
    outputContent.textContent = payload.content_markdown;

    if (payload.extraction_warning) {
      warningBox.textContent = payload.extraction_warning;
      warningBox.classList.remove('hidden');
    } else {
      warningBox.classList.add('hidden');
    }

    outputSection.classList.remove('hidden');
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    window.alert(error.message);
  } finally {
    button.disabled = false;
    button.textContent = originalLabel;
  }
}

document.getElementById('lecture-form').addEventListener('submit', (event) => {
  event.preventDefault();
  submitForm(event.currentTarget, '/api/lecture-notes/generate');
});

document.getElementById('summary-form').addEventListener('submit', (event) => {
  event.preventDefault();
  submitForm(event.currentTarget, '/api/summaries/generate');
});

downloadButton.addEventListener('click', async () => {
  if (!latestOutput) return;
  downloadButton.disabled = true;
  const originalLabel = downloadButton.textContent;
  downloadButton.textContent = 'Preparing…';

  try {
    const response = await fetch('/api/exports/docx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: latestOutput.title,
        content_markdown: latestOutput.content_markdown,
      }),
    });
    if (!response.ok) throw new Error('DOCX export failed.');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${latestOutput.title.replace(/[^a-z0-9]+/gi, '_')}.docx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    window.alert(error.message);
  } finally {
    downloadButton.disabled = false;
    downloadButton.textContent = originalLabel;
  }
});
