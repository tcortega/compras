export function isStagingTriageEnabled(): boolean {
  const raw = (process.env.STAGING_TRIAGE ?? '').trim().toLowerCase()
  return raw !== '0' && raw !== 'false' && raw !== 'off'
}
