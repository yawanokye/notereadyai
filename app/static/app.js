const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
const outputSection = document.getElementById('output-section');
const outputTitle = document.getElementById('output-title');
const outputMeta = document.getElementById('output-meta');
const outputContent = document.getElementById('output-content');
const warningBox = document.getElementById('warning');
const unitStatus = document.getElementById('unit-status');
const downloadButton = document.getElementById('download-docx');
const unitList = document.getElementById('unit-list');
const practiceContent = document.getElementById('practice-content');
const progressBar = document.getElementById('progress-bar');
const statusText = document.getElementById('status-text');
const statusCount = document.getElementById('status-count');
const generationStatus = document.getElementById('generation-status');
const answerKeyOption = document.getElementById('answer-key-option');
const includeAnswerKey = document.getElementById('include-answer-key');
const notesTab = document.getElementById('notes-tab');
const practiceTab = document.getElementById('practice-tab');
const notesView = document.getElementById('notes-view');
const practiceView = document.getElementById('practice-view');
const previousUnit = document.getElementById('previous-unit');
const nextUnit = document.getElementById('next-unit');
const unitPosition = document.getElementById('unit-position');
const fullscreenButton = document.getElementById('fullscreen-button');
const toast = document.getElementById('toast');

const state = {
  mode: null,
  title: '',
  sourceFilename: '',
  jobId: null,
  modules: [],
  batches: new Map(),
  statuses: new Map(),
  activeIndex: 0,
  fontSize: 17,
};

let toastTimer = null;

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove('hidden');
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.add('hidden'), 4500);
}

function resetState() {
  state.mode = null;
  state.title = '';
  state.sourceFilename = '';
  state.jobId = null;
  state.modules = [];
  state.batches = new Map();
  state.statuses = new Map();
  state.activeIndex = 0;
  unitList.innerHTML = '';
  outputContent.innerHTML = '';
  practiceContent.innerHTML = '';
  generationStatus.classList.add('hidden');
  warningBox.classList.add('hidden');
  answerKeyOption.classList.add('hidden');
  switchReaderView('notes');
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.remove('active'));
    panels.forEach((panel) => panel.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.target).classList.add('active');
  });
});

function switchReaderView(view) {
  const practice = view === 'practice';
  notesTab.classList.toggle('active', !practice);
  practiceTab.classList.toggle('active', practice);
  notesView.classList.toggle('active', !practice);
  practiceView.classList.toggle('active', practice);
}

notesTab.addEventListener('click', () => switchReaderView('notes'));
practiceTab.addEventListener('click', () => switchReaderView('practice'));

function updateProgress(completed, total, label) {
  const percentage = total ? Math.round((completed / total) * 100) : 0;
  statusText.textContent = label;
  statusCount.textContent = `${percentage}%`;
  progressBar.style.width = `${percentage}%`;
}

function renderUnitList() {
  unitList.innerHTML = '';
  state.modules.forEach((module, index) => {
    const button = document.createElement('button');
    const status = state.statuses.get(module.id) || 'pending';
    button.type = 'button';
    button.className = `unit-button ${status} ${index === state.activeIndex ? 'active' : ''}`;
    button.innerHTML = `
      <span class="unit-number">${index + 1}</span>
      <span class="unit-name"></span>
      <span class="unit-indicator" aria-hidden="true"></span>
    `;
    button.querySelector('.unit-name').textContent = module.title;
    button.addEventListener('click', () => {
      state.activeIndex = index;
      renderUnitList();
      renderActiveUnit();
    });
    unitList.appendChild(button);
  });
}

function wrapTables(container) {
  container.querySelectorAll('table').forEach((table) => {
    if (table.parentElement?.classList.contains('table-scroll')) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'table-scroll';
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
  });
}

