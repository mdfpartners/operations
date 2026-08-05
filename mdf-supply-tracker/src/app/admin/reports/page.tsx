export const runtime = 'edge'
export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { getAgingBucket } from '@/lib/aging'
import { STATUS_LABELS, OPEN_STATUSES } from '@/lib/constants'
import type { OrderStatus } from '@/types'
import Link from 'next/link'

interface ReportsPageProps {
  searchParams: Promise<{ from?: string; to?: string }>
}

export default async function ReportsPage({ searchParams }: ReportsPageProps) {
  const sp = await searchParams
  const fromDate = sp.from || ''
  const toDate = sp.to || ''

  const supabase = createSupabaseServiceClient()

  let ordersQuery = supabase
    .from('supply_requests')
    .select(`
      id, order_number, status, urgency, submitted_at, completed_at, cancelled_at,
      account:accounts(id, name),
      requester:app_users(id, name),
      request_line_items(
        purchase_details(total_cost, vendor_id, vendors(name)),
        supply_catalog(item_name, category)
      )
    `)
  if (fromDate) ordersQuery = ordersQuery.gte('submitted_at', fromDate)
  if (toDate) ordersQuery = ordersQuery.lte('submitted_at', toDate + 'T23:59:59')

  const { data: orders } = await ordersQuery

  const all: any[] = orders || []
  const open = all.filter((o) => OPEN_STATUSES.includes(o.status as OrderStatus))

  // Open orders by status
  const byStatus: Record<string, number> = {}
  for (const o of open) byStatus[o.status] = (byStatus[o.status] || 0) + 1

  // Open orders by aging bucket
  const byAging: Record<string, number> = {}
  for (const o of open) {
    const bucket = getAgingBucket(o.submitted_at, o.status as OrderStatus, o.completed_at, o.cancelled_at)
    byAging[bucket] = (byAging[bucket] || 0) + 1
  }

  // Spend by account
  const spendByAccount: Record<string, { name: string; total: number }> = {}
  for (const o of all) {
    const acc = (o as any).account as { id: string; name: string } | null
    if (!acc) continue
    const items = (o as any).request_line_items as any[] || []
    const cost = items.flatMap((li: any) => li.purchase_details || []).reduce((s: number, pd: any) => s + (pd.total_cost || 0), 0)
    if (!spendByAccount[acc.id]) spendByAccount[acc.id] = { name: acc.name, total: 0 }
    spendByAccount[acc.id].total += cost
  }

  // Spend by vendor
  const spendByVendor: Record<string, { name: string; total: number }> = {}
  for (const o of all) {
    const items = (o as any).request_line_items as any[] || []
    for (const li of items) {
      for (const pd of (li.purchase_details || [])) {
        const vname = pd.vendors?.name || 'Unknown Vendor'
        const vid = pd.vendor_id || 'unknown'
        if (!spendByVendor[vid]) spendByVendor[vid] = { name: vname, total: 0 }
        spendByVendor[vid].total += pd.total_cost || 0
      }
    }
  }

  // Spend by category
  const spendByCategory: Record<string, number> = {}
  for (const o of all) {
    const items = (o as any).request_line_items as any[] || []
    for (const li of items) {
      const cat = li.supply_catalog?.category || 'Other'
      const cost = (li.purchase_details || []).reduce((s: number, pd: any) => s + (pd.total_cost || 0), 0)
      spendByCategory[cat] = (spendByCategory[cat] || 0) + cost
    }
  }

  // Average days to complete
  const completed = all.filter((o) => o.status === 'complete_received' && o.completed_at)
  const avgDays = completed.length
    ? (completed.reduce((s, o) => {
        const ms = new Date(o.completed_at!).getTime() - new Date(o.submitted_at).getTime()
        return s + ms / 86400000
      }, 0) / completed.length).toFixed(1)
    : null

  // Emergency/out-of-stock open by requester
  const emergencyOpen = open.filter((o) =>
    o.urgency === 'emergency_service_impacting' || o.urgency === 'out_of_stock'
  )
  const emergencyByRequester: Record<string, { name: string; count: number }> = {}
  for (const o of emergencyOpen) {
    const req = (o as any).requester as { id: string; name: string } | null
    if (!req) continue
    if (!emergencyByRequester[req.id]) emergencyByRequester[req.id] = { name: req.name, count: 0 }
    emergencyByRequester[req.id].count++
  }

  // Delayed orders
  const delayed = all.filter((o) => o.status === 'delayed')
  // Cancelled orders (last 30 days)
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
  const recentCancelled = all.filter((o) => o.status === 'cancelled' && o.cancelled_at && new Date(o.cancelled_at) > thirtyDaysAgo)

  const eightPlusOpen = open.filter((o) => {
    const bucket = getAgingBucket(o.submitted_at, o.status as OrderStatus, o.completed_at, o.cancelled_at)
    return bucket === '8+'
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Reports</h1>
        <div className="flex items-center gap-4">
          <Link href="/admin/reports/spend-by-account" className="text-sm text-blue-600 hover:underline">Spend by Account →</Link>
          <Link href="/admin/reports/spend-by-item" className="text-sm text-blue-600 hover:underline">Spend by Item →</Link>
          <Link href="/admin/reports/by-requester" className="text-sm text-blue-600 hover:underline">By Requester →</Link>
          <a href="/api/admin/reports/export-orders" className="text-sm text-blue-600 hover:underline">Export CSV</a>
        </div>
      </div>

      {/* Date range filter */}
      <form method="GET" className="flex flex-wrap items-end gap-3 bg-white rounded-lg shadow-sm p-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input
            type="date"
            name="from"
            defaultValue={fromDate}
            className="border border-gray-300 rounded px-2 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input
            type="date"
            name="to"
            defaultValue={toDate}
            className="border border-gray-300 rounded px-2 py-1.5 text-sm"
          />
        </div>
        <button type="submit" className="bg-gray-800 text-white px-3 py-1.5 rounded text-sm">Apply</button>
        {(fromDate || toDate) && (
          <a href="/admin/reports" className="text-sm text-gray-500 hover:text-gray-700 py-1.5">Clear</a>
        )}
        {(fromDate || toDate) && (
          <span className="text-xs text-blue-700 py-1.5">
            Showing {fromDate || 'all time'} → {toDate || 'today'}
          </span>
        )}
      </form>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <p className="text-xs text-gray-500">Open Orders</p>
          <p className="text-3xl font-bold text-gray-900">{open.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4">
          <p className="text-xs text-gray-500">8+ Day Open</p>
          <p className="text-3xl font-bold text-red-700">{eightPlusOpen.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4">
          <p className="text-xs text-gray-500">Emergency / OOS Open</p>
          <p className="text-3xl font-bold text-orange-700">{emergencyOpen.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4">
          <p className="text-xs text-gray-500">Avg Days to Complete</p>
          <p className="text-3xl font-bold text-gray-900">{avgDays ?? '—'}</p>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-6">
        {/* Open orders by status */}
        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-3">Open Orders by Status</h2>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {Object.entries(byStatus).sort((a, b) => b[1] - a[1]).map(([s, c]) => (
                <tr key={s}><td className="py-1.5 text-gray-700">{STATUS_LABELS[s as OrderStatus]}</td><td className="py-1.5 font-medium text-right">{c}</td></tr>
              ))}
              {Object.keys(byStatus).length === 0 && <tr><td className="py-2 text-gray-400" colSpan={2}>No open orders</td></tr>}
            </tbody>
          </table>
        </div>

        {/* Open orders by aging */}
        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-3">Open Orders by Aging</h2>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {['0','1','2','3','4-7','8+'].map((b) => (
                <tr key={b}><td className="py-1.5 text-gray-700">{b} day(s)</td><td className="py-1.5 font-medium text-right">{byAging[b] || 0}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Spend by account */}
        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-3">Spend by Account</h2>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {Object.values(spendByAccount).sort((a, b) => b.total - a.total).map((a) => (
                <tr key={a.name}><td className="py-1.5 text-gray-700">{a.name}</td><td className="py-1.5 font-medium text-right">${a.total.toFixed(2)}</td></tr>
              ))}
              {Object.keys(spendByAccount).length === 0 && <tr><td className="py-2 text-gray-400" colSpan={2}>No spend data</td></tr>}
            </tbody>
          </table>
        </div>

        {/* Spend by vendor */}
        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-3">Spend by Vendor</h2>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {Object.values(spendByVendor).filter(v => v.total > 0).sort((a, b) => b.total - a.total).map((v) => (
                <tr key={v.name}><td className="py-1.5 text-gray-700">{v.name}</td><td className="py-1.5 font-medium text-right">${v.total.toFixed(2)}</td></tr>
              ))}
              {Object.values(spendByVendor).filter(v => v.total > 0).length === 0 && <tr><td className="py-2 text-gray-400" colSpan={2}>No spend data</td></tr>}
            </tbody>
          </table>
        </div>

        {/* Spend by category */}
        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-3">Spend by Category</h2>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {Object.entries(spendByCategory).filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]).map(([cat, total]) => (
                <tr key={cat}><td className="py-1.5 text-gray-700">{cat}</td><td className="py-1.5 font-medium text-right">${total.toFixed(2)}</td></tr>
              ))}
              {Object.values(spendByCategory).every(v => v === 0) && <tr><td className="py-2 text-gray-400" colSpan={2}>No spend data</td></tr>}
            </tbody>
          </table>
        </div>

        {/* Emergency / OOS by requester */}
        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-3">Emergency / OOS Open Requests by Requester</h2>
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {Object.values(emergencyByRequester).sort((a, b) => b.count - a.count).map((r) => (
                <tr key={r.name}><td className="py-1.5 text-gray-700">{r.name}</td><td className="py-1.5 font-medium text-right">{r.count}</td></tr>
              ))}
              {Object.keys(emergencyByRequester).length === 0 && <tr><td className="py-2 text-gray-400" colSpan={2}>None</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      {/* Delayed orders */}
      {delayed.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="font-semibold text-gray-900 mb-3">Delayed Orders</h2>
          <table className="w-full text-sm">
            <thead><tr className="border-b"><th className="text-left py-1.5 text-xs text-gray-500">Order #</th><th className="text-left py-1.5 text-xs text-gray-500">Account</th><th className="text-left py-1.5 text-xs text-gray-500">Submitted</th></tr></thead>
            <tbody className="divide-y divide-gray-100">
              {delayed.map((o) => (
                <tr key={o.id}>
                  <td className="py-1.5"><Link href={`/admin/orders/${o.id}`} className="text-blue-600 hover:underline">{o.order_number}</Link></td>
                  <td className="py-1.5 text-gray-600">{(o as any).account?.name}</td>
                  <td className="py-1.5 text-gray-500">{new Date(o.submitted_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
