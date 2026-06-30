'use client'

import { useState, useRef } from 'react'
import Papa from 'papaparse'

type ImportType = 'accounts' | 'requesters' | 'vendors' | 'supply_catalog' | 'requester_account_permissions'

interface PreviewRow {
  rowNumber: number
  data: Record<string, string>
  action: 'insert' | 'update' | 'rejected'
  errors: string[]
}

interface ImportSummary {
  total: number
  inserted: number
  updated: number
  rejected: number
  duplicates: number
}

const IMPORT_TYPES: { value: ImportType; label: string }[] = [
  { value: 'accounts', label: 'Accounts' },
  { value: 'requesters', label: 'Requesters' },
  { value: 'vendors', label: 'Vendors' },
  { value: 'supply_catalog', label: 'Supply Catalog' },
  { value: 'requester_account_permissions', label: 'Requester Account Permissions' },
]

const TEMPLATES: Record<ImportType, { headers: string[]; example: string[] }> = {
  accounts: {
    headers: ['account_name', 'location', 'active'],
    example: ['Woodford County', 'Eureka, IL', 'true'],
  },
  requesters: {
    headers: ['name', 'email', 'phone', 'role', 'active'],
    example: ['Jane Doe', 'jane@example.com', '309-555-0101', 'requester', 'true'],
  },
  vendors: {
    headers: ['vendor_name', 'website', 'active'],
    example: ['Grainger', 'https://www.grainger.com', 'true'],
  },
  supply_catalog: {
    headers: ['item_name', 'category', 'unit_of_measure', 'preferred_vendor_name', 'default_notes', 'active'],
    example: ['Paper Towels', 'Paper Products', 'Case', 'Amazon Business', '', 'true'],
  },
  requester_account_permissions: {
    headers: ['requester_email', 'account_name'],
    example: ['jane@example.com', 'Woodford County'],
  },
}

