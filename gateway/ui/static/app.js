/* eslint-env browser */
/* global document, window, console, sessionStorage, fetch, navigator, Blob, URL, URLSearchParams, FormData, Intl */

(function () {
  const scope = document.querySelector('[data-dm-scope="layout"]');
  if (!scope) {
    return;
  }

  const body = document.body;
  const html = document.documentElement;

  const STRINGS = {
    search_ready: 'Ready. Queries will use the reader token if available.',
    search_need_token: 'Provide a reader token before querying.',
    search_running: 'Running search…',
    search_require_query_token: 'Query and token required.',
    search_error_auth: 'Access denied. Provide a reader token for search.',
    search_error_generic: 'Search failed. Check logs for details.',
    search_no_results: 'No results found.',
    search_before_copy: 'Run a search before copying the command.',
    search_copy_success: 'Copied MCP command to clipboard.',
    search_copy_failure: 'Clipboard copy failed.',
    search_before_download: 'Run a search before downloading results.',
    search_download_success: 'Downloaded search results.',

    subsystem_ready: 'Ready. Provide a subsystem name to explore.',
    subsystem_need_token: 'Provide a reader token before exploring subsystems.',
    subsystem_loading: 'Loading subsystem…',
    subsystem_error_auth: 'Access denied. Provide a reader token for subsystem lookups.',
    subsystem_error_generic: 'Subsystem lookup failed. Check logs for details.',
    subsystem_before_copy: 'Load a subsystem before copying the command.',
    subsystem_copy_success: 'Copied MCP command to clipboard.',
    subsystem_copy_failure: 'Clipboard copy failed.',
    subsystem_before_download: 'Load a subsystem before downloading details.',
    subsystem_download_success: 'Downloaded subsystem details.',

    lifecycle_disabled: 'Lifecycle reporting is disabled for this deployment.',
    lifecycle_need_token: 'Provide a maintainer token before loading lifecycle metrics.',
    lifecycle_ready: 'Ready. Use refresh to load lifecycle metrics.',
    lifecycle_reader_warning: 'Using reader token; maintainer features may be limited.',
    lifecycle_loading: 'Loading lifecycle metrics…',
    lifecycle_updated: 'Lifecycle metrics updated.',
    lifecycle_error_auth: 'Access denied. Provide a maintainer token for lifecycle metrics.',
    lifecycle_error_generic: 'Lifecycle report unavailable.',
    lifecycle_download_success: 'Lifecycle report downloaded.',
    lifecycle_download_failure: 'Download failed. Check console for details.',
    lifecycle_download_need_token: 'Provide a maintainer token before downloading lifecycle metrics.',
    lifecycle_history_failure: 'Unable to load lifecycle history.',
    lifecycle_recipe_release: 'Copied release prep recipe command.',
    lifecycle_recipe_stale: 'Copied stale audit recipe command.',

    tokens_saved: 'Tokens stored for this session.',
    tokens_cleared: 'Tokens cleared.',

    contrast_enable: 'Enable high contrast',
    contrast_disable: 'Disable high contrast',
    motion_enable: 'Reduce motion',
    motion_disable: 'Enable motion effects',
    clipboard_unavailable: 'Clipboard copy is unavailable in this browser.'
  };

  function t(key, fallback) {
    return STRINGS[key] || fallback || key;
  }

  const PREF_KEYS = {
    contrast: 'duskmantle.ui.contrast',
    motion: 'duskmantle.ui.motion'
  };

  function getPreference(key, fallback) {
    try {
      const value = window.localStorage.getItem(key);
      if (value === null) {
        return fallback;
      }
      return value === '1';
    } catch (error) {
      console.debug('Unable to access localStorage', error);
      return fallback;
    }
  }

  function setPreference(key, value) {
    try {
      window.localStorage.setItem(key, value ? '1' : '0');
    } catch (error) {
      console.debug('Unable to persist preference', error);
    }
  }

  const reduceMotionDefault = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const preferences = {
    contrast: getPreference(PREF_KEYS.contrast, false),
    motion: getPreference(PREF_KEYS.motion, reduceMotionDefault)
  };

  const state = {
    readerToken: sessionStorage.getItem('dm.readerToken') || '',
    maintainerToken: sessionStorage.getItem('dm.maintainerToken') || '',
    active: document.querySelector('[data-dm-nav-link].is-active')?.dataset?.dmNavLink ?? 'home'
  };
  let lastSearchPayload = null;
  let lastSearchParams = null;
  let lastSubsystemPayload = null;
  let lastSubsystemParams = null;

  const elements = {
    modal: scope.querySelector('[data-dm-modal]'),
    readerInput: scope.querySelector('[data-dm-reader-token]'),
    maintainerInput: scope.querySelector('[data-dm-maintainer-token]'),
    requestId: scope.querySelector('[data-dm-request-id]'),
    searchStatus: scope.querySelector('[data-dm-search-status]'),
    searchResults: scope.querySelector('[data-dm-search-results]'),
    searchList: scope.querySelector('[data-dm-search-list]'),
    searchFeedback: scope.querySelector('[data-dm-search-feedback]'),
    searchFilters: scope.querySelector('[data-dm-search-filters]'),
    searchActions: scope.querySelector('[data-dm-search-actions]'),
    searchCopy: scope.querySelector('[data-dm-search-copy]'),
    searchDownload: scope.querySelector('[data-dm-search-download]'),

    subsystemStatus: scope.querySelector('[data-dm-subsystem-status]'),
    subsystemPanel: scope.querySelector('[data-dm-subsystem-panel]'),
    subsystemTitle: scope.querySelector('[data-dm-subsystem-title]'),
    subsystemHops: scope.querySelector('[data-dm-subsystem-hops]'),
    subsystemSummary: scope.querySelector('[data-dm-subsystem-summary]'),
    subsystemArtifacts: scope.querySelector('[data-dm-subsystem-artifacts]'),
    subsystemTable: scope.querySelector('[data-dm-subsystem-related] tbody'),
    subsystemError: scope.querySelector('[data-dm-subsystem-error]'),
    subsystemActions: scope.querySelector('[data-dm-subsystem-actions]'),
    subsystemCopy: scope.querySelector('[data-dm-subsystem-copy]'),
    subsystemDownload: scope.querySelector('[data-dm-subsystem-download]'),

    lifecycleRoot: scope.querySelector('[data-dm-lifecycle-root]'),
    lifecycleStatus: scope.querySelector('[data-dm-lifecycle-status]'),
    lifecycleGenerated: scope.querySelector('[data-dm-lifecycle-generated]'),
    lifecycleSummary: scope.querySelector('[data-dm-lifecycle-summary]'),
    lifecyclePanels: scope.querySelector('[data-dm-lifecycle-panels]'),
    lifecycleStale: scope.querySelector('[data-dm-lifecycle-stale] tbody'),
    lifecycleIsolated: scope.querySelector('[data-dm-lifecycle-isolated] tbody'),
    lifecycleMissing: scope.querySelector('[data-dm-lifecycle-missing] tbody'),
    lifecycleSymbolPanel: scope.querySelector('[data-dm-lifecycle-symbol-panel]'),
    lifecycleSymbolTests: scope.querySelector('[data-dm-lifecycle-symbol-tests] tbody'),
    lifecycleRemoved: scope.querySelector('[data-dm-lifecycle-removed] tbody'),
    lifecycleRefresh: scope.querySelector('[data-dm-lifecycle-refresh]'),
    lifecycleDownload: scope.querySelector('[data-dm-lifecycle-download]'),
    recipeRelease: scope.querySelector('[data-dm-recipe-release]'),
    recipeStale: scope.querySelector('[data-dm-recipe-stale]'),

    contrastToggle: scope.querySelector('[data-dm-toggle-contrast]'),
    motionToggle: scope.querySelector('[data-dm-toggle-motion]'),
    openTokens: scope.querySelectorAll('[data-dm-open-tokens]'),
    closeTokens: scope.querySelectorAll('[data-dm-close-tokens]'),
    saveTokens: scope.querySelector('[data-dm-save-tokens]'),
    clearTokens: scope.querySelector('[data-dm-clear-tokens]')
  };

  const lifecycleEnabled = !!(elements.lifecycleRoot && elements.lifecycleRoot.dataset.reportEnabled === 'true');
  const lifecycleMetricMap = new Map();
  scope.querySelectorAll('[data-metric]').forEach((metricEl) => {
    const key = metricEl.dataset.metric;
    if (!key) {
      return;
    }
    lifecycleMetricMap.set(key, {
      containerEl: metricEl,
      valueEl: metricEl.querySelector('.dm-metric__value'),
      sparkEl: metricEl.querySelector('[data-dm-lifecycle-spark]')
    });
  });

  function applyPreferences() {
    body.classList.toggle('dm-theme-contrast', preferences.contrast);
    body.classList.toggle('dm-reduce-motion', preferences.motion);
    html.setAttribute('data-dm-contrast', preferences.contrast ? 'true' : 'false');
    html.setAttribute('data-dm-motion', preferences.motion ? 'reduced' : 'normal');

    if (elements.contrastToggle) {
      const enabled = preferences.contrast;
      elements.contrastToggle.setAttribute('aria-pressed', enabled ? 'true' : 'false');
      elements.contrastToggle.textContent = enabled ? t('contrast_disable', 'Disable high contrast') : t('contrast_enable', 'Enable high contrast');
    }
    if (elements.motionToggle) {
      const enabled = preferences.motion;
      elements.motionToggle.setAttribute('aria-pressed', enabled ? 'true' : 'false');
      elements.motionToggle.textContent = enabled ? t('motion_disable', 'Enable motion effects') : t('motion_enable', 'Reduce motion');
    }
  }

  applyPreferences();

  function syncInputs() {
    if (elements.readerInput) {
      elements.readerInput.value = state.readerToken;
    }
    if (elements.maintainerInput) {
      elements.maintainerInput.value = state.maintainerToken;
    }
  }

  function updateNav() {
    scope.querySelectorAll('[data-dm-nav-link]').forEach((link) => {
      if (link.dataset.dmNavLink === state.active) {
        link.classList.add('is-active');
        link.setAttribute('aria-current', 'page');
      } else {
        link.classList.remove('is-active');
        link.setAttribute('aria-current', 'false');
      }
    });
  }

  function updateStatus(message) {
    if (!elements.searchStatus) {
      return;
    }
    if (message) {
      elements.searchStatus.textContent = message;
      return;
    }
    elements.searchStatus.textContent = hasReader() ? t('search_ready') : t('search_need_token');
  }

  function updateSubsystemStatus(message) {
    if (!elements.subsystemStatus) {
      return;
    }
    if (message) {
      elements.subsystemStatus.textContent = message;
      return;
    }
    elements.subsystemStatus.textContent = hasReader() ? t('subsystem_ready') : t('subsystem_need_token');
  }

  function updateLifecycleStatus(message) {
    if (!elements.lifecycleStatus) {
      return;
    }
    if (message) {
      elements.lifecycleStatus.textContent = message;
      return;
    }
    if (!lifecycleEnabled) {
      elements.lifecycleStatus.textContent = t('lifecycle_disabled');
      return;
    }
    if (hasMaintainer()) {
      elements.lifecycleStatus.textContent = t('lifecycle_ready');
      return;
    }
    if (state.readerToken) {
      elements.lifecycleStatus.textContent = t('lifecycle_reader_warning');
      return;
    }
    elements.lifecycleStatus.textContent = t('lifecycle_need_token');
  }

  function refreshTokenPrompts() {
    updateStatus();
    updateSubsystemStatus();
    updateLifecycleStatus();
  }

  function hasReader() {
    return Boolean(state.readerToken || state.maintainerToken);
  }

  function hasMaintainer() {
    return Boolean(state.maintainerToken);
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
    if (!token) {
      return {};
    }
    return { Authorization: `Bearer ${token}` };
  }

  async function recordUiEvent(eventName, extra) {
    try {
      await fetch('/ui/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeader('maintainer')
        },
        body: JSON.stringify({ event: eventName, ...extra })
      });
    } catch (error) {
      console.debug('Failed to record UI event', error);
    }
  }

  function copyToClipboard(text, onSuccess, onFailure) {
    const writer = navigator.clipboard?.writeText;
    if (!writer) {
      onFailure(new Error('Clipboard API unavailable'));
      return;
    }
    writer
      .call(navigator.clipboard, text)
      .then(onSuccess)
      .catch((error) => onFailure(error));
  }

  function downloadJsonPayload(payload, filename) {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  async function performSearch(formData) {
    const query = (formData.get('query') || '').toString().trim();
    const limit = Number(formData.get('limit') || 5);
    const includeGraph = formData.get('include_graph') === 'on';
    const filters = buildSearchFilters(formData);

    if (!validateSearchRequest(query)) {
      return;
    }

    prepareSearchUi();

    const body = {
      query,
      limit,
      include_graph: includeGraph
    };
    if (filters) {
      body.filters = filters;
    }

    try {
      const response = await fetch('/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeader('reader')
        },
        body: JSON.stringify(body)
      });

      await processSearchResponse(response, { query, limit, includeGraph, filters });
    } catch (error) {
      await handleSearchException(error);
    }
  }

  function renderSearchResults(payload) {
    if (!elements.searchResults || !elements.searchList) {
      return;
    }
    elements.searchList.innerHTML = '';

    const filtersApplied = payload?.metadata?.filters_applied || null;
    renderActiveFilters(filtersApplied);

    const results = Array.isArray(payload?.results) ? payload.results : [];
    if (!results.length) {
      if (elements.searchFeedback) {
        elements.searchFeedback.textContent = t('search_no_results');
        elements.searchFeedback.hidden = false;
      }
      elements.searchResults.hidden = false;
      return;
    }

    results.forEach((entry) => {
      const li = document.createElement('li');
      li.className = 'dm-result__item';

      const title = document.createElement('h4');
      title.textContent = entry?.chunk?.title || entry?.chunk?.path || 'Untitled result';
      li.appendChild(title);

      const symbolInfo = prepareSymbolEntries(entry?.chunk?.symbols);

      if (entry?.chunk?.snippet) {
        const snippet = document.createElement('pre');
        snippet.className = 'dm-result__snippet';
        snippet.textContent = entry.chunk.snippet;
        li.appendChild(snippet);
      }

      const meta = document.createElement('div');
      meta.className = 'dm-result__meta';

      if (entry?.chunk?.path) {
        meta.appendChild(createMetaTag('Path', entry.chunk.path));
      }

      if (entry?.graph_context?.subsystem) {
        meta.appendChild(createMetaTag('Subsystem', entry.graph_context.subsystem));
      }

      if (symbolInfo.lineLabel) {
        meta.appendChild(createMetaTag('Lines', symbolInfo.lineLabel));
      }

      const scoring = entry?.scoring || {};
      if (typeof scoring.vector_score === 'number') {
        meta.appendChild(createMetaTag('Vector', scoring.vector_score.toFixed(4)));
      }
      if (typeof scoring.lexical_score === 'number') {
        meta.appendChild(createMetaTag('Lexical', scoring.lexical_score.toFixed(4)));
      }
      if (typeof scoring.adjusted_score === 'number') {
        meta.appendChild(createMetaTag('Adjusted', scoring.adjusted_score.toFixed(4)));
      }

      li.appendChild(meta);

      if (symbolInfo.entries.length) {
        li.appendChild(renderSymbolSection(symbolInfo.entries, entry?.chunk?.symbol_count));
      }

      elements.searchList.appendChild(li);
    });

    if (elements.searchFeedback) {
      const prompt = payload?.metadata?.feedback_prompt || '';
      elements.searchFeedback.textContent = prompt;
      elements.searchFeedback.hidden = !prompt;
      elements.searchFeedback.classList.remove('dm-alert-error');
    }

    elements.searchResults.hidden = false;
  }

  function renderActiveFilters(filters) {
    if (!elements.searchFilters) {
      return;
    }
    elements.searchFilters.innerHTML = '';
    if (!filters || typeof filters !== 'object') {
      elements.searchFilters.hidden = true;
      return;
    }
    Object.entries(filters).forEach(([key, value]) => {
      if (value === null || value === undefined) {
        return;
      }
      const values = Array.isArray(value) ? value : [value];
      values.forEach((entry) => {
        const text = String(entry ?? '').trim();
        if (!text) {
          return;
        }
        elements.searchFilters.appendChild(createFilterPill(formatFilterLabel(key), text, key));
      });
    });
    elements.searchFilters.hidden = elements.searchFilters.childElementCount === 0;
  }

  function formatFilterLabel(key) {
    switch (key) {
      case 'symbols':
        return 'Symbol';
      case 'symbol_kinds':
        return 'Kind';
      case 'symbol_languages':
        return 'Language';
      case 'artifact_types':
        return 'Artifact';
      case 'subsystems':
        return 'Subsystem';
      case 'namespaces':
        return 'Namespace';
      case 'tags':
        return 'Tag';
      case 'updated_after':
        return 'Updated After';
      case 'max_age_days':
        return 'Max Age (days)';
      default:
        return key;
    }
  }

  function createFilterPill(label, value, key) {
    const pill = document.createElement('span');
    pill.className = 'dm-pill';
    pill.textContent = `${label}: ${formatFilterValue(key, value)}`;
    return pill;
  }

  function formatFilterValue(key, value) {
    if (!value) {
      return value;
    }
    const lower = value.toLowerCase();
    if (key === 'symbol_languages') {
      return formatLanguageLabel(lower);
    }
    if (key === 'symbol_kinds') {
      return formatKindLabel(lower);
    }
    return value;
  }

  function buildSearchFilters(formData) {
    const filters = {};
    const kinds = normaliseMultiSelect(formData.getAll('symbol_kinds'));
    if (kinds.length) {
      filters.symbol_kinds = kinds;
    }
    const languages = normaliseMultiSelect(formData.getAll('symbol_languages'));
    if (languages.length) {
      filters.symbol_languages = languages;
    }
    return Object.keys(filters).length ? filters : null;
  }

  function normaliseMultiSelect(values, options = {}) {
    const lowercase = options.lowercase !== false;
    const result = [];
    const seen = new Set();
    values.forEach((value) => {
      if (value === null || value === undefined) {
        return;
      }
      const text = String(value).trim();
      if (!text) {
        return;
      }
      const key = lowercase ? text.toLowerCase() : text;
      if (seen.has(key)) {
        return;
      }
      seen.add(key);
      result.push(key);
    });
    return result;
  }

  function cloneFilters(filters) {
    if (!filters || typeof filters !== 'object') {
      return null;
    }
    const copy = {};
    Object.entries(filters).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        const entries = value
          .map((item) => String(item ?? '').trim())
          .filter((item) => item);
        if (entries.length) {
          copy[key] = entries;
        }
      } else if (value !== null && value !== undefined) {
        const text = String(value).trim();
        if (text) {
          copy[key] = text;
        }
      }
    });
    return Object.keys(copy).length ? copy : null;
  }

  function prepareSymbolEntries(rawSymbols) {
    const entries = [];
    let minLine = Number.POSITIVE_INFINITY;
    let maxLine = Number.NEGATIVE_INFINITY;

    if (Array.isArray(rawSymbols)) {
      rawSymbols.forEach((symbol) => {
        if (!symbol || typeof symbol !== 'object') {
          return;
        }
        const qualified = typeof symbol.qualified_name === 'string' ? symbol.qualified_name.trim() : '';
        const name = typeof symbol.name === 'string' ? symbol.name.trim() : '';
        const label = qualified || name;
        if (!label) {
          return;
        }
        const kind = typeof symbol.kind === 'string' ? symbol.kind.trim().toLowerCase() : '';
        const language = typeof symbol.language === 'string' ? symbol.language.trim().toLowerCase() : '';
        const lineStart = coerceNumber(symbol.line_start);
        const lineEndRaw = coerceNumber(symbol.line_end);
        const lineEnd = lineEndRaw !== null ? lineEndRaw : lineStart;
        if (lineStart !== null && lineStart < minLine) {
          minLine = lineStart;
        }
        if (lineEnd !== null && lineEnd > maxLine) {
          maxLine = lineEnd;
        }
        entries.push({
          qualified_name: qualified,
          name,
          kind,
          language,
          line_start: lineStart,
          line_end: lineEnd,
          editor_uri: typeof symbol.editor_uri === 'string' ? symbol.editor_uri : null
        });
      });
    }

    const lineLabel = entries.length && minLine !== Number.POSITIVE_INFINITY && maxLine !== Number.NEGATIVE_INFINITY
      ? formatLineRange(minLine, maxLine)
      : '';

    return {
      entries,
      lineLabel
    };
  }

  function renderSymbolSection(symbols, symbolCount) {
    const container = document.createElement('div');
    container.className = 'dm-result__symbols';

    const total = typeof symbolCount === 'number' ? symbolCount : symbols.length;
    const label = document.createElement('span');
    label.className = 'dm-result__symbols-label';
    label.textContent = `Symbols (${total})`;
    container.appendChild(label);

    const list = document.createElement('ul');
    list.className = 'dm-symbol-list';

    symbols.forEach((symbol) => {
      const item = document.createElement('li');
      item.className = 'dm-symbol';

      const name = document.createElement('span');
      name.className = 'dm-symbol__name';
      name.textContent = symbol.qualified_name || symbol.name || 'Symbol';
      item.appendChild(name);

      if (symbol.kind || symbol.language) {
        const badges = document.createElement('span');
        badges.className = 'dm-symbol__badges';
        if (symbol.kind) {
          badges.appendChild(createBadge(formatKindLabel(symbol.kind), 'kind'));
        }
        if (symbol.language) {
          badges.appendChild(createBadge(formatLanguageLabel(symbol.language), 'language'));
        }
        item.appendChild(badges);
      }

      const lineLabel = formatLineRange(symbol.line_start, symbol.line_end);
      if (lineLabel) {
        const lineEl = document.createElement('span');
        lineEl.className = 'dm-symbol__lines';
        lineEl.textContent = lineLabel;
        item.appendChild(lineEl);
      }

      if (symbol.editor_uri) {
        const link = document.createElement('a');
        link.className = 'dm-symbol__link';
        link.href = symbol.editor_uri;
        link.target = '_blank';
        link.rel = 'noreferrer';
        link.textContent = 'Open in editor';
        item.appendChild(link);
      }

      list.appendChild(item);
    });

    container.appendChild(list);

    if (typeof total === 'number' && total > symbols.length) {
      const more = document.createElement('span');
      more.className = 'dm-symbol__more';
      more.textContent = `+${total - symbols.length} more`;
      container.appendChild(more);
    }

    return container;
  }

  function createBadge(text, variant) {
    const badge = document.createElement('span');
    badge.className = variant ? `dm-symbol__badge dm-symbol__badge--${variant}` : 'dm-symbol__badge';
    badge.textContent = text;
    return badge;
  }

  function formatKindLabel(value) {
    if (!value) {
      return '';
    }
    const lower = value.toLowerCase();
    return lower.charAt(0).toUpperCase() + lower.slice(1);
  }

  function formatLanguageLabel(value) {
    if (!value) {
      return '';
    }
    const lower = value.toLowerCase();
    const labels = {
      python: 'Python',
      typescript: 'TypeScript',
      tsx: 'TSX',
      javascript: 'JavaScript',
      go: 'Go'
    };
    return labels[lower] || formatKindLabel(lower);
  }

  function formatLineRange(start, end) {
    const startLine = coerceNumber(start);
    const endLine = coerceNumber(end);
    if (startLine === null && endLine === null) {
      return '';
    }
    if (startLine !== null && endLine !== null) {
      return startLine === endLine ? `Line ${startLine}` : `Lines ${startLine}–${endLine}`;
    }
    const line = startLine !== null ? startLine : endLine;
    return line !== null ? `Line ${line}` : '';
  }

  function coerceNumber(value) {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return Math.trunc(value);
    }
    if (typeof value === 'string') {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) {
        return Math.trunc(parsed);
      }
    }
    return null;
  }

  function validateSearchRequest(query) {
    if (!query || !hasReader()) {
      updateStatus(query ? t('search_need_token') : t('search_require_query_token'));
      return false;
    }
    return true;
  }

  function prepareSearchUi() {
    updateStatus(t('search_running'));
    if (elements.searchFeedback) {
      elements.searchFeedback.textContent = '';
      elements.searchFeedback.hidden = true;
      elements.searchFeedback.classList.remove('dm-alert-error');
    }
    if (elements.searchFilters) {
      elements.searchFilters.hidden = true;
      elements.searchFilters.innerHTML = '';
    }
    if (elements.searchResults) {
      elements.searchResults.hidden = true;
    }
    if (elements.searchActions) {
      elements.searchActions.hidden = true;
    }
  }

  async function processSearchResponse(response, params) {
    updateRequestIdFromResponse(response);
    if (!response.ok) {
      const message = await extractSearchError(response);
      updateStatus(message);
      await recordUiEvent('search_error', { status: response.status, message });
      return;
    }

    const payload = await response.json();
    lastSearchParams = params;
    lastSearchPayload = payload;
    renderSearchResults(payload);
    if (elements.searchActions) {
      elements.searchActions.hidden = false;
    }
    updateStatus(`Found ${payload.results?.length || 0} match(es).`);
    await recordUiEvent('search_success', { params });
  }

  function updateRequestIdFromResponse(response) {
    const requestId = response.headers.get('x-request-id');
    if (requestId && elements.requestId) {
      elements.requestId.textContent = requestId;
    }
  }

  async function extractSearchError(response) {
    if (response.status === 401 || response.status === 403) {
      return t('search_error_auth');
    }
    const detail = await response.json().catch(() => ({}));
    if (detail?.detail) {
      return detail.detail;
    }
    return t('search_error_generic');
  }

  async function handleSearchException(error) {
    console.error('Search request failed', error);
    updateStatus(t('search_error_generic'));
    await recordUiEvent('search_error', { error: String(error) });
  }

  function createMetaTag(label, value) {
    const el = document.createElement('span');
    el.textContent = `${label}: ${value}`;
    return el;
  }

  async function loadSubsystem(formData) {
    const name = (formData.get('name') || '').toString().trim();
    const depth = Math.min(4, Math.max(1, Number(formData.get('depth') || 2)));
    const limit = Math.min(50, Math.max(1, Number(formData.get('limit') || 15)));
    const includeArtifacts = formData.get('include_artifacts') === 'on';

    if (!validateSubsystemRequest(name)) {
      return;
    }

    prepareSubsystemUi();

    const params = new URLSearchParams({ depth: String(depth), limit: String(limit) });
    if (!includeArtifacts) {
      params.set('include_artifacts', 'false');
    }

    try {
      const response = await fetch(`/graph/subsystems/${encodeURIComponent(name)}?${params.toString()}`, {
        headers: authHeader('reader')
      });

      await processSubsystemResponse(response, { name, depth, limit, includeArtifacts });
    } catch (error) {
      await handleSubsystemException(error);
    }
  }

  function renderSubsystem(payload) {
    if (!elements.subsystemPanel) {
      return;
    }
    const subsystem = payload?.subsystem || {};
    const props = subsystem.properties || {};

    renderSubsystemHeader(subsystem, props, payload);
    renderSubsystemSummary(props, subsystem);
    renderSubsystemArtifacts(payload);
    renderSubsystemTable(payload);
    resetSubsystemError();
    elements.subsystemPanel.hidden = false;
  }

  function renderSubsystemHeader(subsystem, props, payload) {
    const name = props.name || props.title || subsystem.id || 'Subsystem';
    if (elements.subsystemTitle) {
      elements.subsystemTitle.textContent = name;
    }
    if (elements.subsystemHops) {
      const total = payload?.related?.total ?? 0;
      const isVisible = Boolean(total);
      elements.subsystemHops.textContent = isVisible ? `${total} related nodes` : '';
      elements.subsystemHops.style.display = isVisible ? 'inline-flex' : 'none';
    }
  }

  function renderSubsystemSummary(props, subsystem) {
    if (!elements.subsystemSummary) {
      return;
    }
    elements.subsystemSummary.innerHTML = '';
    const added = new Set();
    const addDefinition = (label, value) => {
      if (value === undefined || value === null || value === '') {
        return;
      }
      const dt = document.createElement('dt');
      dt.textContent = label;
      const dd = document.createElement('dd');
      dd.textContent = String(value);
      elements.subsystemSummary.append(dt, dd);
    };
    const formatKey = (key) => key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    addDefinition('ID', subsystem.id);
    if (Array.isArray(subsystem.labels) && subsystem.labels.length) {
      addDefinition('Labels', subsystem.labels.join(', '));
    }
    ['owner', 'owner_team', 'status', 'criticality', 'freshness_days', 'updated_at'].forEach((key) => {
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

  function renderSubsystemArtifacts(payload) {
    if (!elements.subsystemArtifacts) {
      return;
    }
    elements.subsystemArtifacts.innerHTML = '';
    const artifacts = Array.isArray(payload?.artifacts) ? payload.artifacts : [];
    if (!artifacts.length) {
      const li = document.createElement('li');
      li.textContent = 'No artifacts linked.';
      elements.subsystemArtifacts.appendChild(li);
      return;
    }
    artifacts.forEach((artifact) => {
      const li = document.createElement('li');
      const aprops = artifact?.properties || {};
      li.textContent = aprops.path || aprops.title || artifact.id;
      elements.subsystemArtifacts.appendChild(li);
    });
  }

  function renderSubsystemTable(payload) {
    if (!elements.subsystemTable) {
      return;
    }
    elements.subsystemTable.innerHTML = '';
    const related = Array.isArray(payload?.related?.nodes) ? payload.related.nodes : [];
    if (!related.length) {
      const row = document.createElement('tr');
      const cell = document.createElement('td');
      cell.colSpan = 4;
      cell.textContent = 'No related nodes at this depth.';
      row.appendChild(cell);
      elements.subsystemTable.appendChild(row);
      return;
    }
    related.forEach((entry) => {
      const row = document.createElement('tr');
      const target = entry?.target || {};
      const tprops = target.properties || {};
      appendCells(row, [tprops.name || tprops.title || target.id, entry?.relationship || '—', entry?.direction || 'OUT', String(entry?.hops ?? '—')]);
      elements.subsystemTable.appendChild(row);
    });
  }

  function appendCells(row, values) {
    values.forEach((value) => {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    });
  }

  function resetSubsystemError() {
    if (elements.subsystemError) {
      elements.subsystemError.hidden = true;
      elements.subsystemError.textContent = '';
    }
  }

  function validateSubsystemRequest(name) {
    if (!name) {
      updateSubsystemStatus(t('subsystem_ready'));
      return false;
    }
    if (!hasReader()) {
      updateSubsystemStatus(t('subsystem_need_token'));
      return false;
    }
    return true;
  }

  function prepareSubsystemUi() {
    updateSubsystemStatus(t('subsystem_loading'));
    if (elements.subsystemError) {
      elements.subsystemError.hidden = true;
      elements.subsystemError.textContent = '';
    }
    if (elements.subsystemPanel) {
      elements.subsystemPanel.hidden = true;
    }
    if (elements.subsystemActions) {
      elements.subsystemActions.hidden = true;
    }
  }

  async function processSubsystemResponse(response, params) {
    updateRequestIdFromResponse(response);
    if (!response.ok) {
      const message = await extractSubsystemError(response);
      exposeSubsystemError(message);
      await recordUiEvent('subsystem_error', { status: response.status, message });
      return;
    }

    const payload = await response.json();
    lastSubsystemParams = params;
    lastSubsystemPayload = payload;
    renderSubsystem(payload);
    if (elements.subsystemActions) {
      elements.subsystemActions.hidden = false;
    }
    const loaded = payload?.related?.nodes?.length || 0;
    const total = payload?.related?.total ?? loaded;
    const extra = payload?.related?.cursor ? ' (more available via API).' : '.';
    updateSubsystemStatus(`Loaded ${loaded} of ${total} related node(s)${extra}`);
    await recordUiEvent('subsystem_success', { params });
  }

  async function extractSubsystemError(response) {
    if (response.status === 401 || response.status === 403) {
      return t('subsystem_error_auth');
    }
    const detail = await response.json().catch(() => ({}));
    if (detail?.detail) {
      return detail.detail;
    }
    return t('subsystem_error_generic');
  }

  function exposeSubsystemError(message) {
    updateSubsystemStatus(message);
    if (elements.subsystemError) {
      elements.subsystemError.hidden = false;
      elements.subsystemError.textContent = message;
    }
  }

  async function handleSubsystemException(error) {
    console.error('Subsystem request failed', error);
    updateSubsystemStatus(t('subsystem_error_generic'));
    await recordUiEvent('subsystem_error', { error: String(error) });
  }

  function computeLifecycleCounts(payload) {
    const summary = payload?.summary || {};
    const staleDocs = Array.isArray(payload?.stale_docs) ? payload.stale_docs : [];
    const missingTests = Array.isArray(payload?.missing_tests) ? payload.missing_tests : [];
    const removedArtifacts = Array.isArray(payload?.removed_artifacts) ? payload.removed_artifacts : [];
    const symbolTests = Array.isArray(payload?.symbol_tests) ? payload.symbol_tests : [];
    const symbolGaps = Array.isArray(payload?.symbol_test_gaps) ? payload.symbol_test_gaps : [];
    const isolated = payload?.isolated || {};
    const isolatedCount = Object.values(isolated).reduce((total, nodes) => {
      if (!Array.isArray(nodes)) {
        return total;
      }
      return total + nodes.length;
    }, 0);

    const hasSymbolInsights = Boolean(symbolTests.length || symbolGaps.length || summary.symbol_tests !== undefined || summary.symbol_test_gaps !== undefined);

    return {
      stale_docs: Number(summary.stale_docs ?? staleDocs.length) || 0,
      isolated_nodes: Number(summary.isolated_nodes ?? isolatedCount) || 0,
      subsystems_missing_tests: Number(summary.subsystems_missing_tests ?? missingTests.length) || 0,
      removed_artifacts: Number(summary.removed_artifacts ?? removedArtifacts.length) || 0,
      symbol_tests: Number(summary.symbol_tests ?? symbolTests.length) || 0,
      _has_symbol_insights: hasSymbolInsights
    };
  }

  async function loadLifecycle() {
    if (!validateLifecycleAccess()) {
      return;
    }

    prepareLifecycleUi();

    try {
      const response = await fetch('/lifecycle', {
        headers: authHeader('maintainer')
      });

      await processLifecycleResponse(response);
    } catch (error) {
      await handleLifecycleException(error);
    }
  }

  async function loadLifecycleHistory() {
    if (!lifecycleEnabled || !hasMaintainer()) {
      return;
    }
    try {
      const response = await fetch('/lifecycle/history?limit=30', {
        headers: authHeader('maintainer')
      });
      if (!response.ok) {
        await recordUiEvent('lifecycle_history_error', { status: response.status });
        return;
      }
      const payload = await response.json();
      const history = Array.isArray(payload?.history) ? payload.history : [];
      renderLifecycleHistory(history);
    } catch (error) {
      console.error('Lifecycle history request failed', error);
      await recordUiEvent('lifecycle_history_error', { error: String(error) });
    }
  }

  function validateLifecycleAccess() {
    if (!lifecycleEnabled) {
      updateLifecycleStatus(t('lifecycle_disabled'));
      return false;
    }
    if (!hasMaintainer()) {
      updateLifecycleStatus(hasReader() ? t('lifecycle_reader_warning') : t('lifecycle_need_token'));
      return false;
    }
    return true;
  }

  function prepareLifecycleUi() {
    updateLifecycleStatus(t('lifecycle_loading'));
    if (elements.lifecycleSummary) {
      elements.lifecycleSummary.hidden = true;
    }
    if (elements.lifecyclePanels) {
      elements.lifecyclePanels.hidden = true;
    }
    if (elements.lifecycleSymbolPanel) {
      elements.lifecycleSymbolPanel.hidden = true;
    }
  }

  async function processLifecycleResponse(response) {
    updateRequestIdFromResponse(response);
    if (!response.ok) {
      const message = await extractLifecycleError(response);
      updateLifecycleStatus(message);
      await recordUiEvent('lifecycle_error', { status: response.status, message });
      return;
    }

    const payload = await response.json();
    renderLifecycle(payload);
    await loadLifecycleHistory();
    updateLifecycleStatus(`${t('lifecycle_updated')} (${new Date().toLocaleTimeString()})`);
    await recordUiEvent('lifecycle_success');
  }

  async function extractLifecycleError(response) {
    if (response.status === 401 || response.status === 403) {
      return t('lifecycle_error_auth');
    }
    const detail = await response.json().catch(() => ({}));
    if (detail?.detail) {
      return detail.detail;
    }
    return t('lifecycle_error_generic');
  }

  async function handleLifecycleException(error) {
    console.error('Lifecycle request failed', error);
    updateLifecycleStatus(t('lifecycle_error_generic'));
    await recordUiEvent('lifecycle_error', { error: String(error) });
  }

  function renderLifecycle(payload) {
    if (!elements.lifecycleRoot) {
      return;
    }
    const counts = computeLifecycleCounts(payload);
    showLifecycleSummary(counts);
    updateLifecycleGeneratedAt(payload);
    renderLifecycleTables(payload);
    if (elements.lifecyclePanels) {
      elements.lifecyclePanels.hidden = false;
    }
  }

  function showLifecycleSummary(counts) {
    if (elements.lifecycleSummary) {
      elements.lifecycleSummary.hidden = false;
    }
    const hasSymbolInsights = Boolean(counts._has_symbol_insights);
    lifecycleMetricMap.forEach((refs, key) => {
      if (!refs) {
        return;
      }
      if (key === 'symbol_tests' && refs.containerEl) {
        refs.containerEl.hidden = !hasSymbolInsights;
      }
      if (key === '_has_symbol_insights') {
        return;
      }
      const value = counts[key] ?? 0;
      if (refs.valueEl) {
        refs.valueEl.textContent = new Intl.NumberFormat().format(value);
      }
    });
  }

  function updateLifecycleGeneratedAt(payload) {
    if (!elements.lifecycleGenerated) {
      return;
    }
    const generated = payload?.generated_at || payload?.generated_at_iso || payload?.timestamp;
    const formatted = formatTimestamp(generated);
    if (formatted) {
      elements.lifecycleGenerated.hidden = false;
      elements.lifecycleGenerated.textContent = `Generated at ${formatted}`;
    } else {
      elements.lifecycleGenerated.hidden = true;
    }
  }

  function renderLifecycleTables(payload) {
    const generatedAt = typeof payload?.generated_at === 'number' ? payload.generated_at : null;
    renderStaleDocsTable(payload, generatedAt);
    renderIsolatedNodesTable(payload);
    renderMissingTestsTable(payload);
    renderSymbolTestsTable(payload);
    renderRemovedArtifactsTable(payload);
  }

  function renderStaleDocsTable(payload, generatedAt) {
    const rows = Array.isArray(payload?.stale_docs) ? payload.stale_docs : [];
    renderListTable(elements.lifecycleStale, rows, (row, doc) => {
      const path = doc?.path || doc?.properties?.path || doc?.id || 'Unknown';
      const subsystem = doc?.subsystem || doc?.metadata?.subsystem || doc?.properties?.subsystem || '—';
      let age = '—';
      const gitTimestamp = doc?.git_timestamp ?? doc?.properties?.git_timestamp;
      if (typeof gitTimestamp === 'number' && generatedAt) {
        age = Math.max(0, (generatedAt - gitTimestamp) / 86400).toFixed(1);
      }
      appendCells(row, [path, subsystem, age]);
    }, 3);
  }

  function renderIsolatedNodesTable(payload) {
    const entries = buildIsolatedEntries(payload?.isolated || {});
    renderListTable(elements.lifecycleIsolated, entries, (row, entry) => {
      const props = entry?.node?.properties || {};
      const label = props.name || props.title || entry?.node?.id || 'Node';
      const labels = Array.isArray(entry?.node?.labels) && entry.node.labels.length
        ? entry.node.labels.join(', ')
        : entry?.label || '—';
      appendCells(row, [label, labels]);
    }, 2);
  }

  function renderMissingTestsTable(payload) {
    const rows = Array.isArray(payload?.missing_tests) ? payload.missing_tests : [];
    renderListTable(elements.lifecycleMissing, rows, (row, item) => {
      if (typeof item === 'string') {
        appendCells(row, [item, '—']);
        return;
      }
      const name = item?.name || item?.subsystem || item?.id || 'Subsystem';
      const note = item?.note || item?.reason || 'Needs test coverage';
      appendCells(row, [name, note]);
    }, 2);
  }

  function renderSymbolTestsTable(payload) {
    if (!elements.lifecycleSymbolTests) {
      return;
    }
    const coverage = Array.isArray(payload?.symbol_tests) ? payload.symbol_tests : [];
    const gaps = Array.isArray(payload?.symbol_test_gaps) ? payload.symbol_test_gaps : [];
    const entries = [];

    coverage.forEach((item) => {
      entries.push(normaliseSymbolTestEntry(item, 'Covered'));
    });
    gaps.forEach((item) => {
      entries.push(normaliseSymbolTestEntry(item, 'Missing'));
    });

    if (!entries.length) {
      elements.lifecycleSymbolTests.innerHTML = '';
      if (elements.lifecycleSymbolPanel) {
        elements.lifecycleSymbolPanel.hidden = true;
      }
      return;
    }

    if (elements.lifecycleSymbolPanel) {
      elements.lifecycleSymbolPanel.hidden = false;
    }

    renderListTable(elements.lifecycleSymbolTests, entries, (row, entry) => {
      appendCells(row, [entry.symbol, entry.tests, entry.status]);
    }, 3);
  }

  function normaliseSymbolTestEntry(item, fallbackStatus) {
    const symbol = extractSymbolName(item);
    const tests = extractSymbolTests(item);
    const status = extractSymbolStatus(item, fallbackStatus);
    return {
      symbol,
      tests: tests.length ? tests.join(', ') : '—',
      status
    };
  }

  function extractSymbolName(item) {
    if (!item || typeof item !== 'object') {
      return 'Symbol';
    }
    const candidates = [item.symbol, item.qualified_name, item.name, item.id];
    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.trim()) {
        return candidate.trim();
      }
    }
    return 'Symbol';
  }

  function extractSymbolTests(item) {
    if (!item || typeof item !== 'object') {
      return [];
    }
    const arrayCandidates = [item.tests, item.test_paths, item.test_cases, item.cases];
    for (const candidate of arrayCandidates) {
      if (Array.isArray(candidate)) {
        return candidate
          .map((entry) => String(entry ?? '').trim())
          .filter((entry) => entry);
      }
    }
    const singleCandidates = [item.test, item.case, item.path];
    for (const candidate of singleCandidates) {
      if (typeof candidate === 'string' && candidate.trim()) {
        return [candidate.trim()];
      }
    }
    return [];
  }

  function extractSymbolStatus(item, fallbackStatus) {
    if (!item || typeof item !== 'object') {
      return typeof fallbackStatus === 'string' ? fallbackStatus : '—';
    }
    const candidates = [item.status, item.note, item.reason, item.state];
    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.trim()) {
        return candidate.trim();
      }
    }
    return typeof fallbackStatus === 'string' ? fallbackStatus : '—';
  }

  function renderRemovedArtifactsTable(payload) {
    const rows = Array.isArray(payload?.removed_artifacts) ? payload.removed_artifacts : [];
    renderListTable(elements.lifecycleRemoved, rows, (row, item) => {
      if (typeof item === 'string') {
        appendCells(row, [item, '—']);
        return;
      }
      const pathVal = item?.path || item?.id || item?.properties?.path || 'Artifact';
      const removedAt = formatTimestamp(item?.removed_at || item?.timestamp || item?.recorded_at);
      appendCells(row, [pathVal, removedAt || '—']);
    }, 2);
  }

  function renderListTable(table, rows, renderer, columns) {
    if (!table) {
      return;
    }
    table.innerHTML = '';
    if (!rows.length) {
      const row = document.createElement('tr');
      const cell = document.createElement('td');
      cell.colSpan = columns;
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
  }

  function buildIsolatedEntries(isolatedMap) {
    const entries = [];
    Object.entries(isolatedMap).forEach(([label, nodes]) => {
      if (!Array.isArray(nodes)) {
        return;
      }
      nodes.forEach((node) => {
        entries.push({ label, node });
      });
    });
    return entries;
  }

  function renderLifecycleHistory(history) {
    lifecycleMetricMap.forEach((refs, metric) => {
      if (!refs?.sparkEl) {
        return;
      }
      const values = history.map((entry) => Number(entry?.counts?.[metric] ?? 0));
      renderSparkline(values, refs.sparkEl);
    });
  }

  function renderSparkline(values, element) {
    if (!element) {
      return;
    }
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

  function formatTimestamp(value) {
    if (!value) {
      return '';
    }
    if (typeof value === 'number') {
      return new Date(value * 1000).toLocaleString();
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return '';
    }
    return date.toLocaleString();
  }

  function openModal() {
    if (!elements.modal) {
      return;
    }
    elements.modal.dataset.open = 'true';
    elements.modal.removeAttribute('hidden');
    syncInputs();
    (elements.readerInput || elements.maintainerInput)?.focus();
  }

  function closeModal() {
    if (!elements.modal) {
      return;
    }
    elements.modal.dataset.open = 'false';
    elements.modal.setAttribute('hidden', 'hidden');
  }

  function attachEventHandlers() {
    attachModalHandlers();
    attachTokenHandlers();
    attachSearchHandlers();
    attachSubsystemHandlers();
    attachLifecycleHandlers();
    attachRecipeHandlers();
    attachPreferenceHandlers();
  }

  function attachModalHandlers() {
    elements.openTokens.forEach((button) => button.addEventListener('click', openModal));
    elements.closeTokens.forEach((button) => button.addEventListener('click', closeModal));
    scope.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && elements.modal?.dataset.open === 'true') {
        closeModal();
      }
    });
  }

  function attachTokenHandlers() {
    if (elements.saveTokens) {
      elements.saveTokens.addEventListener('click', () => {
        state.readerToken = (elements.readerInput?.value || '').trim();
        state.maintainerToken = (elements.maintainerInput?.value || '').trim();
        sessionStorage.setItem('dm.readerToken', state.readerToken);
        sessionStorage.setItem('dm.maintainerToken', state.maintainerToken);
        refreshTokenPrompts();
        updateStatus(t('tokens_saved'));
        closeModal();
      });
    }

    if (elements.clearTokens) {
      elements.clearTokens.addEventListener('click', () => {
        state.readerToken = '';
        state.maintainerToken = '';
        sessionStorage.removeItem('dm.readerToken');
        sessionStorage.removeItem('dm.maintainerToken');
        syncInputs();
        refreshTokenPrompts();
        updateStatus(t('tokens_cleared'));
      });
    }
  }

  function attachSearchHandlers() {
    const searchForm = document.getElementById('dm-search-form');
    if (searchForm) {
      searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        performSearch(new FormData(searchForm));
      });
    }

    if (elements.searchCopy) {
      elements.searchCopy.addEventListener('click', () => {
        if (!lastSearchParams) {
          updateStatus(t('search_before_copy'));
          return;
        }
        const payload = {
          query: lastSearchParams.query,
          limit: lastSearchParams.limit
        };
        if (!lastSearchParams.includeGraph) {
          payload.include_graph = false;
        }
        const filters = cloneFilters(lastSearchParams.filters);
        if (filters) {
          payload.filters = filters;
        }
        const command = `km-search ${JSON.stringify(payload)}`;
        copyToClipboard(command, () => {
          updateStatus(t('search_copy_success'));
          recordUiEvent('search_copy_command');
        }, () => updateStatus(t('search_copy_failure')));
      });
    }

    if (elements.searchDownload) {
      elements.searchDownload.addEventListener('click', () => {
        if (!lastSearchPayload) {
          updateStatus(t('search_before_download'));
          return;
        }
        downloadJsonPayload(lastSearchPayload, `search-${Date.now()}.json`);
        updateStatus(t('search_download_success'));
        recordUiEvent('search_download');
      });
    }
  }

  function attachSubsystemHandlers() {
    const subsystemForm = document.getElementById('dm-subsystem-form');
    if (subsystemForm) {
      subsystemForm.addEventListener('submit', (event) => {
        event.preventDefault();
        loadSubsystem(new FormData(subsystemForm));
      });
    }

    if (elements.subsystemCopy) {
      elements.subsystemCopy.addEventListener('click', () => {
        if (!lastSubsystemParams) {
          updateSubsystemStatus(t('subsystem_before_copy'));
          return;
        }
        const payload = {
          name: lastSubsystemParams.name,
          depth: lastSubsystemParams.depth,
          limit: lastSubsystemParams.limit
        };
        if (!lastSubsystemParams.includeArtifacts) {
          payload.include_artifacts = false;
        }
        const command = `km-graph-subsystem ${JSON.stringify(payload)}`;
        copyToClipboard(command, () => {
          updateSubsystemStatus(t('subsystem_copy_success'));
          recordUiEvent('subsystem_copy_command');
        }, () => updateSubsystemStatus(t('subsystem_copy_failure')));
      });
    }

    if (elements.subsystemDownload) {
      elements.subsystemDownload.addEventListener('click', () => {
        if (!lastSubsystemPayload) {
          updateSubsystemStatus(t('subsystem_before_download'));
          return;
        }
        const label = lastSubsystemParams?.name || 'subsystem';
        downloadJsonPayload(lastSubsystemPayload, `subsystem-${label}-${Date.now()}.json`);
        updateSubsystemStatus(t('subsystem_download_success'));
        recordUiEvent('subsystem_download');
      });
    }
  }

  function attachLifecycleHandlers() {
    if (elements.lifecycleRefresh) {
      elements.lifecycleRefresh.addEventListener('click', () => {
        loadLifecycle();
      });
    }

    if (elements.lifecycleDownload) {
      elements.lifecycleDownload.addEventListener('click', async () => {
        if (!lifecycleEnabled) {
          updateLifecycleStatus(t('lifecycle_disabled'));
          return;
        }
        if (!hasMaintainer()) {
          updateLifecycleStatus(t('lifecycle_download_need_token'));
          return;
        }
        try {
          const response = await fetch('/ui/lifecycle/report', {
            headers: authHeader('maintainer')
          });
          if (!response.ok) {
            const detail = await response.json().catch(() => ({}));
            const message = detail?.detail || t('lifecycle_download_failure');
            updateLifecycleStatus(message);
            await recordUiEvent('lifecycle_download_error', { status: response.status, message });
            return;
          }
          const data = await response.json();
          downloadJsonPayload(data, `lifecycle-${new Date().toISOString()}.json`);
          updateLifecycleStatus(t('lifecycle_download_success'));
          await recordUiEvent('lifecycle_download');
        } catch (error) {
          console.error('Lifecycle download failed', error);
          updateLifecycleStatus(t('lifecycle_download_failure'));
          await recordUiEvent('lifecycle_download_error', { error: String(error) });
        }
      });
    }
  }

  function attachRecipeHandlers() {
    if (elements.recipeRelease) {
      elements.recipeRelease.addEventListener('click', () => {
        const command = 'km-recipe-run release-prep --var profile=release';
        copyToClipboard(command, () => {
          updateLifecycleStatus(t('lifecycle_recipe_release'));
          recordUiEvent('recipe_copy_release');
        }, () => updateLifecycleStatus(t('search_copy_failure')));
      });
    }

    if (elements.recipeStale) {
      elements.recipeStale.addEventListener('click', () => {
        const command = 'km-recipe-run stale-audit';
        copyToClipboard(command, () => {
          updateLifecycleStatus(t('lifecycle_recipe_stale'));
          recordUiEvent('recipe_copy_stale_audit');
        }, () => updateLifecycleStatus(t('search_copy_failure')));
      });
    }
  }

  function attachPreferenceHandlers() {
    if (elements.contrastToggle) {
      elements.contrastToggle.addEventListener('click', () => {
        preferences.contrast = !preferences.contrast;
        setPreference(PREF_KEYS.contrast, preferences.contrast);
        applyPreferences();
        recordUiEvent('ui_toggle_contrast', { enabled: preferences.contrast });
      });
    }

    if (elements.motionToggle) {
      elements.motionToggle.addEventListener('click', () => {
        preferences.motion = !preferences.motion;
        setPreference(PREF_KEYS.motion, preferences.motion);
        applyPreferences();
        recordUiEvent('ui_toggle_motion', { enabled: preferences.motion });
      });
    }
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

  syncInputs();
  applyPreferences();
  initialiseActiveNav();
  updateStatus();
  updateSubsystemStatus();
  updateLifecycleStatus();
  attachEventHandlers();

  if (state.active === 'lifecycle') {
    loadLifecycle();
  }
})();
