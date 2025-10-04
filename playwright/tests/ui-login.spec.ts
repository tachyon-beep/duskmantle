import { expect, test } from '@playwright/test';

import { bootstrapSession } from './helpers';

test.describe('UI password login', () => {
  const password = process.env.KM_UI_PASSWORD ?? '';

  test.skip(password.length === 0, 'KM_UI_PASSWORD must be set for UI login tests');

  test('prompts for password and establishes a session', async ({ page }) => {
    await bootstrapSession(page);

    await page.goto('/ui/login');
    if (page.url().endsWith('/ui/')) {
      const signOut = page.getByRole('button', { name: 'Sign out' });
      if (await signOut.isVisible()) {
        await signOut.click();
      }
      await page.goto('/ui/login');
    }

    await expect(page).toHaveURL(/\/ui\/login/);
    await expect(page.locator('h2', { hasText: 'Sign in to the console' })).toBeVisible();

    const passwordField = page.getByLabel('Password');
    await passwordField.fill('wrong');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL(/error=invalid/);
    await expect(page.getByRole('alert')).toHaveText('Incorrect password, please try again.');

    await passwordField.fill(password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL('/ui/');
    await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible();

    await page.getByRole('button', { name: 'Sign out' }).click();
    await expect(page).toHaveURL(/\/ui\/login/);
  });
});