export default function ImportExportClient() {
  const [importType, setImportType] = useState<ImportType>('accounts')
  const [previewRows, setPreviewRows] = useState<PreviewRow[] | null>(null)
  const [fileName, setFileName] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [summary, setSummary] = useState<ImportSummary | null>(null)
  const [msg, setMsg] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  function downloadTemplate() {
    const tpl = TEMPLATES[importType]
    const csv = [tpl.headers.join(','), tpl.example.join(',')].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mdf_${importType}_template.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function downloadExport(type: ImportType) {
    const res = await fetch(`/api/admin/import/export?type=${type}`)
    if (!res.ok) { setMsg('Export failed'); return }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mdf_${type}_export.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setFileName(file.name)
    setPreviewRows(null)
    setSummary(null)
    setMsg('')

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (results) => {
        if (results.data.length > 500) {
          setMsg('Import capped at 500 rows. Please split your file.')
          return
        }
        const res = await fetch('/api/admin/import/preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type: importType, rows: results.data }),
        })
        const data = await res.json()
        if (res.ok) {
          setPreviewRows(data.rows)
        } else {
          setMsg(data.error || 'Preview failed')
        }
      },
      error: () => setMsg('Failed to parse CSV file'),
    })
  }

  async function confirmImport() {
    if (!previewRows) return
    setConfirming(true)
    const res = await fetch('/api/admin/import/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: importType, rows: previewRows, fileName }),
    })
    const data = await res.json()
    setConfirming(false)
    if (res.ok) {
      setSummary(data.summary)
      setPreviewRows(null)
      if (fileRef.current) fileRef.current.value = ''
    } else {
      setMsg(data.error || 'Import failed')
    }
  }

  function reset() {
    setPreviewRows(null)
    setSummary(null)
    setMsg('')
    setFileName('')
    if (fileRef.current) fileRef.current.value = ''
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Import / Export</h1>

      {/* Export section */}
      <div className="bg-white rounded-lg shadow-sm p-5 mb-6">
        <h2 className="font-semibold text-gray-900 mb-3">Export Data</h2>
        <div className="flex flex-wrap gap-2">
          {IMPORT_TYPES.map((t) => (
            <button
              key={t.value}
              onClick={() => downloadExport(t.value)}
              className="text-sm border border-gray-300 rounded px-3 py-1.5 hover:bg-gray-50 text-gray-700"
            >
              Export {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Import section */}
      <div className="bg-white rounded-lg shadow-sm p-5">
        <h2 className="font-semibold text-gray-900 mb-4">Import Data</h2>

        <div className="flex flex-wrap items-end gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Import Type</label>
            <select
              value={importType}
              onChange={(e) => { setImportType(e.target.value as ImportType); reset() }}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm"
            >
              {IMPORT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <button onClick={downloadTemplate} className="text-sm text-blue-600 hover:underline">
            Download template
          </button>
        </div>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center mb-4">
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            onChange={handleFile}
            className="hidden"
            id="csv-upload"
          />
          <label htmlFor="csv-upload" className="cursor-pointer">
            <p className="text-sm text-gray-600">Click to upload a CSV file</p>
            <p className="text-xs text-gray-400 mt-1">Max 500 rows</p>
            {fileName && <p className="text-sm font-medium text-blue-700 mt-2">{fileName}</p>}
          </label>
        </div>

        {msg && <div className="text-sm text-red-600 mb-4">{msg}</div>}

        {summary && (
          <div className="bg-green-50 border border-green-200 rounded p-4 mb-4">
            <p className="font-semibold text-green-800 mb-2">Import Complete</p>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-sm">
              <div><p className="text-xs text-gray-500">Total</p><p className="font-medium">{summary.total}</p></div>
              <div><p className="text-xs text-gray-500">Inserted</p><p className="font-medium text-green-700">{summary.inserted}</p></div>
              <div><p className="text-xs text-gray-500">Updated</p><p className="font-medium text-blue-700">{summary.updated}</p></div>
              <div><p className="text-xs text-gray-500">Rejected</p><p className="font-medium text-red-700">{summary.rejected}</p></div>
              <div><p className="text-xs text-gray-500">Duplicates</p><p className="font-medium text-orange-700">{summary.duplicates}</p></div>
            </div>
          </div>
        )}

        {previewRows && (
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Preview ({previewRows.length} rows)</h3>
            <div className="overflow-x-auto mb-4 max-h-96 overflow-y-auto border border-gray-200 rounded">
              <table className="min-w-full text-xs">
                <thead className="bg-gray-50 border-b sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left text-gray-600">#</th>
                    <th className="px-3 py-2 text-left text-gray-600">Action</th>
                    {Object.keys(previewRows[0]?.data || {}).map((k) => (
                      <th key={k} className="px-3 py-2 text-left text-gray-600">{k}</th>
                    ))}
                    <th className="px-3 py-2 text-left text-gray-600">Errors</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {previewRows.map((row) => (
                    <tr key={row.rowNumber} className={row.action === 'rejected' ? 'bg-red-50' : row.action === 'update' ? 'bg-blue-50' : ''}>
                      <td className="px-3 py-2 text-gray-500">{row.rowNumber}</td>
                      <td className="px-3 py-2">
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                          row.action === 'insert' ? 'bg-green-100 text-green-700' :
                          row.action === 'update' ? 'bg-blue-100 text-blue-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {row.action}
                        </span>
                      </td>
                      {Object.values(row.data).map((v, i) => (
                        <td key={i} className="px-3 py-2 text-gray-700">{v}</td>
                      ))}
                      <td className="px-3 py-2 text-red-600">{row.errors.join('; ') || ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex gap-3">
              <button
                onClick={confirmImport}
                disabled={confirming || previewRows.every((r) => r.action === 'rejected')}
                className="bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {confirming ? 'Importing…' : 'Confirm Import'}
              </button>
              <button onClick={reset} className="text-sm text-gray-500 hover:text-gray-700 px-2">Cancel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
