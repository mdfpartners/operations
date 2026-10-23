import { NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { getAgingBucket } from '@/lib/aging'
import type { OrderStatus } from '@/types'

function toCSV(headers: string[], rows: string[][]): string {
  const escape = (v: string) => {
    if (v.includes(',') || v.includes('"') || v.includes('\n')) {
      return `"${v.replace(/"/g, '""')}"`
    }
    return v
  }
  const lines = [headers.map(escape).join(',')]
  for (const row of rows) lines.push(row.map((c) => escape(String(c ?? ''))).join(','))
  return lines.join('\n')
}

export async function GET() {
  const supabase = createSupabaseServiceClient()
  const { data: orders } = await supabase
    .from('supply_requests')
    .select(`
      order_number, status, urgency, submitted_at, completed_at, cancelled_at,
      account:accounts(name),
      requester:app_users(name),
      request_line_items(purchase_details(total_cost))
    `)
    .order('submitted_at', { ascending: false })

  const headers = ['order_number', 'account', 'requester', 'submitted_date', 'status', 'urgency', 'aging_bucket', 'completed_cancelled_date', 'total_cost']
  const rows = (orders || []).map((o: any) => {
    const bucket = getAgingBucket(o.submitted_at, o.status as OrderStatus, o.completed_at, o.cancelled_at)
    const items = (o as any).request_line_items as any[] || []
    const total = items.flatMap((li: any) => li.purchase_details || []).reduce((s: number, pd: any) => s + (pd.total_cost || 0), 0)
    const endDate = o.completed_at || o.cancelled_at || ''
    return [
      o.order_number,
      (o as any).account?.name || '',
      (o as any).requester?.name || '',
      new Date(o.submitted_at).toLocaleDateString(),
      o.status,
      o.urgency,
      bucket,
      endDate ? new Date(endDate).toLocaleDateString() : '',
      total > 0 ? total.toFixed(2) : '',
    ]
  })

  const csv = toCSV(headers, rows)
  return new NextResponse(csv, {
    headers: {
      'Content-Type': 'text/csv',
      'Content-Disposition': 'attachment; filename="mdf_order_history.csv"',
    },
  })
}
