export const runtime = 'edge'
export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import Link from 'next/link'

interface PageProps {
  searchParams: Promise<{ from?: string; to?: string; category?: string }>
}

export default async function SpendByItemPage({ searchParams }: PageProps) {
  const sp = await searchParams
  const fromDate = sp.from || ''
  const toDate = sp.to || ''
  const focusCategory = sp.category || ''

  const supabase = createSupabaseServiceClient()

  let query = supabase
    .from('request_line_items')
    .select(`
      id, other_item_description, quantity_requested,
      catalog_item:supply_catalog(id, item_name, category),
      purchase_details(total_cost, quantity_purchased, vendor:vendors(name)),
      supply_request:supply_requests!request_id(id, order_number, submitted_at, account:accounts(name))
    `)

  if (fromDate || toDate) {
    // filter via submitted_at on the parent request
    if (fromDate) query = (query as any).gte('supply_requests.submitted_at', fromDate)
    if (toDate) query = (query as any).lte('supply_requests.submitted_at', toDate + 'T23:59:59')
  }

  const { data: lineItems } = await query
  const all: any[] = (lineItems || []).filter((li: any) => li.supply_request != null)

  // Build item map
  interface ItemStat {
    itemName: string
    category: string
    timesOrdered: number
    totalQty: number
    totalSpend: number
    orders: { orderNumber: string; orderId: string; account: string; qty: number; cost: number }[]
  }

  const itemMap: Record<string, ItemStat> = {}

  for (const li of all) {
    const key = li.catalog_item?.id || `other:${li.other_item_description}`
    const itemName = li.catalog_item?.item_name || li.other_item_description || 'Unknown'
    const category = li.catalog_item?.category || 'Other'
    const pds = li.purchase_details as any[] || []
    const cost = pds.reduce((s: number, pd: any) => s + (pd.total_cost || 0), 0)
    const qty = li.quantity_requested || 0
    const req = li.supply_request as any

    if (!itemMap[key]) itemMap[key] = { itemName, category, timesOrdered: 0, totalQty: 0, totalSpend: 0, orders: [] }
    itemMap[key].timesOrdered++
    itemMap[key].totalQty += qty
    itemMap[key].totalSpend += cost
    if (req) {
      itemMap[key].orders.push({
        orderNumber: req.order_number,
        orderId: req.id,
        account: req.account?.name || '—',
        qty,
        cost,
      })
    }
  }

  // Group by category
  const categoryMap: Record<string, ItemStat[]> = {}
  for (const item of Object.values(itemMap)) {
    if (focusCategory && item.category !== focusCategory) continue
    if (!categoryMap[item.category]) categoryMap[item.category] = []
    categoryMap[item.category].push(item)
  }
  for (const cat of Object.keys(categoryMap)) {
    categoryMap[cat].sort((a, b) => b.totalSpend - a.totalSpend)
  }

  const categories = Object.keys(categoryMap).sort()
  const grandTotal = Object.values(itemMap)
    .filter(i => !focusCategory || i.category === focusCategory)
    .reduce((s, i) => s + i.totalSpend, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/admin/reports" className="text-sm text-gray-500 hover:text-gray-700">← Reports</Link>
        <h1 className="text-xl font-bold text-gray-900">Spend by Item</h1>
      </div>

      <form method="GET" className="flex flex-wrap items-end gap-3 bg-white rounded-lg shadow-sm p-4">
        {focusCategory && <input type="hidden" name="category" value={focusCategory} />}
        <div>
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input type="date" name="from" defaultValue={fromDate} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input type="date" name="to" defaultValue={toDate} className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
        </div>
        <button type="submit" className="bg-gray-800 text-white px-3 py-1.5 rounded text-sm">Apply</button>
        {(fromDate || toDate || focusCategory) && (
          <Link href="/admin/reports/spend-by-item" className="text-sm text-gray-500 hover:text-gray-700 py-1.5">Clear</Link>
        )}
      </form>

      {/* Category filter chips */}
      <div className="flex flex-wrap gap-2">
        <Link
          href={`/admin/reports/spend-by-item${fromDate || toDate ? `?from=${fromDate}&to=${toDate}` : ''}`}
          className={`px-3 py-1 rounded-full text-sm ${!focusCategory ? 'bg-gray-900 text-white' : 'bg-white text-gray-600 shadow-sm hover:bg-gray-50'}`}
        >
          All Categories
        </Link>
        {Object.keys(categoryMap).sort().map((cat) => (
          <Link
            key={cat}
            href={`/admin/reports/spend-by-item?category=${encodeURIComponent(cat)}${fromDate ? `&from=${fromDate}` : ''}${toDate ? `&to=${toDate}` : ''}`}
            className={`px-3 py-1 rounded-full text-sm ${focusCategory === cat ? 'bg-gray-900 text-white' : 'bg-white text-gray-600 shadow-sm hover:bg-gray-50'}`}
          >
            {cat}
          </Link>
        ))}
      </div>

      {grandTotal > 0 && (
        <p className="text-sm text-gray-500">
          Total spend shown: <span className="font-semibold text-gray-900">${grandTotal.toFixed(2)}</span>
        </p>
      )}

      {categories.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm px-5 py-10 text-center text-gray-400">No spend data for this period</div>
      )}

      {categories.map((cat) => (
        <div key={cat} className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">{cat}</h2>
            <span className="text-sm text-gray-500">
              ${categoryMap[cat].reduce((s, i) => s + i.totalSpend, 0).toFixed(2)}
            </span>
          </div>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left px-5 py-2 text-xs font-medium text-gray-500">Item</th>
                <th className="text-center px-5 py-2 text-xs font-medium text-gray-500">Times Ordered</th>
                <th className="text-right px-5 py-2 text-xs font-medium text-gray-500">Total Qty</th>
                <th className="text-right px-5 py-2 text-xs font-medium text-gray-500">Total Spend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {categoryMap[cat].map((item) => (
                <tr key={item.itemName} className="hover:bg-gray-50">
                  <td className="px-5 py-2.5 text-gray-800 font-medium">{item.itemName}</td>
                  <td className="px-5 py-2.5 text-center text-gray-500">{item.timesOrdered}</td>
                  <td className="px-5 py-2.5 text-right text-gray-500">{item.totalQty}</td>
                  <td className="px-5 py-2.5 text-right font-medium text-gray-900">
                    {item.totalSpend > 0 ? `$${item.totalSpend.toFixed(2)}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}