function renderActiveUnit() {
  const module = state.modules[state.activeIndex];
  if (!module) return;

  renderUnitList();
  const batch = state.batches.get(module.id);
  const status = state.statuses.get(module.id) || 'pending';
  unitPosition.textContent = `Unit ${state.activeIndex + 1} of ${state.modules.length}`;
  previousUnit.disabled = state.activeIndex <= 0;
  nextUnit.disabled = state.activeIndex >= state.modules.length - 1;

  if (batch) {
    unitStatus.classList.add('hidden');
    outputContent.innerHTML = batch.content_html;
    wrapTables(outputContent);
    renderPractice(batch);
    if (batch.assessment_warning) {
      showToast(batch.assessment_warning);
    }
  } else {
    outputContent.innerHTML = '';
    practiceContent.innerHTML = '<div class="empty-practice">Practice questions appear when this unit is ready.</div>';
    unitStatus.classList.remove('hidden');
    if (status === 'generating') {
      unitStatus.textContent = `Generating “${module.title}”…`;
    } else if (status === 'failed') {
      unitStatus.textContent = `This unit could not be generated. Select it again after restarting the course generation.`;
    } else {
      unitStatus.textContent = `“${module.title}” is waiting in the generation queue.`;
    }
  }
  outputContent.scrollTop = 0;
}

function renderPractice(batch) {
  const questions = batch.objective_questions || [];
  const essays = batch.essay_questions || [];
  if (!questions.length && !essays.length) {
    practiceContent.innerHTML = '<div class="empty-practice">No practice questions were returned for this unit.</div>';
    return;
  }

  practiceContent.innerHTML = '';
  const heading = document.createElement('div');
  heading.innerHTML = `
    <h2>${escapeHtml(batch.title)} Practice</h2>
    <p class="practice-intro">Answer the objective questions and submit to see your score, correct answers and explanations. Essay marking guides can be revealed after you plan your response.</p>
  `;
  practiceContent.appendChild(heading);

  const form = document.createElement('form');
  form.className = 'quiz-form';
  questions.forEach((question, questionIndex) => {
    const card = document.createElement('section');
    card.className = 'question-card';
    const prompt = document.createElement('p');
    prompt.className = 'question-number';
    prompt.textContent = `${questionIndex + 1}. ${question.question}`;
    card.appendChild(prompt);

    question.options.forEach((option, optionIndex) => {
      const label = document.createElement('label');
      label.className = 'option-label';
      label.dataset.optionIndex = String(optionIndex);
      const input = document.createElement('input');
      input.type = 'radio';
      input.name = question.id;
      input.value = String(optionIndex);
      const text = document.createElement('span');
      text.textContent = `${String.fromCharCode(65 + optionIndex)}. ${option}`;
      label.append(input, text);
      card.appendChild(label);
    });
    form.appendChild(card);
  });

  if (questions.length) {
    const actions = document.createElement('div');
    actions.className = 'quiz-actions';
    const submit = document.createElement('button');
    submit.className = 'secondary';
    submit.type = 'submit';
    submit.textContent = 'Submit objective test';
    const score = document.createElement('div');
    score.className = 'quiz-score';
    actions.append(submit, score);
    form.appendChild(actions);

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      let correct = 0;
      questions.forEach((question, questionIndex) => {
        const card = form.querySelectorAll('.question-card')[questionIndex];
        const selected = form.querySelector(`input[name="${cssEscape(question.id)}"]:checked`);
        const selectedIndex = selected ? Number(selected.value) : -1;
        if (selectedIndex === question.correct_index) correct += 1;

        card.querySelectorAll('.option-label').forEach((label) => {
          const index = Number(label.dataset.optionIndex);
          label.classList.remove('correct', 'incorrect');
          if (index === question.correct_index) label.classList.add('correct');
          if (index === selectedIndex && selectedIndex !== question.correct_index) label.classList.add('incorrect');
        });

        let feedback = card.querySelector('.question-feedback');
        if (!feedback) {
          feedback = document.createElement('div');
          feedback.className = 'question-feedback';
          card.appendChild(feedback);
        }
        const answerLetter = String.fromCharCode(65 + question.correct_index);
        feedback.textContent = `Correct answer: ${answerLetter}. ${question.explanation}`;
      });
      const percentage = Math.round((correct / questions.length) * 100);
      score.textContent = `Score: ${correct}/${questions.length} (${percentage}%)`;
      score.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }
  practiceContent.appendChild(form);

  if (essays.length) {
    const essayHeading = document.createElement('h2');
    essayHeading.textContent = 'Essay Questions';
    practiceContent.appendChild(essayHeading);
    essays.forEach((essay, index) => {
      const card = document.createElement('section');
      card.className = 'essay-card';
      const question = document.createElement('h4');
      question.textContent = `${index + 1}. ${essay.question}`;
      const reveal = document.createElement('button');
      reveal.type = 'button';
      reveal.className = 'secondary ghost';
      reveal.textContent = 'Show marking guide';
      const guide = document.createElement('div');
      guide.className = 'marking-guide hidden';
      const list = document.createElement('ul');
      essay.marking_points.forEach((point) => {
        const item = document.createElement('li');
        item.textContent = point;
        list.appendChild(item);
      });
      guide.appendChild(list);
      reveal.addEventListener('click', () => {
        const hidden = guide.classList.toggle('hidden');
        reveal.textContent = hidden ? 'Show marking guide' : 'Hide marking guide';
      });
      card.append(question, reveal, guide);
      practiceContent.appendChild(card);
    });
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
  }[character]));
}

