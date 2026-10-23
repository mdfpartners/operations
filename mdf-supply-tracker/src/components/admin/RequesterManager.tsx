'use client'

import { useState } from 'react'

interface Requester {
  id: string
  name: string
  email: string | null
  phone: string | null
  role: string
  request_token: string | null
  active: boolean
  requester_account_permissions?: { account_id: string; accounts: { id: string; name: string } | null }[]
}

const EMPTY_FORM = {
  name: '',
  email: '',
  phone: '',
  role: 'requester',
  active: true,
  accountIds: [] as string[],
}

export default function RequesterManager({
  requesters,
  accounts,
  baseUrl,
}: {
  requesters: Requester[]
  accounts: { id: string; name: string }[]
  baseUrl: string
}) {
  const [editing, setEditing] = useState<(Requester & { accountIds?: string[] }) | null>(null)
  const [isNew, setIsNew] = useState(false)
  const [msg, setMsg] = useState('')
  const [copied, setCopied] = useState<string | null>(null)

  async function save() {
    const method = isNew ? 'POST' : 'PATCH'
    const url = isNew ? '/api/admin/requesters' : `/api/admin/requesters/${editing?.id}`
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editing),
    })
    if (res.ok) {
      setMsg('Saved.')
      setEditing(null)
      window.location.reload()
    } else {
      const d = await res.json()
      setMsg(d.error || 'Error saving')
    }
  }

  async function toggleActive(r: Requester) {
    await fetch(`/api/admin/requesters/${r.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !r.active }),
    })
    window.location.reload()
  }

  function copyLink(token: string) {
    const url = `${baseUrl}/request/${token}`
    navigator.clipboard.writeText(url)
    setCopied(token)
    setTimeout(() => setCopied(null), 2000)
  }

  function startEdit(r: Requester) {
    const accountIds = (r.requester_account_permissions || [])
      .map((p) => p.account_id)
      .filter(Boolean)
    setEditing({ ...r, accountIds })
    setIsNew(false)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Requesters / Site Leads</h1>
        <button
          onClick={() => { setEditing(EMPTY_FORM as unknown as Requester & { accountIds?: string[] }); setIsNew(true) }}
          className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-blue-700"
        >
          + Add Requester
        </button>
      </div>
      {msg && <div className="mb-4 text-sm text-blue-700">{msg}</div>}

      {editing && (
        <div className="bg-white rounded-lg shadow-sm p-5 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4">{isNew ? 'New Requester' : 'Edit Requester'}</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500">Name *</label>
              <input type="text" value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Email</label>
              <input type="email" value={editing.email || ''} onChange={(e) => setEditing({ ...editing, email: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Phone</label>
              <input type="tel" value={editing.phone || ''} onChange={(e) => setEditing({ ...editing, phone: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Role</label>
              <select value={editing.role} onChange={(e) => setEditing({ ...editing, role: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5">
                <option value="requester">Requester / Site Lead</option>
                <option value="analyst">Analyst</option>
                <option value="executive">Executive</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <input type="checkbox" id="active_req" checked={editing.active} onChange={(e) => setEditing({ ...editing, active: e.target.checked })} />
              <label htmlFor="active_req" className="text-sm text-gray-700">Active</label>
            </div>
            {editing.role === 'requester' && (
              <div className="sm:col-span-2">
                <label className="text-xs text-gray-500 mb-1 block">Assigned Accounts</label>
                <div className="grid grid-cols-2 gap-2">
                  {accounts.map((a) => (
                    <label key={a.id} className="flex items-center gap-2 text-sm text-gray-700">
                      <input
                        type="checkbox"
                        checked={editing.accountIds?.includes(a.id)}
                        onChange={(e) => {
                          const ids = editing.accountIds || []
                          setEditing({
                            ...editing,
                            accountIds: e.target.checked ? [...ids, a.id] : ids.filter((id: string) => id !== a.id),
                          })
                        }}
                      />
                      {a.name}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={save} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700">Save</button>
            <button onClick={() => setEditing(null)} className="text-sm text-gray-500 hover:text-gray-700 px-2">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Name</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Email</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Role</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Accounts</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Request Link</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Status</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {requesters.map((r) => {
              const permittedAccounts = (r.requester_account_permissions || [])
                .map((p) => p.accounts?.name)
                .filter(Boolean)
              return (
                <tr key={r.id} className={r.active ? '' : 'opacity-50'}>
                  <td className="px-4 py-3 font-medium text-gray-900">{r.name}</td>
                  <td className="px-4 py-3 text-gray-600">{r.email || '—'}</td>
                  <td className="px-4 py-3 text-gray-600 capitalize">{r.role}</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{permittedAccounts.join(', ') || '—'}</td>
                  <td className="px-4 py-3">
                    {r.request_token ? (
                      <button
                        onClick={() => copyLink(r.request_token!)}
                        className="text-xs text-blue-600 hover:underline"
                      >
                        {copied === r.request_token ? 'Copied!' : 'Copy link'}
                      </button>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${r.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {r.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => startEdit(r)} className="text-sm text-blue-600 hover:underline mr-3">Edit</button>
                    <button onClick={() => toggleActive(r)} className="text-sm text-gray-500 hover:text-gray-700">
                      {r.active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
