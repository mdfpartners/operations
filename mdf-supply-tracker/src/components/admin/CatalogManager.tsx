'use client'

import { useState } from 'react'

interface CatalogItem {
  id: string
  item_name: string
  category: string | null
  unit_of_measure: string | null
  preferred_vendor_id: string | null
  default_notes: string | null
  active: boolean
  preferred_vendor?: { id: string; name: string } | null
}

const EMPTY: Omit<CatalogItem, 'id' | 'preferred_vendor'> = {
  item_name: '',
  category: '',
  unit_of_measure: '',
  preferred_vendor_id: null,
  default_notes: '',
  active: true,
}

export default function CatalogManager({ items, vendors }: { items: CatalogItem[], vendors: { id: string; name: string }[] }) {
  const [list, setList] = useState(items)
  const [editing, setEditing] = useState<CatalogItem | typeof EMPTY | null>(null)
  const [isNew, setIsNew] = useState(false)
  const [msg, setMsg] = useState('')

  async function save() {
    if (!editing) return
    const method = isNew ? 'POST' : 'PATCH'
    const url = isNew ? '/api/admin/catalog' : `/api/admin/catalog/${(editing as CatalogItem).id}`
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
      setMsg(d.error || 'Error')
    }
  }

  async function toggleActive(item: CatalogItem) {
    await fetch(`/api/admin/catalog/${item.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !item.active }),
    })
    window.location.reload()
  }

  const form = editing as any

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Supply Catalog</h1>
        <button
          onClick={() => { setEditing({ ...EMPTY }); setIsNew(true) }}
          className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-blue-700"
        >
          + Add Item
        </button>
      </div>
      {msg && <div className="mb-4 text-sm text-blue-700">{msg}</div>}

      {editing && (
        <div className="bg-white rounded-lg shadow-sm p-5 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4">{isNew ? 'New Catalog Item' : 'Edit Item'}</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500">Item Name *</label>
              <input type="text" value={form.item_name} onChange={(e) => setEditing({ ...form, item_name: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Category</label>
              <input type="text" value={form.category || ''} onChange={(e) => setEditing({ ...form, category: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Unit of Measure</label>
              <input type="text" value={form.unit_of_measure || ''} onChange={(e) => setEditing({ ...form, unit_of_measure: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
            </div>
            <div>
              <label className="text-xs text-gray-500">Preferred Vendor</label>
              <select value={form.preferred_vendor_id || ''} onChange={(e) => setEditing({ ...form, preferred_vendor_id: e.target.value || null })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5">
                <option value="">— None —</option>
                {vendors.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="text-xs text-gray-500">Default Notes</label>
              <textarea rows={2} value={form.default_notes || ''} onChange={(e) => setEditing({ ...form, default_notes: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="active" checked={form.active} onChange={(e) => setEditing({ ...form, active: e.target.checked })} />
              <label htmlFor="active" className="text-sm text-gray-700">Active</label>
            </div>
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
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Item</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Category</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">UOM</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Preferred Vendor</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-600">Status</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {list.map((item) => (
              <tr key={item.id} className={item.active ? '' : 'opacity-50'}>
                <td className="px-4 py-3 font-medium text-gray-900">{item.item_name}</td>
                <td className="px-4 py-3 text-gray-600">{item.category || '—'}</td>
                <td className="px-4 py-3 text-gray-600">{item.unit_of_measure || '—'}</td>
                <td className="px-4 py-3 text-gray-600">{(item as any).preferred_vendor?.name || '—'}</td>
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
