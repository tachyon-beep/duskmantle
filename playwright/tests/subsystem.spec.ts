import { promises as fs } from 'fs';

import { expect, test } from '@playwright/test';

import { bootstrapSession, readClipboard } from './helpers';

test.describe('Subsystem explorer', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapSession(page, { readerToken: 'reader-token' });
  });

  test('loads subsystem data and supports copy/download actions', async ({ page }) => {
    const subsystemPayload = {
      subsystem: {
        id: 'Subsystem:ReleaseTooling',
        labels: ['Subsystem'],
        properties: {
          name: 'ReleaseTooling',
          owner: 'Platform Enablement',
          status: 'active',
        },
      },
      artifacts: [
        {
          id: 'Document:docs/release.md',
          properties: {
            path: 'docs/release.md',
            title: 'Release Checklist',
          },
        },
      ],
      related: {
        total: 1,
        nodes: [
          {
            target: {
              id: 'Subsystem:GatewayCore',
              labels: ['Subsystem'],
              properties: {
                name: 'GatewayCore',
              },
            },
            relationship: 'DEPENDS_ON',
            direction: 'OUT',
            hops: 1,
          },
        ],
      },
    };

    await page.route('**/graph/subsystems/**', (route) => {
      void route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(subsystemPayload),
      });
    });

    await page.goto('/ui/subsystems');

    await page.fill('input[name="name"]', 'ReleaseTooling');

    const responsePromise = page.waitForResponse((response) =>
      response.url().includes('/graph/subsystems/ReleaseTooling') && response.request().method() === 'GET',
    );
    await page.locator('#dm-subsystem-form button[type="submit"]').click();
    await responsePromise;

    const status = page.locator('[data-dm-subsystem-status]');
    await expect(status).toHaveText('Loaded 1 of 1 related node(s).');

    const panel = page.locator('[data-dm-subsystem-panel]');
    await expect(panel).toBeVisible();
    await expect(panel.locator('[data-dm-subsystem-title]')).toHaveText('ReleaseTooling');
    await expect(panel.locator('[data-dm-subsystem-related] tbody tr')).toHaveCount(1);
    await expect(panel.locator('[data-dm-subsystem-artifacts] li')).toHaveCount(1);

    await expect(page.locator('[data-dm-subsystem-actions]')).toBeVisible();

    await page.locator('[data-dm-subsystem-copy]').click();
    await expect(status).toHaveText('Copied MCP command to clipboard.');
    await expect.poll(() => readClipboard(page)).toBe('km-graph-subsystem {"name":"ReleaseTooling","depth":2,"limit":15}');

    const downloadPromise = page.waitForEvent('download');
    await page.locator('[data-dm-subsystem-download]').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/^subsystem-ReleaseTooling-\d+\.json$/);

    const downloadPath = await download.path();
    expect(downloadPath).not.toBeNull();
    const raw = downloadPath ? await fs.readFile(downloadPath, 'utf-8') : '{}';
    const parsed = JSON.parse(raw || '{}');
    expect(parsed.related?.total).toBe(1);
    expect(parsed.subsystem?.properties?.name).toBe('ReleaseTooling');
  });
});
