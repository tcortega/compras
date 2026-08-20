import { expect, type Page } from '@playwright/test'

export const banned = /fraude|corrupto|roubo|\bflag\b|ranking|adjacenc|shared_qsa|shared_partner/i
export const bannedKinds = /cnae_mismatch/
export const againstCompose = Boolean(process.env.PLAYWRIGHT_BASE_URL)

export async function assertCoverageAndBan(page: Page) {
  await expect(page.getByText(/n=\d+/).first()).toBeVisible()
  await expect(
    page.getByText(/UF RJ|UF SP|UF RS|UF SC|UF MG|UF PR|UF BA|UF PE|UF GO|UF ES|UF PB|UF CE|UF MA|UF AL|UF MS|UF PA|UF MT|UF RO|UF RN|UF AC|UF AP|UF RR|UF mista|filtro sem registros/).first(),
  ).toBeVisible()
  await expect(page.getByText(/trimestre|trim\./i).first()).toBeVisible()
  await expect(page.getByText(/metodologia/i).first()).toBeVisible()
  await expect(page.locator('body')).not.toHaveText(banned)
  await expect(page.locator('body')).not.toHaveText(bannedKinds)
}

export async function firstTableName(page: Page, path: string): Promise<string> {
  await page.goto(path)
  const link = page.locator('table.data tbody a').first()
  await expect(link).toBeVisible()
  return (await link.innerText()).trim()
}
