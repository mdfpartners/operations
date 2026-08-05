export const runtime = 'edge'
export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import Link from 'next/link'

interface PageProps {
  searchParams: Promise<{ from?: string; to?: string; account?: string }>
}

export default async function SpendByAccountPage({ searchParams }: PageProps) {
  const sp = await searchParams
  const fromDate = sp.from || ''
  const toDate = sp.to || ''
  const focusAccount = sp.account || ''

  const supabase = createSupabaseServiceClient()

  let query = supabase
    .from('supply_requests')
    .select(`
      id, order_number, submitted_at,
      requester_name,
      account:accounts(id, name),
      request_line_items(
        other_item_description,
        catalog_item:supply_catalog(item_name, category),
        purchase_details(total_cost, quantity_purchased, product_name, vendor:vendors(name))
      )
    `)
    .order('submitted_at', { ascending: false })

  if (fromDate) query = query.gte('submitted_at', fromDate)
  if (toDate) query = query.lte('submitted_at', toDate + 'T23:59:59')
  if (focusAccount) query = query.eq('account_id', focusAccount)

  const { data: orders } = await query
  const all: any[] = orders || []

  // Build account summary
  const accountMap: Record<string, { id: string; name: string; orderCount: number; total: number; orders: any[] }> = {}
  for (const o of all) {
    const acc = o.account as { id: string; name: string } | null
    if (!acc) continue
    const lineItems = o.request_line_items as any[] || []
    const cost = lineItems.flatMap((li: any) => li.purchase_details || []).reduce((s: number, pd: any) => s + (pd.total_cost || 0), 0)
    if (!accountMap[acc.id]) accountMap[acc.id] = { id: acc.id, name: acc.name, orderCount: 0, total: 0, orders: [] }
    accountMap[acc.id].orderCount++
    accountMap[acc.id].total += cost
    accountMap[acc.id].orders.push(o)
  }

  const accounts = Object.values(accountMap).sort((a, b) => b.total - a.total)
  const focusedAccount = focusAccount ? accountMap[focusAccount] : null
  const grandTotal = accounts.reduce((s, a) => s + a.total, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/admin/reports" className="text-sm text-gray-500 hover:text-gray-700">← Reports</Link>
        <h1 className="text-xl font-bold text-gray-900">Spend by Account</h1>
      </div>

      {/* Date filter */}
      <form method="GET" className="flex flex-wrap items-end gap-3 bg-white rounded-lg shadow-sm p-4">
        {focusAccount && <input type="hidden" name="account" value={focusAccount} />}
        <div>
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input type="date" name="from" defaultValue={fromDate} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input type="date" name="to" defaultValue={toDate} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
        </div>
        <button type="submit" className="bg-gray-800 text-white px-3 py-1.5 rounded text-sm">Apply</button>
        {(fromDate || toDate || focusAccount) && (
          <Link href="/admin/reports/spend-by-account" className="text-sm text-gray-500 hover:text-gray-700 py-1.5">Clear</Link>
        )}
      </form>

      {/* Account summary table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">
            {focusedAccount ? `Account: ${focusedAccount.name}` : 'All Accounts'}
          </h2>
          {grandTotal > 0 && (
            <span className="text-sm text-gray-500">Total: <span className="font-semibold text-gray-900">${grandTotal.toFixed(2)}</span></span>
          )}
        </div>
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-5 py-3 font-medium text-gray-600">Account</th>
              <th className="text-center px-5 py-3 font-medium text-gray-600">Orders</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Total Spend</th>
              <th className="text-right px-5 py-3 font-medium text-gray-600">Avg / Order</th>
              <th className="px-5 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {accounts.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-gray-400">No spend data for this period</td></tr>
            )}
            {accounts.map((a) => (
              <tr key={a.id} className={`hover:bg-gray-50 ${focusAccount === a.id ? 'bg-blue-50' : ''}`}>
                <td className="px-5 py-3 font-medium text-gray-900">{a.name}</td>
                <td className="px-5 py-3 text-center text-gray-600">{a.orderCount}</td>
                <td className="px-5 py-3 text-right font-medium text-gray-900">
                  {a.total > 0 ? `$${a.total.toFixed(2)}` : '—'}
                </td>
                <td className="px-5 py-3 text-right text-gray-600">
                  {a.total > 0 ? `$${(a.total / a.orderCount).toFixed(2)}` : '—'}
                </td>
                <td className="px-5 py-3 text-right">
                  <Link
                    href={`/admin/reports/spend-by-account?account=${a.id}${fromDate ? `&from=${fromDate}` : ''}${toDate ? `&to=${toDate}` : ''}`}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    {focusAccount === a.id ? 'Showing ↓' : 'Drill down →'}
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Drill-down: orders for focused account */}
      {focusedAccount && (
        <div className="space-y-4">
          <h2 className="font-semibold text-gray-900">Orders — {focusedAccount.name}</h2>
          {focusedAccount.orders.map((o: any) => {
            const lineItems = o.request_line_items as any[] || []
            const orderTotal = lineItems.flatMap((li: any) => li.purchase_details || []).reduce((s: number, pd: any) => s + (pd.total_cost || 0), 0)
            return (
              <div key={o.id} className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Link href={`/admin/orders/${o.id}`} className="font-medium text-blue-600 hover:underline">{o.order_number}</Link>
                    <span className="text-sm text-gray-500">{o.requester_name || '—'}</span>
                    <span className="text-sm text-gray-400">{new Date(o.submitted_at).toLocaleDateString('en-US', { timeZone: 'America/Chicago' })}</span>
                  </div>
                  <span className="font-semibold text-gray-900">{orderTotal > 0 ? `$${orderTotal.toFixed(2)}` : '—'}</span>
                </div>
                <table className="min-w-full text-sm">
                  <tbody className="divide-y divide-gray-50">
                    {lineItems.map((li: any, i: number) => {
                      const itemName = li.catalog_item?.item_name || li.other_item_description || 'Unknown item'
                      const category = li.catalog_item?.category || '—'
                      const pds = li.purchase_details as any[] || []
                      return pds.length > 0 ? pds.map((pd: any, j: number) => (
                        <tr key={`${i}-${j}`} className="hover:bg-gray-50">
                          <td className="px-5 py-2 text-gray-700">{itemName}</td>
                          <td className="px-5 py-2 text-gray-400 text-xs">{category}</td>
                          <td className="px-5 py-2 text-gray-500">{pd.vendor?.name || '—'}</td>
                          <td className="px-5 py-2 text-right text-gray-500">×{pd.quantity_purchased ?? '—'}</td>
                          <td className="px-5 py-2 text-right font-medium text-gray-900">
                            {pd.total_cost != null ? `$${pd.total_cost.toFixed(2)}` : '—'}
                          </td>
                        </tr>
                      )) : (
                        <tr key={i}>
                          <td className="px-5 py-2 text-gray-500">{itemName}</td>
                          <td className="px-5 py-2 text-gray-400 text-xs">{category}</td>
                          <td colSpan={3} className="px-5 py-2 text-gray-400 text-xs">No purchase details</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
