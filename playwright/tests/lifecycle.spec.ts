import { promises as fs } from 'fs';

import { expect, test } from '@playwright/test';

import { bootstrapSession, readClipboard } from './helpers';

test.describe('Lifecycle dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapSession(page, { maintainerToken: 'maintainer-token' });
  });

  test('renders lifecycle metrics, refreshes, and exercises maintainer actions', async ({ page }) => {
    let lifecycleRequests = 0;
    page.on('request', (request) => {
      if (request.url().endsWith('/lifecycle')) {
        lifecycleRequests += 1;
      }
    });

    await page.goto('/ui/lifecycle');

    const status = page.locator('[data-dm-lifecycle-status]');
    await expect(status).toContainText('Lifecycle metrics updated', { timeout: 15_000 });
    await expect.poll(() => lifecycleRequests).toBeGreaterThan(0);

    const summary = page.locator('[data-dm-lifecycle-summary]');
    await expect(summary).toBeVisible();
    await expect(summary.locator('[data-metric="stale_docs"] .dm-metric__value')).toHaveText('2');
    await expect(summary.locator('[data-metric="isolated_nodes"] .dm-metric__value')).toHaveText('1');
    await expect(summary.locator('[data-metric="removed_artifacts"] .dm-metric__value')).toHaveText('1');

    const staleRows = page.locator('[data-dm-lifecycle-stale] tbody tr');
    await expect(staleRows).toHaveCount(2);
    await expect(staleRows.first()).toContainText('docs/design/playbook.md');

    const missingRows = page.locator('[data-dm-lifecycle-missing] tbody tr');
    await expect(missingRows).toHaveCount(1);
    await expect(missingRows.first()).toContainText('GatewayCore');

    const spark = page.locator('[data-dm-lifecycle-spark="stale_docs"] svg polyline');
    await expect(spark).toBeVisible();
    const points = await spark.getAttribute('points');
    expect(points).not.toBeNull();
    const pointCount = points!.trim().split(/\s+/).length;
    expect(pointCount).toBeGreaterThanOrEqual(2);

    const initialLifecycleRequests = lifecycleRequests;
    const refreshButton = page.locator('[data-dm-lifecycle-refresh]');
    await expect(refreshButton).toBeVisible();

    await Promise.all([
      page.waitForResponse((response) => response.url().endsWith('/lifecycle') && response.request().method() === 'GET'),
      refreshButton.click(),
    ]);

    await expect.poll(() => lifecycleRequests).toBe(initialLifecycleRequests + 1);
    await expect(status).toContainText('Lifecycle metrics updated');

    const releaseRecipe = page.locator('[data-dm-recipe-release]');
    await releaseRecipe.click();
    await expect(status).toContainText('Copied release prep recipe command.');
    await expect.poll(() => readClipboard(page)).toBe('km-recipe-run release-prep --var profile=release');

    const staleRecipe = page.locator('[data-dm-recipe-stale]');
    await staleRecipe.click();
    await expect(status).toContainText('Copied stale audit recipe command.');
    await expect.poll(() => readClipboard(page)).toBe('km-recipe-run stale-audit');

    const downloadPromise = page.waitForEvent('download');
    await page.locator('[data-dm-lifecycle-download]').click();
    const download = await downloadPromise;
    await expect(status).toContainText('Lifecycle report downloaded.');
    expect(download.suggestedFilename()).toMatch(/^lifecycle-.*\.json$/);

    const filePath = await download.path();
    expect(filePath).not.toBeNull();
    if (!filePath) {
      throw new Error('Download path unavailable for lifecycle report');
    }

    const contents = await fs.readFile(filePath, 'utf-8');
    type LifecycleSummary = {
      summary?: {
        stale_docs?: number;
        isolated_nodes?: number;
        removed_artifacts?: number;
      };
    };
    const parsed = JSON.parse(contents) as LifecycleSummary;
    expect(parsed.summary?.stale_docs).toBe(2);
    expect(parsed.summary?.isolated_nodes).toBe(1);
    expect(parsed.summary?.removed_artifacts).toBe(1);
  });
});
