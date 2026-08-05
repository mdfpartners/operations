export const runtime = 'edge'
export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import Link from 'next/link'
import { getAgingBucket } from '@/lib/aging'
import { STATUS_LABELS, URGENCY_LABELS, STATUS_COLORS, URGENCY_COLORS, AGING_COLORS, OPEN_STATUSES } from '@/lib/constants'
import type { OrderStatus, UrgencyLevel } from '@/types'

interface SearchParams {
  status?: string
  urgency?: string
  account?: string
  aging?: string
  show?: string
}

interface PageProps {
  searchParams: Promise<SearchParams>
}

export default async function OrdersPage({ searchParams }: PageProps) {
  const sp = await searchParams
  const showAll = sp.show === 'all'
  const supabase = createSupabaseServiceClient()

  let ordersQuery = supabase
    .from('supply_requests')
    .select(`
      id, order_number, status, urgency, submitted_at, completed_at, cancelled_at, created_at,
      requester_name,
      account:accounts(id, name),
      purchase_details:request_line_items(purchase_details(total_cost))
    `)
    .order('submitted_at', { ascending: false })
    .limit(300)

  if (!showAll) ordersQuery = ordersQuery.in('status', OPEN_STATUSES)
  if (sp.status) ordersQuery = ordersQuery.eq('status', sp.status)
  if (sp.urgency) ordersQuery = ordersQuery.eq('urgency', sp.urgency)
  if (sp.account) ordersQuery = ordersQuery.eq('account_id', sp.account)

  const [{ data: orders }, { data: accounts }] = await Promise.all([
    ordersQuery,
    supabase.from('accounts').select('id, name').eq('active', true).order('name'),
  ])

  const rows = (orders || []).map((o: any) => {
    const agingBucket = getAgingBucket(o.submitted_at, o.status as OrderStatus, o.completed_at, o.cancelled_at)
    const lineItems = (o as any).purchase_details as { purchase_details: { total_cost: number | null }[] }[]
    const totalCost = lineItems
      .flatMap((li) => li.purchase_details)
      .reduce((sum, pd) => sum + (pd?.total_cost || 0), 0)
    return { ...o, agingBucket, totalCost: totalCost > 0 ? totalCost : null, itemCount: lineItems.length }
  })

  const filteredRows = sp.aging ? rows.filter((r: any) => r.agingBucket === sp.aging) : rows

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Orders</h1>
        <Link
          href={showAll ? '/admin/orders' : '/admin/orders?show=all'}
          className="text-sm text-blue-600 hover:underline"
        >
          {showAll ? 'Show open only' : 'Show all'}
        </Link>
      </div>

      <form method="GET" className="flex flex-wrap gap-3 mb-4">
        {showAll && <input type="hidden" name="show" value="all" />}
        <select name="account" defaultValue={sp.account || ''} className="border border-gray-300 rounded-md px-2 py-1.5 text-sm">
          <option value="">All accounts</option>
          {(accounts || []).map((a: any) => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
        <select name="status" defaultValue={sp.status || ''} className="border border-gray-300 rounded-md px-2 py-1.5 text-sm">
          <option value="">All statuses</option>
          {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select name="urgency" defaultValue={sp.urgency || ''} className="border border-gray-300 rounded-md px-2 py-1.5 text-sm">
          <option value="">All urgencies</option>
          {Object.entries(URGENCY_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select name="aging" defaultValue={sp.aging || ''} className="border border-gray-300 rounded-md px-2 py-1.5 text-sm">
          <option value="">All aging</option>
          {['0','1','2','3','4-7','8+'].map((b) => <option key={b} value={b}>{b} day(s)</option>)}
        </select>
        <button type="submit" className="bg-gray-800 text-white px-3 py-1.5 rounded-md text-sm">Filter</button>
        <Link href="/admin/orders" className="text-sm text-gray-500 hover:text-gray-700 py-1.5">Clear</Link>
      </form>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {filteredRows.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-500">No orders found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Order #</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Account</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Requester</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Submitted</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Aging</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Urgency</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">Items</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">Total Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredRows.map((o: any) => {
                  const account = o.account as { id: string; name: string } | null
                  return (
                    <tr key={o.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <Link href={`/admin/orders/${o.id}`} className="font-medium text-blue-600 hover:underline">
                          {o.order_number}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-gray-700">{account?.name}</td>
                      <td className="px-4 py-3 text-gray-700">{o.requester_name}</td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(o.submitted_at).toLocaleDateString('en-US', { timeZone: 'America/Chicago' })}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${AGING_COLORS[o.agingBucket]}`}>
                          {o.agingBucket}d
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[o.status as OrderStatus]}`}>
                          {STATUS_LABELS[o.status as OrderStatus]}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${URGENCY_COLORS[o.urgency as UrgencyLevel]}`}>
                          {URGENCY_LABELS[o.urgency as UrgencyLevel]}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-gray-500 text-sm">{o.itemCount}</td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {o.totalCost != null ? `$${o.totalCost.toFixed(2)}` : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
