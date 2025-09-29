import { expect, test } from '@playwright/test';

import { bootstrapSession, setSessionTokens } from './helpers';

test.describe('Navigation prompts', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapSession(page);
  });

  test('reflects token requirements across primary views', async ({ page }) => {
    await page.goto('/ui/search');

    const searchLink = page.locator('[data-dm-nav-link="search"]');
    await expect(searchLink).toHaveAttribute('aria-current', 'page');
    await expect(page.locator('[data-dm-search-status]')).toHaveText('Provide a reader token before querying.');

    const subsystemsLink = page.locator('[data-dm-nav-link="subsystems"]');
    await Promise.all([page.waitForNavigation({ url: '**/ui/subsystems' }), subsystemsLink.click()]);
    await expect(subsystemsLink).toHaveAttribute('aria-current', 'page');
    await expect(page.locator('[data-dm-subsystem-status]')).toHaveText('Provide a reader token before exploring subsystems.');

    const lifecycleLink = page.locator('[data-dm-nav-link="lifecycle"]');
    await Promise.all([page.waitForNavigation({ url: '**/ui/lifecycle' }), lifecycleLink.click()]);
    await expect(lifecycleLink).toHaveAttribute('aria-current', 'page');
    await expect(page.locator('[data-dm-lifecycle-status]')).toHaveText('Provide a maintainer token before loading lifecycle metrics.');

    await setSessionTokens(page, { readerToken: 'reader-token', maintainerToken: null });
    await page.reload();
    await expect(page.locator('[data-dm-lifecycle-status]')).toHaveText('Using reader token; maintainer features may be limited.');

    await Promise.all([page.waitForNavigation({ url: '**/ui/search' }), page.locator('[data-dm-nav-link="search"]').click()]);
    await expect(page.locator('[data-dm-search-status]')).toHaveText('Ready. Queries will use the reader token if available.');

    await setSessionTokens(page, { readerToken: 'reader-token', maintainerToken: 'maintainer-token' });
    await page.reload();
    await expect(page.locator('[data-dm-search-status]')).toHaveText('Ready. Queries will use the reader token if available.');

    await Promise.all([page.waitForNavigation({ url: '**/ui/lifecycle' }), page.locator('[data-dm-nav-link="lifecycle"]').click()]);
    await expect(page.locator('[data-dm-lifecycle-status]')).toContainText('Lifecycle metrics updated');
  });
});
