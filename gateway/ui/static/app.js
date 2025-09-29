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
  let lifecycleLoaded = false;
  let lastSearchPayload = null;
  let lastSearchParams = null;
  let lastSubsystemPayload = null;
  let lastSubsystemParams = null;

  const modal = scope.querySelector('[data-dm-modal]');
  const readerInput = scope.querySelector('[data-dm-reader-token]');
  const maintainerInput = scope.querySelector('[data-dm-maintainer-token]');
  const requestIdEl = scope.querySelector('[data-dm-request-id]');
  const statusEl = scope.querySelector('[data-dm-search-status]');
  const resultsSection = scope.querySelector('[data-dm-search-results]');
  const resultsList = scope.querySelector('[data-dm-search-list]');
  const feedbackEl = scope.querySelector('[data-dm-search-feedback]');
  const searchActions = scope.querySelector('[data-dm-search-actions]');
  const searchCopyBtn = scope.querySelector('[data-dm-search-copy]');
  const searchDownloadBtn = scope.querySelector('[data-dm-search-download]');

  const subsystemStatus = scope.querySelector('[data-dm-subsystem-status]');
  const subsystemPanel = scope.querySelector('[data-dm-subsystem-panel]');
  const subsystemTitle = scope.querySelector('[data-dm-subsystem-title]');
  const subsystemHops = scope.querySelector('[data-dm-subsystem-hops]');
  const subsystemSummary = scope.querySelector('[data-dm-subsystem-summary]');
  const subsystemArtifacts = scope.querySelector('[data-dm-subsystem-artifacts]');
  const subsystemRelatedTable = scope.querySelector('[data-dm-subsystem-related] tbody');
  const subsystemError = scope.querySelector('[data-dm-subsystem-error]');
  const subsystemActions = scope.querySelector('[data-dm-subsystem-actions]');
  const subsystemCopyBtn = scope.querySelector('[data-dm-subsystem-copy]');
  const subsystemDownloadBtn = scope.querySelector('[data-dm-subsystem-download]');

  const lifecycleRoot = scope.querySelector('[data-dm-lifecycle-root]');
  const lifecycleStatus = scope.querySelector('[data-dm-lifecycle-status]');
  const lifecycleGenerated = scope.querySelector('[data-dm-lifecycle-generated]');
  const lifecycleSummary = scope.querySelector('[data-dm-lifecycle-summary]');
  const lifecyclePanels = scope.querySelector('[data-dm-lifecycle-panels]');
  const lifecycleStaleTable = scope.querySelector('[data-dm-lifecycle-stale] tbody');
  const lifecycleIsolatedTable = scope.querySelector('[data-dm-lifecycle-isolated] tbody');
  const lifecycleMissingTable = scope.querySelector('[data-dm-lifecycle-missing] tbody');
  const lifecycleRemovedTable = scope.querySelector('[data-dm-lifecycle-removed] tbody');
  const lifecycleRefreshBtn = scope.querySelector('[data-dm-lifecycle-refresh]');
  const lifecycleDownloadBtn = scope.querySelector('[data-dm-lifecycle-download]');
  const recipeReleaseBtn = scope.querySelector('[data-dm-recipe-release]');
  const recipeStaleBtn = scope.querySelector('[data-dm-recipe-stale]');

  const lifecycleEnabled = lifecycleRoot ? lifecycleRoot.dataset.reportEnabled === 'true' : false;
  const lifecycleMetricMap = new Map();
  scope.querySelectorAll('[data-metric]').forEach((metricEl) => {
    const key = metricEl.dataset.metric;
    if (!key) return;
    lifecycleMetricMap.set(key, {
      valueEl: metricEl.querySelector('.dm-metric__value'),
      sparkEl: metricEl.querySelector('[data-dm-lifecycle-spark]'),
    });
  });

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
      refreshTokenPrompts();
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
      refreshTokenPrompts();
    });
  }

  scope.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal?.dataset.open === 'true') {
      closeModal();
    }
  });

  function hasToken() {
    return Boolean(state.readerToken || state.maintainerToken);
  }

  function refreshTokenPrompts() {
    updateStatus();
    updateSubsystemStatus();
    maybeAutoLoadLifecycle();
  }

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
    if (hasToken()) {
      statusEl.textContent = 'Ready. Queries will use the reader token if available.';
    } else {
      statusEl.textContent = 'Provide a reader token before querying.';
    }
  }

  function authHeader(scopeHint) {
    if (scopeHint === 'maintainer') {
      if (state.maintainerToken) {
        return { Authorization: `Bearer ${state.maintainerToken}` };
      }
      if (state.readerToken) {
        return { Authorization: `Bearer ${state.readerToken}` };
      }
      return {};
    }
    const token = state.readerToken || state.maintainerToken;
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  }

  async function recordUiEvent(eventName, extra) {
    try {
      await fetch('/ui/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeader('maintainer'),
        },
        body: JSON.stringify({ event: eventName, ...extra }),
      });
    } catch (error) {
      console.debug('Failed to record UI event', error);
    }
  }

  async function performSearch(formData) {
    const query = formData.get('query');
    const limit = Number(formData.get('limit') || 5);
    const includeGraph = formData.get('include_graph') === 'on';

    if (!query || !hasToken()) {
      updateStatus('Query and token required.');
      return;
    }

    updateStatus('Running search…');
    if (feedbackEl) feedbackEl.textContent = '';
    if (resultsSection) resultsSection.hidden = true;
    if (searchActions) searchActions.hidden = true;

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
        void recordUiEvent('search_error', { error: message });
        if (feedbackEl) {
          feedbackEl.textContent = message;
          feedbackEl.classList.add('dm-alert-error');
        }
        return;
      }

      const payload = await response.json();
      lastSearchParams = { query, limit, includeGraph };
      lastSearchPayload = payload;
      renderResults(payload);
      if (searchActions) {
        searchActions.hidden = false;
      }
      updateStatus(`Found ${payload.results?.length || 0} match(es).`);
      void recordUiEvent('search_success', { params: lastSearchParams });
    } catch (error) {
      console.error('Search request failed', error);
      updateStatus('Unable to reach the gateway. Check container logs.');
      void recordUiEvent('search_error', { error: String(error) });
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

  function updateSubsystemStatus(text) {
    if (!subsystemStatus) return;
    if (text) {
      subsystemStatus.textContent = text;
      return;
    }
    if (hasToken()) {
      subsystemStatus.textContent = 'Ready. Provide a subsystem name to explore.';
    } else {
      subsystemStatus.textContent = 'Provide a reader token before exploring subsystems.';
    }
  }

  async function loadSubsystem(formData) {
    const name = (formData.get('name') || '').trim();
    const depth = Math.min(4, Math.max(1, Number(formData.get('depth') || 2)));
    const limit = Math.min(50, Math.max(1, Number(formData.get('limit') || 15)));
    const includeArtifacts = formData.get('include_artifacts') === 'on';

    if (!name) {
      updateSubsystemStatus('Subsystem name is required.');
      return;
    }
    if (!hasToken()) {
      updateSubsystemStatus('Reader token required to query subsystems.');
      return;
    }

    updateSubsystemStatus('Loading subsystem…');
    if (subsystemActions) subsystemActions.hidden = true;
    if (subsystemError) {
      subsystemError.hidden = true;
      subsystemError.textContent = '';
    }
    if (subsystemPanel) {
      subsystemPanel.hidden = true;
    }

    const params = new URLSearchParams({ depth: String(depth), limit: String(limit) });
    if (!includeArtifacts) {
      params.set('include_artifacts', 'false');
    }

    try {
      const response = await fetch(`/graph/subsystems/${encodeURIComponent(name)}?${params.toString()}`, {
        headers: authHeader('reader'),
      });
      const requestId = response.headers.get('x-request-id');
      if (requestId && requestIdEl) {
        requestIdEl.textContent = requestId;
      }

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const message = detail?.detail || 'Subsystem lookup failed';
        updateSubsystemStatus(message);
        void recordUiEvent('subsystem_error', { error: message });
        if (subsystemError) {
          subsystemError.hidden = false;
          subsystemError.textContent = message;
        }
        return;
      }

      const payload = await response.json();
      lastSubsystemParams = { name, depth, limit, includeArtifacts };
      lastSubsystemPayload = payload;
      renderSubsystem(payload);
      if (subsystemActions) { subsystemActions.hidden = false; }
      void recordUiEvent('subsystem_success', { params: lastSubsystemParams });
      const loaded = payload?.related?.nodes?.length || 0;
      const total = payload?.related?.total ?? loaded;
      const extra = payload?.related?.cursor ? ' (more available via API).' : '.';
      updateSubsystemStatus(`Loaded ${loaded} of ${total} related node(s)${extra}`);
    } catch (error) {
      console.error('Subsystem request failed', error);
      updateSubsystemStatus('Unable to reach the gateway. Check logs.');
      void recordUiEvent('subsystem_error', { error: String(error) });
    }
  }

  function renderSubsystem(payload) {
    if (!subsystemPanel) return;
    const subsystem = payload?.subsystem || {};
    const props = subsystem.properties || {};
    const name = props.name || props.title || subsystem.id || 'Subsystem';

    if (subsystemTitle) {
      subsystemTitle.textContent = name;
    }
    if (subsystemHops) {
      const total = payload?.related?.total ?? 0;
      if (total) {
        subsystemHops.textContent = `${total} related nodes`;
        subsystemHops.style.display = 'inline-flex';
      } else {
        subsystemHops.textContent = '';
        subsystemHops.style.display = 'none';
      }
    }

    if (subsystemSummary) {
      subsystemSummary.innerHTML = '';
      const added = new Set();
      const addDefinition = (label, value) => {
        if (value === undefined || value === null || value === '') return;
        const dt = document.createElement('dt');
        dt.textContent = label;
        const dd = document.createElement('dd');
        dd.textContent = String(value);
        subsystemSummary.append(dt, dd);
      };
      const formatKey = (key) => key.replace(/_/g, ' ').replace(/\w/g, (c) => c.toUpperCase());
      addDefinition('ID', subsystem.id);
      if (Array.isArray(subsystem.labels) && subsystem.labels.length) {
        addDefinition('Labels', subsystem.labels.join(', '));
      }
      const highlight = ['owner', 'owner_team', 'status', 'criticality', 'freshness_days', 'updated_at'];
      highlight.forEach((key) => {
        if (props[key] !== undefined) {
          addDefinition(formatKey(key), props[key]);
          added.add(key);
        }
      });
      Object.keys(props)
        .filter((key) => !added.has(key))
        .slice(0, 6)
        .forEach((key) => addDefinition(formatKey(key), props[key]));
    }

    if (subsystemArtifacts) {
      subsystemArtifacts.innerHTML = '';
      const artifacts = payload?.artifacts || [];
      if (!artifacts.length) {
        const li = document.createElement('li');
        li.textContent = 'No artifacts linked.';
        subsystemArtifacts.appendChild(li);
      } else {
        artifacts.forEach((artifact) => {
          const li = document.createElement('li');
          const aprops = artifact?.properties || {};
          li.textContent = aprops.path || aprops.title || artifact.id;
          subsystemArtifacts.appendChild(li);
        });
      }
    }

    if (subsystemRelatedTable) {
      subsystemRelatedTable.innerHTML = '';
      const related = payload?.related?.nodes || [];
      if (!related.length) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 4;
        cell.textContent = 'No related nodes at this depth.';
        row.appendChild(cell);
        subsystemRelatedTable.appendChild(row);
      } else {
        related.forEach((entry) => {
          const row = document.createElement('tr');
          const target = entry?.target || {};
          const tprops = target.properties || {};
          const nodeCell = document.createElement('td');
          nodeCell.textContent = tprops.name || tprops.title || target.id;
          row.appendChild(nodeCell);

          const relCell = document.createElement('td');
          relCell.textContent = entry?.relationship || '—';
          row.appendChild(relCell);

          const dirCell = document.createElement('td');
          dirCell.textContent = entry?.direction || 'OUT';
          row.appendChild(dirCell);

          const hopsCell = document.createElement('td');
          hopsCell.textContent = String(entry?.hops ?? '—');
          row.appendChild(hopsCell);

          subsystemRelatedTable.appendChild(row);
        });
      }
    }

    if (subsystemError) {
      subsystemError.hidden = true;
      subsystemError.textContent = '';
    }
    subsystemPanel.hidden = false;
  }

  function updateLifecycleStatus(text) {
    if (!lifecycleStatus) return;
    if (text) {
      lifecycleStatus.textContent = text;
      return;
    }
    if (!lifecycleRoot || !lifecycleEnabled) {
      lifecycleStatus.textContent = 'Lifecycle reporting is disabled for this deployment.';
      return;
    }
    if (state.maintainerToken) {
      lifecycleStatus.textContent = 'Ready. Use refresh to load lifecycle metrics.';
    } else if (hasToken()) {
      lifecycleStatus.textContent = 'Using reader token; maintainer features may be limited.';
    } else {
      lifecycleStatus.textContent = 'Provide a maintainer token before loading lifecycle metrics.';
    }
  }

  function formatNumber(value) {
    if (!Number.isFinite(value)) return '0';
    return new Intl.NumberFormat().format(value);
  }

  function formatDate(timestamp) {
    if (!timestamp) return '';
    const base = typeof timestamp === 'number' ? timestamp * 1000 : Number(timestamp);
    const date = Number.isFinite(base) ? new Date(base) : new Date(timestamp);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString();
  }

  function computeLifecycleCounts(payload) {
    const summary = payload?.summary || {};
    const staleDocs = Array.isArray(payload?.stale_docs) ? payload.stale_docs : [];
    const missingTests = Array.isArray(payload?.missing_tests) ? payload.missing_tests : [];
    const removedArtifacts = Array.isArray(payload?.removed_artifacts) ? payload.removed_artifacts : [];
    const isolatedMap = payload?.isolated || {};
    const isolatedCount = Object.values(isolatedMap).reduce((acc, nodes) => {
      if (Array.isArray(nodes)) {
        return acc + nodes.length;
      }
      return acc;
    }, 0);
    return {
      stale_docs: Number(summary.stale_docs ?? staleDocs.length) || 0,
      isolated_nodes: Number(summary.isolated_nodes ?? isolatedCount) || 0,
      subsystems_missing_tests: Number(summary.subsystems_missing_tests ?? missingTests.length) || 0,
      removed_artifacts: Number(summary.removed_artifacts ?? removedArtifacts.length) || 0,
    };
  }

  function renderLifecycle(payload) {
    if (!lifecycleRoot) return;
    const counts = computeLifecycleCounts(payload);

    if (lifecycleSummary) {
      lifecycleSummary.hidden = false;
    }
    lifecycleMetricMap.forEach((refs, key) => {
      const value = counts[key] ?? 0;
      if (refs?.valueEl) {
        refs.valueEl.textContent = formatNumber(value);
      }
    });

    if (lifecycleGenerated) {
      const generated = payload?.generated_at || payload?.generated_at_iso || payload?.timestamp;
      const formatted = formatDate(generated);
      if (formatted) {
        lifecycleGenerated.hidden = false;
        lifecycleGenerated.textContent = `Generated at ${formatted}`;
      } else {
        lifecycleGenerated.hidden = true;
      }
    }

    const generatedAt = typeof payload?.generated_at === 'number' ? payload.generated_at : null;
    const staleDocs = Array.isArray(payload?.stale_docs) ? payload.stale_docs : [];
    const isolatedMap = payload?.isolated || {};
    const isolatedEntries = [];
    Object.entries(isolatedMap).forEach(([label, nodes]) => {
      if (!Array.isArray(nodes)) return;
      nodes.forEach((node) => {
        isolatedEntries.push({ label, node });
      });
    });
    const missingTests = Array.isArray(payload?.missing_tests) ? payload.missing_tests : [];
    const removedArtifacts = Array.isArray(payload?.removed_artifacts) ? payload.removed_artifacts : [];

    const renderListTable = (table, rows, renderer, emptyColSpan = 1) => {
      if (!table) return;
      table.innerHTML = '';
      if (!rows.length) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        const span = emptyColSpan || (table.closest('table')?.querySelectorAll('thead th').length ?? 1);
        cell.colSpan = span;
        cell.textContent = 'No entries available.';
        row.appendChild(cell);
        table.appendChild(row);
        return;
      }
      rows.forEach((rowData) => {
        const row = document.createElement('tr');
        renderer(row, rowData);
        table.appendChild(row);
      });
    };

    renderListTable(lifecycleStaleTable, staleDocs, (row, doc) => {
      const path = doc?.path || doc?.properties?.path || doc?.id || 'Unknown';
      const subsystem = doc?.subsystem || doc?.metadata?.subsystem || doc?.properties?.subsystem || '—';
      let age = '—';
      const gitTimestamp = doc?.git_timestamp ?? doc?.properties?.git_timestamp;
      if (typeof gitTimestamp === 'number' && generatedAt) {
        age = Math.max(0, (generatedAt - gitTimestamp) / 86400).toFixed(1);
      }
      row.innerHTML = `<td>${path}</td><td>${subsystem}</td><td>${age}</td>`;
    }, 3);

    renderListTable(lifecycleIsolatedTable, isolatedEntries, (row, entry) => {
      const props = entry?.node?.properties || {};
      const label = props.name || props.title || entry?.node?.id || 'Node';
      const labels = Array.isArray(entry?.node?.labels) ? entry.node.labels.join(', ') : entry?.label || '—';
      row.innerHTML = `<td>${label}</td><td>${labels}</td>`;
    }, 2);

    renderListTable(lifecycleMissingTable, missingTests, (row, item) => {
      if (typeof item === 'string') {
        row.innerHTML = `<td>${item}</td><td>—</td>`;
        return;
      }
      const name = item?.name || item?.subsystem || item?.id || 'Subsystem';
      const note = item?.note || item?.reason || 'Needs test coverage';
      row.innerHTML = `<td>${name}</td><td>${note}</td>`;
    }, 2);

    renderListTable(lifecycleRemovedTable, removedArtifacts, (row, item) => {
      if (typeof item === 'string') {
        row.innerHTML = `<td>${item}</td><td>—</td>`;
        return;
      }
      const pathVal = item?.path || item?.id || item?.properties?.path || 'Artifact';
      const removedAt = item?.removed_at || item?.timestamp || item?.recorded_at || '—';
      row.innerHTML = `<td>${pathVal}</td><td>${removedAt}</td>`;
    }, 2);

    if (lifecyclePanels) {
      lifecyclePanels.hidden = false;
    }
  }

  async function loadLifecycleHistory() {
    if (!lifecycleRoot || !lifecycleEnabled) return;
    try {
      const response = await fetch('/lifecycle/history?limit=30', {
        headers: authHeader('maintainer'),
      });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      const history = Array.isArray(payload?.history) ? payload.history : [];
      renderLifecycleHistory(history);
    } catch (error) {
      console.error('Lifecycle history request failed', error);
    }
  }

  function renderLifecycleHistory(history) {
    const metrics = ['stale_docs', 'isolated_nodes', 'subsystems_missing_tests', 'removed_artifacts'];
    metrics.forEach((metric) => {
      const refs = lifecycleMetricMap.get(metric);
      if (!refs?.sparkEl) return;
      const values = history.map((entry) => Number(entry?.counts?.[metric] ?? 0));
      renderSparkline(values, refs.sparkEl);
    });
  }

  function renderSparkline(values, element) {
    if (!element) return;
    element.innerHTML = '';
    const cleaned = values.filter((value) => Number.isFinite(value));
    if (!cleaned.length) {
      element.textContent = '—';
      return;
    }
    const width = 80;
    const height = 24;
    const min = Math.min(...cleaned);
    const max = Math.max(...cleaned);
    const range = max - min || 1;
    const points = cleaned.map((value, index) => {
      const x = cleaned.length === 1 ? width / 2 : (index / (cleaned.length - 1)) * (width - 4) + 2;
      const y = height - ((value - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    }).join(' ');

    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    const polyline = document.createElementNS(svgNS, 'polyline');
    polyline.setAttribute('class', 'dm-spark-line');
    polyline.setAttribute('points', points);
    svg.appendChild(polyline);
    element.appendChild(svg);
  }

  function maybeAutoLoadLifecycle(force = false) {
    if (!lifecycleRoot) return;
    if (!lifecycleEnabled) {
      updateLifecycleStatus('Lifecycle reporting is disabled in settings.');
      return;
    }
    if (state.active === 'lifecycle') {
      if (!hasToken()) {
        updateLifecycleStatus('Provide a maintainer token before loading lifecycle metrics.');
        return;
      }
      if (force || !lifecycleLoaded) {
        void loadLifecycle();
      }
    }
  }

  async function loadLifecycle() {
    if (!lifecycleRoot || !lifecycleEnabled) {
      updateLifecycleStatus('Lifecycle reporting is disabled in settings.');
      return;
    }
    if (!hasToken()) {
      updateLifecycleStatus('Provide a maintainer token before loading lifecycle metrics.');
      return;
    }

    updateLifecycleStatus('Loading lifecycle metrics…');

    if (lifecycleSummary) {
      lifecycleSummary.hidden = true;
    }
    if (lifecyclePanels) {
      lifecyclePanels.hidden = true;
    }

    try {
      const response = await fetch('/lifecycle', {
        headers: authHeader('maintainer'),
      });
      const requestId = response.headers.get('x-request-id');
      if (requestId && requestIdEl) {
        requestIdEl.textContent = requestId;
      }

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const message = detail?.detail || 'Lifecycle report unavailable';
        updateLifecycleStatus(message);
        return;
      }

      const payload = await response.json();
      renderLifecycle(payload);
      await loadLifecycleHistory();
      lifecycleLoaded = true;
      updateLifecycleStatus(`Lifecycle metrics updated (${new Date().toLocaleTimeString()}).`);
    } catch (error) {
      console.error('Lifecycle request failed', error);
      updateLifecycleStatus('Unable to reach the gateway. Check logs.');
    }
  }
  if (lifecycleRefreshBtn) {
    lifecycleRefreshBtn.addEventListener('click', () => {
      lifecycleLoaded = false;
      void loadLifecycle();
    });
  }

  if (lifecycleDownloadBtn) {
    lifecycleDownloadBtn.addEventListener('click', async () => {
      if (!lifecycleEnabled) {
        updateLifecycleStatus('Lifecycle reporting is disabled in settings.');
        return;
      }
      if (!hasToken()) {
        updateLifecycleStatus('Provide a maintainer token before downloading lifecycle metrics.');
        return;
      }
      try {
        const response = await fetch('/ui/lifecycle/report', {
          headers: authHeader('maintainer'),
        });
        if (!response.ok) {
          const detail = await response.json().catch(() => ({}));
          const message = detail?.detail || 'Download failed';
          updateLifecycleStatus(message);
          return;
        }
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `lifecycle-${new Date().toISOString()}.json`;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
        updateLifecycleStatus('Lifecycle report downloaded.');
        void recordUiEvent('lifecycle_download');
      } catch (error) {
        console.error('Lifecycle download failed', error);
        updateLifecycleStatus('Download failed. Check console for details.');
      }
    });
  }

  if (recipeReleaseBtn) {
    recipeReleaseBtn.addEventListener('click', () => {
      const command = 'km-recipe-run release-prep --var profile=release';
      navigator.clipboard.writeText(command).then(() => {
        updateLifecycleStatus('Copied release recipe command.');
        void recordUiEvent('recipe_copy_release');
      }).catch((error) => {
        console.error('Clipboard copy failed', error);
        updateLifecycleStatus('Clipboard copy failed.');
      });
    });
  }

  if (recipeStaleBtn) {
    recipeStaleBtn.addEventListener('click', () => {
      const command = 'km-recipe-run stale-audit';
      navigator.clipboard.writeText(command).then(() => {
        updateLifecycleStatus('Copied stale audit recipe command.');
        void recordUiEvent('recipe_copy_stale_audit');
      }).catch((error) => {
        console.error('Clipboard copy failed', error);
        updateLifecycleStatus('Clipboard copy failed.');
      });
    });
  }

  const searchForm = document.getElementById('dm-search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const formData = new FormData(searchForm);
      performSearch(formData);
    });
  }

  if (searchCopyBtn) {
    searchCopyBtn.addEventListener('click', () => {
      if (!lastSearchParams) {
        updateStatus('Run a search before copying the command.');
        return;
      }
      const payload = {
        query: lastSearchParams.query,
        limit: lastSearchParams.limit,
      };
      if (lastSearchParams.includeGraph === false) {
        payload.include_graph = false;
      }
      const command = `km-search ${JSON.stringify(payload)}`;
      navigator.clipboard.writeText(command).then(() => {
        updateStatus('Copied MCP command to clipboard.');
        void recordUiEvent('search_copy_command');
      }).catch((error) => {
        console.error('Clipboard copy failed', error);
        updateStatus('Clipboard copy failed.');
      });
    });
  }

  if (searchDownloadBtn) {
    searchDownloadBtn.addEventListener('click', () => {
      if (!lastSearchPayload) {
        updateStatus('Run a search before downloading results.');
        return;
      }
      const blob = new Blob([JSON.stringify(lastSearchPayload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `search-${Date.now()}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      updateStatus('Downloaded search results.');
      void recordUiEvent('search_download');
    });
  }

  if (subsystemCopyBtn) {
    subsystemCopyBtn.addEventListener('click', () => {
      if (!lastSubsystemParams) {
        updateSubsystemStatus('Load a subsystem before copying the command.');
        return;
      }
      const payload = {
        name: lastSubsystemParams.name,
        depth: lastSubsystemParams.depth,
        limit: lastSubsystemParams.limit,
      };
      if (!lastSubsystemParams.includeArtifacts) {
        payload.include_artifacts = false;
      }
      const command = `km-graph-subsystem ${JSON.stringify(payload)}`;
      navigator.clipboard.writeText(command).then(() => {
        updateSubsystemStatus('Copied MCP command to clipboard.');
        void recordUiEvent('subsystem_copy_command');
      }).catch((error) => {
        console.error('Clipboard copy failed', error);
        updateSubsystemStatus('Clipboard copy failed.');
      });
    });
  }

  if (subsystemDownloadBtn) {
    subsystemDownloadBtn.addEventListener('click', () => {
      if (!lastSubsystemPayload) {
        updateSubsystemStatus('Load a subsystem before downloading details.');
        return;
      }
      const blob = new Blob([JSON.stringify(lastSubsystemPayload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `subsystem-${(lastSubsystemParams?.name || 'subsystem')}-${Date.now()}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      updateSubsystemStatus('Downloaded subsystem details.');
      void recordUiEvent('subsystem_download');
    });
  }
  const subsystemForm = document.getElementById('dm-subsystem-form');
  if (subsystemForm) {
    subsystemForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const formData = new FormData(subsystemForm);
      loadSubsystem(formData);
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
  syncInputs();
  refreshTokenPrompts();
})();
