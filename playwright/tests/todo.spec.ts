import { test, expect } from '@playwright/test';

test('should add and complete todos', async ({ page }) => {
  await page.goto('https://demo.playwright.dev/todomvc');
  const input = page.getByPlaceholder('What needs to be done?');
  await input.fill('Learn Kubernetes');
  await input.press('Enter');
  await input.fill('Demo Testkube');
  await input.press('Enter');
  const items = page.getByTestId('todo-item');
  await expect(items).toHaveCount(2);
  await items.first().getByRole('checkbox').check();
  await expect(page.getByText('1 item left')).toBeVisible();
});

test('should filter active todos', async ({ page }) => {
  await page.goto('https://demo.playwright.dev/todomvc');
  const input = page.getByPlaceholder('What needs to be done?');
  await input.fill('Active task');
  await input.press('Enter');
  await input.fill('Completed task');
  await input.press('Enter');
  const items = page.getByTestId('todo-item');
  await items.nth(1).getByRole('checkbox').check();
  await page.getByRole('link', { name: 'Active' }).click();
  await expect(page.getByTestId('todo-item')).toHaveCount(1);
  await expect(page.getByTestId('todo-item')).toHaveText('Active task');
});
