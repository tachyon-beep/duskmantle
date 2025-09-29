(function () {
  const scope = document.querySelector('[data-dm-scope="layout"]');
  if (!scope) {
    return;
  }

  const state = {
    readerToken: sessionStorage.getItem('dm.readerToken') || '',
    maintainerToken: sessionStorage.getItem('dm.maintainerToken') || '',
    active: (document.querySelector('[data-dm-nav-link].is-active') || {}).dataset?.dmNavLink || 'home',
  };

  const modal = scope.querySelector('[data-dm-modal]');
  const readerInput = scope.querySelector('[data-dm-reader-token]');
  const maintainerInput = scope.querySelector('[data-dm-maintainer-token]');
  const requestIdEl = scope.querySelector('[data-dm-request-id]');
  const statusEl = scope.querySelector('[data-dm-search-status]');
  const resultsSection = scope.querySelector('[data-dm-search-results]');
  const resultsList = scope.querySelector('[data-dm-search-list]');
  const feedbackEl = scope.querySelector('[data-dm-search-feedback]');

  function syncInputs() {
    if (readerInput) readerInput.value = state.readerToken;
    if (maintainerInput) maintainerInput.value = state.maintainerToken;
  }

  function openModal() {
    if (!modal) return;
    modal.dataset.open = 'true';
    modal.removeAttribute('hidden');
    syncInputs();
    (readerInput || maintainerInput)?.focus();
  }

  function closeModal() {
    if (!modal) return;
    modal.dataset.open = 'false';
    modal.setAttribute('hidden', 'hidden');
  }

  scope.querySelectorAll('[data-dm-open-tokens]').forEach((btn) => {
    btn.addEventListener('click', openModal);
  });

  scope.querySelectorAll('[data-dm-close-tokens]').forEach((btn) => {
    btn.addEventListener('click', closeModal);
  });

  const saveBtn = scope.querySelector('[data-dm-save-tokens]');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      state.readerToken = (readerInput?.value || '').trim();
      state.maintainerToken = (maintainerInput?.value || '').trim();
      sessionStorage.setItem('dm.readerToken', state.readerToken);
      sessionStorage.setItem('dm.maintainerToken', state.maintainerToken);
      updateStatus();
      closeModal();
    });
  }

  const clearBtn = scope.querySelector('[data-dm-clear-tokens]');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      state.readerToken = '';
      state.maintainerToken = '';
      sessionStorage.removeItem('dm.readerToken');
      sessionStorage.removeItem('dm.maintainerToken');
      syncInputs();
      updateStatus();
    });
  }

  scope.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal?.dataset.open === 'true') {
      closeModal();
    }
  });

  function updateNav() {
    const links = scope.querySelectorAll('[data-dm-nav-link]');
    links.forEach((link) => {
      if (link.dataset.dmNavLink === state.active) {
        link.classList.add('is-active');
      } else {
        link.classList.remove('is-active');
      }
    });
  }

  function updateStatus(text) {
    if (!statusEl) return;
    if (text) {
      statusEl.textContent = text;
      return;
    }
    if (state.readerToken || state.maintainerToken) {
      statusEl.textContent = 'Ready. Queries will use the reader token if available.';
    } else {
      statusEl.textContent = 'Provide a reader token before querying.';
    }
  }

  function authHeader(scopeHint) {
    const token = scopeHint === 'maintainer'
      ? (state.maintainerToken || state.readerToken)
      : (state.readerToken || state.maintainerToken);
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  }

  async function performSearch(formData) {
    const query = formData.get('query');
    const limit = Number(formData.get('limit') || 5);
    const includeGraph = formData.get('include_graph') === 'on';

    if (!query || !(state.readerToken || state.maintainerToken)) {
      updateStatus('Query and token required.');
      return;
    }

    updateStatus('Running search…');
    if (feedbackEl) feedbackEl.textContent = '';
    if (resultsSection) resultsSection.hidden = true;

    const body = {
      query,
      limit,
      include_graph: includeGraph,
    };

    const headers = {
      'Content-Type': 'application/json',
      ...authHeader('reader'),
    };

    try {
      const response = await fetch('/search', {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });

      const requestId = response.headers.get('x-request-id');
      if (requestId && requestIdEl) {
        requestIdEl.textContent = requestId;
      }

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const message = detail?.detail || 'Search failed';
        updateStatus(message);
        if (feedbackEl) {
          feedbackEl.textContent = message;
          feedbackEl.classList.add('dm-alert-error');
        }
        return;
      }

      const payload = await response.json();
      renderResults(payload);
      updateStatus(`Found ${payload.results?.length || 0} match(es).`);
    } catch (error) {
      console.error('Search request failed', error);
      updateStatus('Unable to reach the gateway. Check container logs.');
    }
  }

  function renderResults(payload) {
    if (!resultsSection || !resultsList) return;
    resultsList.innerHTML = '';

    const results = payload?.results || [];
    results.forEach((entry) => {
      const li = document.createElement('li');
      li.className = 'dm-result__item';

      const title = document.createElement('h4');
      title.textContent = entry?.chunk?.title || entry?.chunk?.path || 'Untitled result';
      li.appendChild(title);

      if (entry?.chunk?.snippet) {
        const snippet = document.createElement('p');
        snippet.textContent = entry.chunk.snippet;
        li.appendChild(snippet);
      }

      const meta = document.createElement('div');
      meta.className = 'dm-result__meta';

      if (entry?.chunk?.path) {
        meta.appendChild(textTag('Path', entry.chunk.path));
      }

      if (entry?.graph_context?.subsystem) {
        meta.appendChild(textTag('Subsystem', entry.graph_context.subsystem));
      }

      const scoring = entry?.scoring || {};
      if (typeof scoring.vector_score === 'number') {
        meta.appendChild(textTag('Vector', scoring.vector_score.toFixed(4)));
      }
      if (typeof scoring.lexical_score === 'number') {
        meta.appendChild(textTag('Lexical', scoring.lexical_score.toFixed(4)));
      }
      if (typeof scoring.adjusted_score === 'number') {
        meta.appendChild(textTag('Adjusted', scoring.adjusted_score.toFixed(4)));
      }

      li.appendChild(meta);
      resultsList.appendChild(li);
    });

    const feedbackPrompt = payload?.metadata?.feedback_prompt;
    if (feedbackEl) {
      feedbackEl.textContent = feedbackPrompt || '';
      feedbackEl.classList.toggle('dm-alert-error', false);
      feedbackEl.hidden = !feedbackPrompt;
    }

    resultsSection.hidden = false;
  }

  function textTag(label, value) {
    const el = document.createElement('span');
    el.textContent = `${label}: ${value}`;
    return el;
  }

  const form = document.getElementById('dm-search-form');
  if (form) {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      performSearch(formData);
    });
  }

  function initialiseActiveNav() {
    const current = window.location.pathname.replace(/\/$/, '');
    if (current.endsWith('/ui/search')) {
      state.active = 'search';
    } else if (current.endsWith('/ui/subsystems')) {
      state.active = 'subsystems';
    } else if (current.endsWith('/ui/lifecycle')) {
      state.active = 'lifecycle';
    } else {
      state.active = 'home';
    }
    updateNav();
  }

  initialiseActiveNav();
  updateStatus();
  syncInputs();
})();
