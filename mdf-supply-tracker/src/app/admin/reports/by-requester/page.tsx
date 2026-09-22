export const runtime = 'edge'
export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import Link from 'next/link'

interface PageProps {
  searchParams: Promise<{ from?: string; to?: string }>
}

export default async function ByRequesterPage({ searchParams }: PageProps) {
  const sp = await searchParams
  const fromDate = sp.from || ''
  const toDate = sp.to || ''

  const supabase = createSupabaseServiceClient()

  let query = supabase
    .from('supply_requests')
    .select(`
      id, order_number, submitted_at, status,
      requester_name, requester_email,
      account:accounts(name),
      request_line_items(
        purchase_details(total_cost)
      )
    `)
    .order('submitted_at', { ascending: false })

  if (fromDate) query = query.gte('submitted_at', fromDate)
  if (toDate) query = query.lte('submitted_at', toDate + 'T23:59:59')

  const { data: orders } = await query
  const all: any[] = orders || []

  // Build requester map keyed by name (normalized) + email
  interface RequesterStat {
    name: string
    email: string | null
    orderCount: number
    totalSpend: number
    accounts: Set<string>
  }

  const requesterMap: Record<string, RequesterStat> = {}

  for (const o of all) {
    const name = (o.requester_name as string | null) || 'Unknown'
    const email = (o.requester_email as string | null) || null
    const key = `${name.toLowerCase()}|${email || ''}`

    const lineItems = (o.request_line_items as any[]) || []
    const spend = lineItems
      .flatMap((li: any) => li.purchase_details || [])
      .reduce((s: number, pd: any) => s + (pd.total_cost || 0), 0)

    const accountName = (o.account as { name: string } | null)?.name || '—'

    if (!requesterMap[key]) {
      requesterMap[key] = { name, email, orderCount: 0, totalSpend: 0, accounts: new Set() }
    }
    requesterMap[key].orderCount++
    requesterMap[key].totalSpend += spend
    if (accountName !== '—') requesterMap[key].accounts.add(accountName)
  }

  const requesters = Object.values(requesterMap).sort((a, b) => b.orderCount - a.orderCount)
  const grandTotal = requesters.reduce((s, r) => s + r.totalSpend, 0)
  const grandOrders = requesters.reduce((s, r) => s + r.orderCount, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/admin/reports" className="text-sm text-gray-500 hover:text-gray-700">← Reports</Link>
        <h1 className="text-xl font-bold text-gray-900">Orders by Requester</h1>
      </div>

      <form method="GET" className="flex flex-wrap items-end gap-3 bg-white rounded-lg shadow-sm p-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input type="date" name="from" defaultValue={fromDate} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input type="date" name="to" defaultValue={toDate} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
        </div>
        <button type="submit" className="bg-gray-800 text-white px-3 py-1.5 rounded text-sm">Apply</button>
        {(fromDate || toDate) && (
          <Link href="/admin/reports/by-requester" className="text-sm text-gray-500 hover:text-gray-700 py-1.5">Clear</Link>
        )}
      </form>

      {requesters.length > 0 && (
        <div className="flex gap-6 text-sm text-gray-500">
          <span>Total orders: <strong className="text-gray-900">{grandOrders}</strong></span>
          {grandTotal > 0 && <span>Total spend: <strong className="text-gray-900">${grandTotal.toFixed(2)}</strong></span>}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Requester</th>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Email</th>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Accounts</th>
              <th className="text-center px-5 py-3 font-medium text-gray-600">Orders</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Total Spend</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Avg / Order</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {requesters.length === 0 && (
              <tr><td colSpan={6} className="px-5 py-8 text-center text-gray-400">No orders for this period</td></tr>
            )}
            {requesters.map((r) => (
              <tr key={`${r.name}|${r.email}`} className="hover:bg-gray-50">
                <td className="px-5 py-3 font-medium text-gray-900">{r.name}</td>
                <td className="px-5 py-3 text-gray-500">{r.email || <span className="text-gray-300 italic">none</span>}</td>
                <td className="px-5 py-3 text-gray-500 text-xs">{Array.from(r.accounts).join(', ') || '—'}</td>
                <td className="px-5 py-3 text-center font-medium text-gray-900">{r.orderCount}</td>
                <td className="px-5 py-3 text-right font-medium text-gray-900">
                  {r.totalSpend > 0 ? `$${r.totalSpend.toFixed(2)}` : '—'}
                </td>
                <td className="px-5 py-3 text-right text-gray-600">
                  {r.totalSpend > 0 ? `$${(r.totalSpend / r.orderCount).toFixed(2)}` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
