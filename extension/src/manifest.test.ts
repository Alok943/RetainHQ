import { describe, it, expect } from 'vitest'
import manifest from '../manifest.json'

// Regression guard for the Firefox port (IMPLEMENTATION-companion-firefox.md).
// These assert on the SOURCE manifest.json (not a build output) since that's
// what's checked in and what a future edit could silently break.
describe('manifest — dual Chrome/Firefox target', () => {
  it('declares both background entry points, same file', () => {
    expect(manifest.background.service_worker).toBeTruthy()
    expect(manifest.background.scripts).toContain(manifest.background.service_worker)
  })

  it('sets a gecko id for Firefox signing', () => {
    expect(manifest.browser_specific_settings?.gecko?.id).toBe('companion@retainhq.app')
  })

  it('requires at least Firefox 128 — the optional_host_permissions floor the consent flow depends on', () => {
    const min = parseFloat(manifest.browser_specific_settings?.gecko?.strict_min_version ?? '0')
    expect(min).toBeGreaterThanOrEqual(128)
  })

  it('declares data collection permissions (mandatory for new Firefox extensions since Nov 2025)', () => {
    expect(manifest.browser_specific_settings?.gecko?.data_collection_permissions?.required).toEqual(['browsingActivity'])
  })

  it('declares the LeetCode reflection free-text note as optional personallyIdentifyingInfo, separate from the base browsingActivity track', () => {
    // The "biggest mistake" field (src/content/leetcode.ts) is unconstrained
    // user-typed free text, unlike titles/domains/durations — Mozilla's opt-in
    // rule for personal data means it can't ride on `required` (IMPLEMENTATION-amo-submission.md §2).
    expect(manifest.browser_specific_settings?.gecko?.data_collection_permissions?.optional).toEqual(['personallyIdentifyingInfo'])
  })
})