function cssEscape(value) {
  if (window.CSS?.escape) return CSS.escape(value);
  return String(value).replace(/[^a-zA-Z0-9_-]/g, '\\$&');
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }
  if (!response.ok) throw new Error(payload.detail || 'The request failed.');
  return payload;
}

async function startLectureGeneration(form) {
  resetState();
  state.mode = 'lecture';
  const button = form.querySelector('button[type="submit"]');
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = 'Analysing course outline…';

  try {
    const job = await requestJson('/api/lecture-notes/jobs', {
      method: 'POST',
      body: new FormData(form),
    });
    state.jobId = job.job_id;
    state.title = job.title;
    state.sourceFilename = job.source_filename;
    state.modules = job.modules;
    state.modules.forEach((module) => state.statuses.set(module.id, 'pending'));
    outputTitle.textContent = job.title;
    outputMeta.textContent = `${job.source_filename} · ${job.extracted_characters.toLocaleString()} extracted characters · ${job.modules.length} course units${job.ai_enabled ? '' : ' · Development preview'}`;
    if (job.extraction_warning) {
      warningBox.textContent = job.extraction_warning;
      warningBox.classList.remove('hidden');
    }
    answerKeyOption.classList.remove('hidden');
    generationStatus.classList.remove('hidden');
    outputSection.classList.remove('hidden');
    renderUnitList();
    renderActiveUnit();
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    updateProgress(0, state.modules.length, 'Course units identified. Starting Unit 1…');

    let completed = 0;
    for (let index = 0; index < state.modules.length; index += 1) {
      const module = state.modules[index];
      state.statuses.set(module.id, 'generating');
      if (index === 0 || state.activeIndex === index) {
        state.activeIndex = index;
        renderActiveUnit();
      } else {
        renderUnitList();
      }
      updateProgress(completed, state.modules.length, `Generating Unit ${index + 1}: ${module.title}`);

      try {
        const batch = await requestJson(`/api/lecture-notes/jobs/${state.jobId}/batches/${module.id}`, {
          method: 'POST',
        });
        state.batches.set(module.id, batch);
        state.statuses.set(module.id, 'ready');
        completed += 1;
        renderUnitList();
        if (index === 0 || state.activeIndex === index) renderActiveUnit();
        updateProgress(completed, state.modules.length, `${completed} of ${state.modules.length} units ready`);
      } catch (error) {
        state.statuses.set(module.id, 'failed');
        renderUnitList();
        showToast(`${module.title}: ${error.message}`);
      }
    }

    const failed = state.modules.filter((module) => state.statuses.get(module.id) === 'failed').length;
    if (failed) {
      updateProgress(completed, state.modules.length, `${completed} units ready. ${failed} unit${failed === 1 ? '' : 's'} failed.`);
    } else {
      updateProgress(completed, state.modules.length, 'All course units are ready.');
      showToast('The complete course is ready for reading, practice and DOCX export.');
    }
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = originalLabel;
  }
}

