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

    const responsePromise = page.waitForResponse((response) =>
      response.url().endsWith('/search') && response.request().method() === 'POST',
    );
    await page.locator('#dm-search-form button[type="submit"]').click();
    await responsePromise;

    expect(capturedBody).toEqual({ query: 'stale docs', limit: 5, include_graph: true });

    const status = page.locator('[data-dm-search-status]');
    await expect(status).toHaveText('Found 2 match(es).');

    const results = page.locator('[data-dm-search-list] li');
    await expect(results).toHaveCount(2);
    await expect(results.nth(0)).toContainText('Lifecycle overview');
    await expect(results.nth(1)).toContainText('Release checklist');

    const feedback = page.locator('[data-dm-search-feedback]');
    await expect(feedback).toBeVisible();
    await expect(feedback).toHaveText('Was this search result helpful? Submit feedback to tune ranking.');

    await expect(page.locator('[data-dm-search-actions]')).toBeVisible();

    await page.locator('[data-dm-search-copy]').click();
    await expect(status).toHaveText('Copied MCP command to clipboard.');
    await expect.poll(() => readClipboard(page)).toBe('km-search {"query":"stale docs","limit":5}');

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
