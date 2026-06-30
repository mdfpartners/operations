'use client'

import { useState } from 'react'

interface Field {
  key: string
  label: string
  required?: boolean
  type?: 'text' | 'url' | 'email' | 'tel' | 'checkbox' | 'select'
  options?: { value: string; label: string }[]
}

interface Column {
  key: string
  label: string
  type?: 'url'
  render?: (value: any, row: any) => React.ReactNode
}

interface Props {
  title: string
  items: any[]
  apiBase: string
  fields: Field[]
  columns: Column[]
}

export default function SimpleManager({ title, items, apiBase, fields, columns }: Props) {
  const [list, setList] = useState(items)
  const [editing, setEditing] = useState<any>(null)
  const [isNew, setIsNew] = useState(false)
  const [msg, setMsg] = useState('')

  const emptyForm = fields.reduce((acc, f) => {
    acc[f.key] = f.type === 'checkbox' ? true : ''
    return acc
  }, {} as any)

  async function save() {
    const method = isNew ? 'POST' : 'PATCH'
    const url = isNew ? apiBase : `${apiBase}/${editing.id}`
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

  async function toggleActive(item: any) {
    await fetch(`${apiBase}/${item.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !item.active }),
    })
    window.location.reload()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">{title}</h1>
        <button
          onClick={() => { setEditing({ ...emptyForm }); setIsNew(true) }}
          className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-blue-700"
        >
          + Add
        </button>
      </div>
      {msg && <div className="mb-4 text-sm text-blue-700">{msg}</div>}

      {editing && (
        <div className="bg-white rounded-lg shadow-sm p-5 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4">{isNew ? `New ${title.slice(0, -1)}` : `Edit`}</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {fields.map((f) => (
              <div key={f.key}>
                <label className="text-xs text-gray-500">{f.label}{f.required ? ' *' : ''}</label>
                {f.type === 'checkbox' ? (
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="checkbox"
                      checked={!!editing[f.key]}
                      onChange={(e) => setEditing({ ...editing, [f.key]: e.target.checked })}
                    />
                    <span className="text-sm text-gray-700">{f.label}</span>
                  </div>
                ) : f.type === 'select' ? (
                  <select
                    value={editing[f.key] || ''}
                    onChange={(e) => setEditing({ ...editing, [f.key]: e.target.value })}
                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5"
                  >
                    {f.options?.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                ) : (
                  <input
                    type={f.type || 'text'}
                    value={editing[f.key] || ''}
                    onChange={(e) => setEditing({ ...editing, [f.key]: e.target.value })}
                    className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5"
                  />
                )}
              </div>
            ))}
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
              {columns.map((c) => (
                <th key={c.key} className="text-left px-4 py-3 text-xs font-medium text-gray-600">{c.label}</th>
              ))}
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Status</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {list.map((item) => (
              <tr key={item.id} className={item.active ? '' : 'opacity-50'}>
                {columns.map((c) => (
                  <td key={c.key} className="px-4 py-3 text-gray-700">
                    {c.render ? c.render(item[c.key], item) : c.type === 'url' && item[c.key] ? <a href={item[c.key]} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-xs">{item[c.key]}</a> : item[c.key] || '—'}
                  </td>
                ))}
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${item.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {item.active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => { setEditing({ ...item }); setIsNew(false) }} className="text-sm text-blue-600 hover:underline mr-3">Edit</button>
                  <button onClick={() => toggleActive(item)} className="text-sm text-gray-500 hover:text-gray-700">
                    {item.active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
