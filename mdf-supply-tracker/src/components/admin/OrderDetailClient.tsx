'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  STATUS_LABELS, URGENCY_LABELS, STATUS_COLORS, URGENCY_COLORS,
  AGING_COLORS, ORDER_STATUSES,
} from '@/lib/constants'
import type { AgingBucket, OrderStatus } from '@/types'

interface Props {
  order: any
  agingBucket: AgingBucket
  daysOutstanding: number
  recentRequests: any[]
  auditLog: any[]
  vendors: { id: string; name: string }[]
}

export default function OrderDetailClient({ order, agingBucket, daysOutstanding, recentRequests, auditLog, vendors }: Props) {
  const [status, setStatus] = useState<OrderStatus>(order.status)
  const [internalNotes, setInternalNotes] = useState(order.internal_notes || '')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [purchaseForms, setPurchaseForms] = useState<Record<string, any>>({})
  const [savingPurchase, setSavingPurchase] = useState<Record<string, boolean>>({})

  const account = order.account as { id: string; name: string } | null
  const requester = order.requester as { id: string; name: string; email: string | null } | null

  async function saveOrderChanges() {
    setSaving(true)
    setMessage('')
    const res = await fetch(`/api/admin/orders/${order.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, internalNotes }),
    })
    setSaving(false)
    if (res.ok) {
      setMessage('Saved.')
      setTimeout(() => window.location.reload(), 800)
    } else {
      const d = await res.json()
      setMessage(d.error || 'Save failed')
    }
  }

  function initPurchaseForm(lineItemId: string, existing: any) {
    setPurchaseForms((prev) => ({
      ...prev,
      [lineItemId]: existing
        ? {
            vendorId: existing.vendor_id || '',
            productUrl: existing.product_url || '',
            productName: existing.product_name || '',
            quantityPurchased: existing.quantity_purchased ?? '',
            unitCost: existing.unit_cost ?? '',
            tax: existing.tax ?? '',
            shipping: existing.shipping ?? '',
            totalCost: existing.total_cost ?? '',
            orderConfirmationNumber: existing.order_confirmation_number || '',
            estimatedDeliveryDate: existing.estimated_delivery_date || '',
            purchaseDetailId: existing.id,
          }
        : {
            vendorId: '',
            productUrl: '',
            productName: '',
            quantityPurchased: '',
            unitCost: '',
            tax: '',
            shipping: '',
            totalCost: '',
            orderConfirmationNumber: '',
            estimatedDeliveryDate: '',
            purchaseDetailId: null,
          },
    }))
  }

  function updatePurchaseField(lineItemId: string, field: string, value: string) {
    setPurchaseForms((prev) => ({
      ...prev,
      [lineItemId]: { ...prev[lineItemId], [field]: value },
    }))
  }

  async function savePurchaseDetail(lineItemId: string) {
    const form = purchaseForms[lineItemId]
    if (!form) return
    setSavingPurchase((prev) => ({ ...prev, [lineItemId]: true }))
    const res = await fetch(`/api/admin/orders/${order.id}/purchase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lineItemId, ...form }),
    })
    setSavingPurchase((prev) => ({ ...prev, [lineItemId]: false }))
    if (res.ok) {
      setMessage('Purchase details saved.')
      setTimeout(() => window.location.reload(), 800)
    } else {
      const d = await res.json()
      setMessage(d.error || 'Save failed')
    }
  }

  const lineItems = order.request_line_items as any[] || []

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link href="/admin/orders" className="text-sm text-gray-500 hover:text-gray-700">← Orders</Link>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{order.order_number}</h1>
          <p className="text-gray-500">{account?.name}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[status]}`}>
            {STATUS_LABELS[status]}
          </span>
          <span className={`px-2 py-1 rounded-full text-sm font-medium ${AGING_COLORS[agingBucket]}`}>
            {agingBucket}d
          </span>
        </div>
      </div>

      {message && (
        <div className="bg-blue-50 border border-blue-200 rounded px-4 py-2 text-sm text-blue-800">{message}</div>
      )}

      {/* Summary */}
      <div className="bg-white rounded-lg shadow-sm p-5 grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
        <div><p className="text-xs text-gray-500">Requester</p><p className="font-medium">{requester?.name}</p></div>
        <div><p className="text-xs text-gray-500">Email</p><p>{requester?.email || '—'}</p></div>
        <div><p className="text-xs text-gray-500">Urgency</p>
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${(URGENCY_COLORS as any)[order.urgency]}`}>
            {(URGENCY_LABELS as any)[order.urgency]}
          </span>
        </div>
        <div><p className="text-xs text-gray-500">Submitted</p>
          <p>{new Date(order.submitted_at).toLocaleString('en-US', { timeZone: 'America/Chicago' })}</p>
        </div>
        <div><p className="text-xs text-gray-500">Days Outstanding</p><p className="font-medium">{daysOutstanding}</p></div>
        <div><p className="text-xs text-gray-500">Requester Notes</p><p>{order.requester_notes || '—'}</p></div>
      </div>

      {/* Status + Internal Notes */}
      <div className="bg-white rounded-lg shadow-sm p-5 space-y-4">
        <h2 className="font-semibold text-gray-900">Update Order</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as OrderStatus)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              {ORDER_STATUSES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Internal Notes</label>
            <textarea
              rows={3}
              value={internalNotes}
              onChange={(e) => setInternalNotes(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
        </div>
        <button
          onClick={saveOrderChanges}
          disabled={saving}
          className="bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save Changes'}
        </button>
      </div>

      {/* Line Items + Purchase Details */}
      <div className="bg-white rounded-lg shadow-sm p-5">
        <h2 className="font-semibold text-gray-900 mb-4">Line Items</h2>
        <div className="space-y-4">
          {lineItems.map((li: any) => {
            const itemName = li.catalog_item?.item_name || li.other_item_description || 'Unknown'
            const uom = li.catalog_item?.unit_of_measure
            const existingPD = li.purchase_details?.[0]
            const form = purchaseForms[li.id]
            return (
              <div key={li.id} className="border border-gray-200 rounded-md p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-medium text-gray-900">{itemName}{uom ? ` (${uom})` : ''}</p>
                    <p className="text-sm text-gray-500">Requested: {li.quantity_requested}{li.quantity_purchased ? ` | Purchased: ${li.quantity_purchased}` : ''}</p>
                    {li.catalog_item?.category && <p className="text-xs text-gray-400">{li.catalog_item.category}</p>}
                  </div>
                  {!form && (
                    <button
                      onClick={() => initPurchaseForm(li.id, existingPD)}
                      className="text-sm text-blue-600 hover:underline"
                    >
                      {existingPD ? 'Edit purchase' : '+ Add purchase'}
                    </button>
                  )}
                </div>

                {existingPD && !form && (
                  <div className="bg-gray-50 rounded p-3 text-xs text-gray-600 grid grid-cols-2 gap-2 mt-2">
                    <div><span className="font-medium">Vendor:</span> {existingPD.vendor?.name || '—'}</div>
                    <div><span className="font-medium">Product:</span> {existingPD.product_name || '—'}</div>
                    <div><span className="font-medium">Qty:</span> {existingPD.quantity_purchased ?? '—'}</div>
                    <div><span className="font-medium">Unit cost:</span> {existingPD.unit_cost != null ? `$${existingPD.unit_cost}` : '—'}</div>
                    <div><span className="font-medium">Total:</span> {existingPD.total_cost != null ? `$${existingPD.total_cost}` : '—'}</div>
                    <div><span className="font-medium">Confirmation:</span> {existingPD.order_confirmation_number || '—'}</div>
                    <div><span className="font-medium">Est. delivery:</span> {existingPD.estimated_delivery_date || '—'}</div>
                  </div>
                )}

                {form && (
                  <div className="mt-3 border-t pt-3 grid sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-gray-500">Vendor</label>
                      <select
                        value={form.vendorId}
                        onChange={(e) => updatePurchaseField(li.id, 'vendorId', e.target.value)}
                        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5"
                      >
                        <option value="">— Select vendor —</option>
                        {vendors.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Product Name</label>
                      <input type="text" value={form.productName} onChange={(e) => updatePurchaseField(li.id, 'productName', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Product URL</label>
                      <input type="url" value={form.productUrl} onChange={(e) => updatePurchaseField(li.id, 'productUrl', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" placeholder="https://" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Qty Purchased</label>
                      <input type="number" value={form.quantityPurchased} onChange={(e) => updatePurchaseField(li.id, 'quantityPurchased', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Unit Cost ($)</label>
                      <input type="number" step="0.01" value={form.unitCost} onChange={(e) => updatePurchaseField(li.id, 'unitCost', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Tax ($)</label>
                      <input type="number" step="0.01" value={form.tax} onChange={(e) => updatePurchaseField(li.id, 'tax', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Shipping ($)</label>
                      <input type="number" step="0.01" value={form.shipping} onChange={(e) => updatePurchaseField(li.id, 'shipping', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Total Cost ($)</label>
                      <input type="number" step="0.01" value={form.totalCost} onChange={(e) => updatePurchaseField(li.id, 'totalCost', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Confirmation #</label>
                      <input type="text" value={form.orderConfirmationNumber} onChange={(e) => updatePurchaseField(li.id, 'orderConfirmationNumber', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Est. Delivery Date</label>
                      <input type="date" value={form.estimatedDeliveryDate} onChange={(e) => updatePurchaseField(li.id, 'estimatedDeliveryDate', e.target.value)} className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-0.5" />
                    </div>
                    <div className="sm:col-span-2 flex gap-2">
                      <button
                        onClick={() => savePurchaseDetail(li.id)}
                        disabled={savingPurchase[li.id]}
                        className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                      >
                        {savingPurchase[li.id] ? 'Saving…' : 'Save Purchase'}
                      </button>
                      <button
                        onClick={() => setPurchaseForms((p) => { const next = { ...p }; delete next[li.id]; return next })}
                        className="text-sm text-gray-500 hover:text-gray-700 px-2"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent similar requests */}
      {recentRequests.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-5">
          <h2 className="font-semibold text-yellow-900 mb-3">Recent Requests — Same Account (last 14 days)</h2>
          <div className="space-y-2">
            {recentRequests.map((r: any) => {
              const items = (r.request_line_items as any[] || [])
                .map((li: any) => li.catalog_item?.item_name || li.other_item_description)
                .filter(Boolean)
                .join(', ')
              return (
                <div key={r.id} className="flex items-center gap-4 text-sm text-yellow-800">
                  <Link href={`/admin/orders/${r.id}`} className="font-medium text-blue-600 hover:underline">{r.order_number}</Link>
                  <span>{new Date(r.submitted_at).toLocaleDateString()}</span>
                  <span className="text-yellow-700">{STATUS_LABELS[r.status as OrderStatus]}</span>
                  <span className="text-gray-600 truncate">{items}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Audit Log */}
      <div className="bg-white rounded-lg shadow-sm p-5">
        <h2 className="font-semibold text-gray-900 mb-3">Audit History</h2>
        {auditLog.length === 0 ? (
          <p className="text-sm text-gray-500">No audit entries yet.</p>
        ) : (
          <div className="space-y-2">
            {auditLog.map((entry: any) => (
              <div key={entry.id} className="text-sm border-b border-gray-100 pb-2 last:border-0">
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 text-xs">{new Date(entry.created_at).toLocaleString()}</span>
                  <span className="font-medium text-gray-700">{entry.actor_name}</span>
                  <span className="text-gray-500">{entry.action.replace(/_/g, ' ')}</span>
                </div>
                {entry.notes && <p className="text-gray-500 text-xs ml-0 mt-0.5">{entry.notes}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
