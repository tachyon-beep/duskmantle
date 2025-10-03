import { promises as fs } from 'fs';

import { expect, test } from '@playwright/test';

import { bootstrapSession, readClipboard } from './helpers';

test.describe('Search console', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapSession(page, { readerToken: 'reader-token' });
  });

  test('runs hybrid search, exposes copy/download actions', async ({ page }) => {
    const responsePayload = {
      results: [
        {
          chunk: {
            title: 'Lifecycle overview',
            path: 'docs/lifecycle.md',
            snippet: 'Summarises lifecycle metrics and signals.',
            symbol_count: 1,
            symbols: [
              {
                id: 'docs/lifecycle.md::Lifecycle overview',
                qualified_name: 'Lifecycle.summary',
                kind: 'method',
                language: 'python',
                line_start: 12,
                line_end: 18,
                editor_uri: 'vscode://file/docs/lifecycle.md:12',
              },
            ],
          },
          graph_context: {
            subsystem: 'GatewayCore',
          },
          scoring: {
            vector_score: 0.8123,
            lexical_score: 0.6421,
            adjusted_score: 0.9012,
          },
        },
        {
          chunk: {
            title: 'Release checklist',
            path: 'docs/release.md',
            snippet: 'Checklist covering release gating tasks.',
          },
          graph_context: {
            subsystem: 'ReleaseTooling',
          },
          scoring: {
            vector_score: 0.7855,
            lexical_score: 0.5988,
            adjusted_score: 0.8423,
          },
        },
      ],
      metadata: {
        feedback_prompt: 'Was this search result helpful? Submit feedback to tune ranking.',
        filters_applied: {
          symbol_kinds: ['method'],
          symbol_languages: ['python'],
        },
      },
    };

    let capturedBody: unknown;
    let fulfilled = false;

    await page.route('**/search', async (route) => {
      const request = route.request();
      if (request.method() !== 'POST' || fulfilled) {
        await route.continue();
        return;
      }
      fulfilled = true;
      capturedBody = request.postDataJSON();
      await route.fulfill({
        status: 200,
        headers: {
          'content-type': 'application/json',
          'x-request-id': 'search-001',
        },
        body: JSON.stringify(responsePayload),
      });
    });

    await page.goto('/ui/search');
    await expect(page.locator('[data-dm-search-status]')).toHaveText('Ready. Queries will use the reader token if available.');

    await page.fill('input[name="query"]', 'stale docs');
    await page.locator('input[name="symbol_kinds"][value="method"]').setChecked(true, { force: true });
    await page.locator('input[name="symbol_languages"][value="python"]').setChecked(true, { force: true });
    await expect(page.getByLabel('Method')).toBeChecked();
    await expect(page.getByLabel('Python')).toBeChecked();

    const responsePromise = page.waitForResponse((response) =>
      response.url().endsWith('/search') && response.request().method() === 'POST',
    );
    await page.locator('#dm-search-form button[type="submit"]').click();
    await responsePromise;

    expect(capturedBody).toEqual({
      query: 'stale docs',
      limit: 5,
      include_graph: true,
      filters: {
        symbol_kinds: ['method'],
        symbol_languages: ['python'],
      },
    });

    const status = page.locator('[data-dm-search-status]');
    await expect(status).toHaveText('Found 2 match(es).');

    const results = page.locator('[data-dm-search-list] > li');
    await expect(results).toHaveCount(2);
    await expect(results.nth(0)).toContainText('Lifecycle overview');
    await expect(results.nth(1)).toContainText('Release checklist');

    const filterSummary = page.locator('[data-dm-search-filters]');
    await expect(filterSummary).toBeVisible();
    await expect(filterSummary).toContainText('Kind: Method');
    await expect(filterSummary).toContainText('Language: Python');

    const firstResult = results.nth(0);
    const snippet = firstResult.locator('.dm-result__snippet');
    await expect(snippet).toHaveText('Summarises lifecycle metrics and signals.');
    await expect(firstResult.locator('.dm-result__meta')).toContainText('Lines 12–18');

    const symbolSection = firstResult.locator('.dm-result__symbols');
    await expect(symbolSection).toContainText('Symbols (1)');
    await expect(symbolSection).toContainText('Lifecycle.summary');
    await expect(symbolSection).toContainText('Method');
    await expect(symbolSection).toContainText('Python');
    const editorLink = symbolSection.locator('.dm-symbol__link');
    await expect(editorLink).toHaveAttribute('href', 'vscode://file/docs/lifecycle.md:12');

    const feedback = page.locator('[data-dm-search-feedback]');
    await expect(feedback).toBeVisible();
    await expect(feedback).toHaveText('Was this search result helpful? Submit feedback to tune ranking.');

    await expect(page.locator('[data-dm-search-actions]')).toBeVisible();

    await page.locator('[data-dm-search-copy]').click();
    await expect(status).toHaveText('Copied MCP command to clipboard.');
    await expect.poll(() => readClipboard(page)).toBe('km-search {"query":"stale docs","limit":5,"filters":{"symbol_kinds":["method"],"symbol_languages":["python"]}}');

    const downloadPromise = page.waitForEvent('download');
    await page.locator('[data-dm-search-download]').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/^search-\d+\.json$/);
    const downloadPath = await download.path();
    expect(downloadPath).not.toBeNull();
    if (!downloadPath) {
      throw new Error('Download path unavailable for search payload');
    }

    const raw = await fs.readFile(downloadPath, 'utf-8');
    const parsed = JSON.parse(raw) as typeof responsePayload;
    expect(parsed).toEqual(responsePayload);

    await expect(page.locator('[data-dm-request-id]')).toHaveText('search-001');
  });
});
