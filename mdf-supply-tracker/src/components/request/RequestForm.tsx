'use client'

import { useState } from 'react'
import { URGENCY_LEVELS } from '@/lib/constants'

interface CatalogItem {
  id: string
  item_name: string
  category: string | null
  unit_of_measure: string | null
}

interface LineItem {
  catalogItemId: string
  otherDescription: string
  quantity: string
}

const EMPTY_LINE: LineItem = { catalogItemId: '', otherDescription: '', quantity: '' }

interface Props {
  accounts: { id: string; name: string }[]
  catalogItems: CatalogItem[]
}

export default function RequestForm({ accounts, catalogItems }: Props) {
  const [requesterName, setRequesterName] = useState('')
  const [requesterEmail, setRequesterEmail] = useState('')
  const [accountId, setAccountId] = useState(accounts.length === 1 ? accounts[0].id : '')
  const [urgency, setUrgency] = useState('')
  const [notes, setNotes] = useState('')
  const [lineItems, setLineItems] = useState<LineItem[]>([{ ...EMPTY_LINE }])
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState<{ orderNumber: string; statusToken?: string } | null>(null)

  function addLineItem() {
    setLineItems((prev) => [...prev, { ...EMPTY_LINE }])
  }

  function removeLineItem(index: number) {
    setLineItems((prev) => prev.filter((_, i) => i !== index))
  }

  function updateLine(index: number, field: keyof LineItem, value: string) {
    setLineItems((prev) => {
      const next = [...prev]
      next[index] = { ...next[index], [field]: value }
      if (field === 'catalogItemId') next[index].otherDescription = ''
      return next
    })
  }

  function validate(): boolean {
    const errs: Record<string, string> = {}
    if (!requesterName.trim()) errs.requesterName = 'Your name is required'
    if (!accountId) errs.accountId = 'Please select an account'
    if (!urgency) errs.urgency = 'Please select an urgency level'
    if (lineItems.length === 0) errs.lineItems = 'At least one item is required'
    lineItems.forEach((li, i) => {
      if (!li.catalogItemId) errs[`line_${i}_item`] = 'Select an item'
      if (li.catalogItemId === 'other' && !li.otherDescription.trim()) {
        errs[`line_${i}_other`] = 'Item description is required'
      }
      const qty = parseInt(li.quantity, 10)
      if (!li.quantity || isNaN(qty) || qty < 1 || String(qty) !== String(Math.floor(Number(li.quantity)))) {
        errs[`line_${i}_qty`] = 'Quantity must be a whole number (1 or more)'
      }
    })
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    try {
      const res = await fetch('/api/request/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requesterName, requesterEmail, accountId, urgency, notes, lineItems }),
      })
      const data = await res.json()
      if (res.ok) {
        setSubmitted({ orderNumber: data.orderNumber, statusToken: data.statusToken })
      } else {
        setErrors({ form: data.error || 'Submission failed — please try again.' })
      }
    } catch {
      setErrors({ form: 'Network error — please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-4xl mb-4">✓</div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Request Submitted!</h2>
        <p className="text-gray-600 mb-4">Your supply request has been received.</p>
        <div className="bg-gray-50 rounded-md px-4 py-3 inline-block">
          <p className="text-sm text-gray-500">Order Number</p>
          <p className="text-2xl font-bold text-blue-700">{submitted.orderNumber}</p>
        </div>
        {requesterEmail && (
          <p className="text-gray-500 text-sm mt-4">
            A confirmation has been sent to <strong>{requesterEmail}</strong>.
          </p>
        )}
        {submitted.statusToken && (
          <p className="mt-3">
            <a href={`/status/${submitted.statusToken}`} className="text-blue-600 hover:underline text-sm">
              Track order status →
            </a>
          </p>
        )}
        <button
          onClick={() => {
            setSubmitted(null)
            setRequesterName('')
            setRequesterEmail('')
            setLineItems([{ ...EMPTY_LINE }])
            setNotes('')
            setUrgency('')
            setAccountId(accounts.length === 1 ? accounts[0].id : '')
            setErrors({})
          }}
          className="mt-6 text-blue-600 hover:text-blue-800 text-sm font-medium underline underline-offset-2"
        >
          Submit another request
        </button>
      </div>
    )
  }

  // Group catalog items by category for dropdown
  const categories = Array.from(new Set(catalogItems.map((c) => c.category || 'Other'))).sort()

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Requester name + email */}
      <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
        <div>
          <label htmlFor="requesterName" className="block text-base font-medium text-gray-800 mb-1.5">
            Your Name <span className="text-red-500">*</span>
          </label>
          <input
            id="requesterName"
            type="text"
            value={requesterName}
            onChange={(e) => setRequesterName(e.target.value)}
            placeholder="First and last name"
            className="w-full border border-gray-300 rounded-md px-3 py-3 text-base text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.requesterName && <p className="text-red-500 text-xs mt-1">{errors.requesterName}</p>}
        </div>
        <div>
          <label htmlFor="requesterEmail" className="block text-base font-medium text-gray-800 mb-1.5">
            Your Email <span className="text-gray-400 font-normal">(optional — for status updates)</span>
          </label>
          <input
            id="requesterEmail"
            type="email"
            value={requesterEmail}
            onChange={(e) => setRequesterEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full border border-gray-300 rounded-md px-3 py-3 text-base text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Account */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <label htmlFor="account" className="block text-base font-medium text-gray-800 mb-1.5">
          Account <span className="text-red-500">*</span>
        </label>
        <select
          id="account"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-3 text-base text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select account…</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
        {errors.accountId && <p className="text-red-500 text-xs mt-1">{errors.accountId}</p>}
      </div>

      {/* Urgency */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <label htmlFor="urgency" className="block text-base font-medium text-gray-800 mb-1.5">
          Urgency <span className="text-red-500">*</span>
        </label>
        <select
          id="urgency"
          value={urgency}
          onChange={(e) => setUrgency(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-3 text-base text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select urgency…</option>
          {URGENCY_LEVELS.map((u) => (
            <option key={u.value} value={u.value}>{u.label}</option>
          ))}
        </select>
        {errors.urgency && <p className="text-red-500 text-xs mt-1">{errors.urgency}</p>}
      </div>

      {/* Line Items */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-gray-700">
            Items Requested <span className="text-red-500">*</span>
          </label>
        </div>
        <div className="space-y-4">
          {lineItems.map((li, i) => {
            const selectedItem = catalogItems.find((c) => c.id === li.catalogItemId)
            return (
              <div key={i} className="border border-gray-200 rounded-md p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-500">Item {i + 1}</span>
                  {lineItems.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeLineItem(i)}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Remove
                    </button>
                  )}
                </div>

                <select
                  value={li.catalogItemId}
                  onChange={(e) => updateLine(i, 'catalogItemId', e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-3 text-base text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select item…</option>
                  {categories.map((cat) => (
                    <optgroup key={cat} label={cat}>
                      {catalogItems
                        .filter((c) => (c.category || 'Other') === cat)
                        .map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.item_name}{c.unit_of_measure ? ` (${c.unit_of_measure})` : ''}
                          </option>
                        ))}
                    </optgroup>
                  ))}
                  <optgroup label="Other">
                    <option value="other">Other (describe below)</option>
                  </optgroup>
                </select>
                {errors[`line_${i}_item`] && (
                  <p className="text-red-500 text-xs">{errors[`line_${i}_item`]}</p>
                )}

                {li.catalogItemId === 'other' && (
                  <div>
                    <input
                      type="text"
                      placeholder="Describe the item…"
                      value={li.otherDescription}
                      onChange={(e) => updateLine(i, 'otherDescription', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-3 text-base text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {errors[`line_${i}_other`] && (
                      <p className="text-red-500 text-xs mt-1">{errors[`line_${i}_other`]}</p>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="1"
                    step="1"
                    placeholder="Qty"
                    value={li.quantity}
                    onChange={(e) => updateLine(i, 'quantity', e.target.value)}
                    className="w-28 border border-gray-300 rounded-md px-3 py-3 text-base text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {selectedItem?.unit_of_measure && (
                    <span className="text-base text-gray-600">{selectedItem.unit_of_measure}</span>
                  )}
                </div>
                {errors[`line_${i}_qty`] && (
                  <p className="text-red-500 text-xs">{errors[`line_${i}_qty`]}</p>
                )}
              </div>
            )
          })}
        </div>
        {errors.lineItems && <p className="text-red-500 text-xs mt-1">{errors.lineItems}</p>}
        <button
          type="button"
          onClick={addLineItem}
          className="mt-3 w-full border border-dashed border-gray-300 rounded-md py-2 text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600"
        >
          + Add another item
        </button>
      </div>

      {/* Notes */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <label htmlFor="notes" className="block text-base font-medium text-gray-800 mb-1.5">
          Notes (optional)
        </label>
        <textarea
          id="notes"
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Any additional notes for the supply team…"
          className="w-full border border-gray-300 rounded-md px-3 py-3 text-base text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {errors.form && (
        <div className="bg-red-50 border border-red-200 rounded-md px-4 py-3 text-sm text-red-700">
          {errors.form}
        </div>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-blue-600 text-white rounded-lg py-3.5 text-base font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? 'Submitting…' : 'Submit Supply Request'}
      </button>
    </form>
  )
}