async function generateSummary(form) {
  resetState();
  state.mode = 'summary';
  const button = form.querySelector('button[type="submit"]');
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = 'Preparing summary…';

  try {
    const payload = await requestJson('/api/summaries/generate', {
      method: 'POST',
      body: new FormData(form),
    });
    const module = { id: 'summary', sequence: 1, title: payload.title };
    state.title = payload.title;
    state.sourceFilename = payload.source_filename;
    state.modules = [module];
    state.statuses.set(module.id, 'ready');
    state.batches.set(module.id, {
      title: payload.title,
      content_markdown: payload.content_markdown,
      content_html: payload.content_html,
      objective_questions: [],
      essay_questions: [],
    });
    outputTitle.textContent = payload.title;
    outputMeta.textContent = `${payload.source_filename} · ${payload.extracted_characters.toLocaleString()} extracted characters${payload.ai_enabled ? '' : ' · Development preview'}`;
    if (payload.extraction_warning) {
      warningBox.textContent = payload.extraction_warning;
      warningBox.classList.remove('hidden');
    }
    outputSection.classList.remove('hidden');
    renderUnitList();
    renderActiveUnit();
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = originalLabel;
  }
}

document.getElementById('lecture-form').addEventListener('submit', (event) => {
  event.preventDefault();
  startLectureGeneration(event.currentTarget);
});

document.getElementById('summary-form').addEventListener('submit', (event) => {
  event.preventDefault();
  generateSummary(event.currentTarget);
});

previousUnit.addEventListener('click', () => {
  if (state.activeIndex > 0) {
    state.activeIndex -= 1;
    renderActiveUnit();
  }
});

nextUnit.addEventListener('click', () => {
  if (state.activeIndex < state.modules.length - 1) {
    state.activeIndex += 1;
    renderActiveUnit();
  }
});

document.getElementById('font-down').addEventListener('click', () => {
  state.fontSize = Math.max(14, state.fontSize - 1);
  document.documentElement.style.setProperty('--reader-size', `${state.fontSize}px`);
});

document.getElementById('font-up').addEventListener('click', () => {
  state.fontSize = Math.min(23, state.fontSize + 1);
  document.documentElement.style.setProperty('--reader-size', `${state.fontSize}px`);
});

fullscreenButton.addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else {
      await outputSection.requestFullscreen();
    }
  } catch {
    showToast('Full-screen mode is not available in this browser.');
  }
});

document.addEventListener('fullscreenchange', () => {
  fullscreenButton.textContent = document.fullscreenElement ? 'Exit full screen' : 'Full screen';
});

function buildExportMarkdown() {
  const parts = [];
  state.modules.forEach((module) => {
    const batch = state.batches.get(module.id);
    if (!batch) return;
    parts.push(batch.content_markdown);
    if (includeAnswerKey.checked && batch.objective_questions?.length) {
      parts.push(`## Answer Key: ${module.title}`);
      batch.objective_questions.forEach((question, index) => {
        const letter = String.fromCharCode(65 + question.correct_index);
        parts.push(`${index + 1}. **${letter}** — ${question.explanation}`);
      });
      if (batch.essay_questions?.length) {
        parts.push('### Essay Marking Guides');
        batch.essay_questions.forEach((essay, index) => {
          parts.push(`${index + 1}. ${essay.question}`);
          essay.marking_points.forEach((point) => parts.push(`   - ${point}`));
        });
      }
    }
  });
  return parts.join('\n\n');
}

downloadButton.addEventListener('click', async () => {
  if (!state.batches.size) return;
  downloadButton.disabled = true;
  const originalLabel = downloadButton.textContent;
  downloadButton.textContent = 'Preparing DOCX…';
  try {
    const response = await fetch('/api/exports/docx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: state.title,
        content_markdown: buildExportMarkdown(),
      }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || 'DOCX export failed.');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${state.title.replace(/[^a-z0-9]+/gi, '_')}.docx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    showToast(error.message);
  } finally {
    downloadButton.disabled = false;
    downloadButton.textContent = originalLabel;
  }
});
