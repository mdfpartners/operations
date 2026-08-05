'use client'

import { useState } from 'react'

interface Props {
  settings: Record<string, string>
}

function parseEmails(value: string): string {
  return value
    .split(/[\n,]+/)
    .map((e) => e.trim())
    .filter(Boolean)
    .join('\n')
}

function EmailListField({
  label,
  description,
  value,
  onChange,
}: {
  label: string
  description: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-5">
      <label className="block text-sm font-semibold text-gray-900 mb-0.5">{label}</label>
      <p className="text-xs text-gray-500 mb-3">{description}</p>
      <textarea
        rows={4}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="one@example.com&#10;two@example.com"
        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <p className="text-xs text-gray-400 mt-1">One email per line</p>
    </div>
  )
}

export default function SettingsClient({ settings }: Props) {
  const [internal, setInternal] = useState(
    parseEmails(settings['internal_notification_emails'] || '')
  )
  const [executive, setExecutive] = useState(
    parseEmails(settings['executive_notification_emails'] || '')
  )
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  async function handleSave() {
    setSaving(true)
    setSaved(false)
    setError('')
    try {
      const res = await fetch('/api/admin/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          internal_notification_emails: parseEmails(internal),
          executive_notification_emails: parseEmails(executive),
        }),
      })
      if (!res.ok) throw new Error('Failed to save')
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch {
      setError('Failed to save settings. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="space-y-5">
        <EmailListField
          label="New Order Alerts"
          description="Notified immediately when a supply request is submitted. Typically your supply coordinator(s)."
          value={internal}
          onChange={setInternal}
        />

        <EmailListField
          label="Daily Digest"
          description="Receives the morning aging report with all open orders. Typically management."
          value={executive}
          onChange={setExecutive}
        />
      </div>

      <div className="mt-6 flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-gray-900 text-white px-5 py-2 rounded-md text-sm font-medium hover:bg-gray-700 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save Settings'}
        </button>
        {saved && <span className="text-sm text-green-600 font-medium">Saved ✓</span>}
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>
    </div>
  )
}
