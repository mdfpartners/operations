import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { sendEmail } from '@/lib/email'
import { getAgingBucket } from '@/lib/aging'
import { OPEN_STATUSES, STATUS_LABELS } from '@/lib/constants'
import type { OrderStatus } from '@/types'
import { toZonedTime } from 'date-fns-tz'

export async function GET(request: NextRequest) {
  // Protect with CRON_SECRET
  const secret = request.nextUrl.searchParams.get('secret') || request.headers.get('x-cron-secret')
  if (!process.env.CRON_SECRET || secret !== process.env.CRON_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const tz = process.env.APP_TIMEZONE || 'America/Chicago'
  const supabase = await createSupabaseServiceClient()

  const { data: orders } = await supabase
    .from('supply_requests')
    .select(`
      id, order_number, status, urgency, submitted_at, completed_at, cancelled_at,
      account:accounts(name)
    `)
    .in('status', OPEN_STATUSES)
    .order('submitted_at', { ascending: true })

  const open = orders || []
  const eightPlus = open.filter((o: any) => getAgingBucket(o.submitted_at, o.status as OrderStatus, o.completed_at, o.cancelled_at) === '8+')
  const emergency = open.filter((o: any) => o.urgency === 'emergency_service_impacting' || o.urgency === 'out_of_stock')

  const today = toZonedTime(new Date(), tz).toLocaleDateString('en-US', { timeZone: tz, year: 'numeric', month: 'long', day: 'numeric' })
  const baseUrl = process.env.APP_BASE_URL || ''

  const tableRows = (open as any[]).map((o) => {
    const bucket = getAgingBucket(o.submitted_at, o.status as OrderStatus, o.completed_at, o.cancelled_at)
    const account = (o as any).account as { name: string } | null
    return `<tr>
      <td style="padding:6px 8px"><a href="${baseUrl}/admin/orders/${o.id}">${o.order_number}</a></td>
      <td style="padding:6px 8px">${account?.name || '—'}</td>
      <td style="padding:6px 8px">${bucket}d</td>
      <td style="padding:6px 8px">${STATUS_LABELS[o.status as OrderStatus]}</td>
    </tr>`
  }).join('')

  const html = `
    <h2>MDF Supply Request Aging Dashboard — ${today}</h2>
    <p><strong>Open Requests:</strong> ${open.length} &nbsp;|&nbsp;
       <strong>8+ Days:</strong> ${eightPlus.length} &nbsp;|&nbsp;
       <strong>Emergency/OOS:</strong> ${emergency.length}</p>
    <table border="1" cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;max-width:700px">
      <thead style="background:#f3f4f6">
        <tr>
          <th style="padding:6px 8px;text-align:left">Order #</th>
          <th style="padding:6px 8px;text-align:left">Account</th>
          <th style="padding:6px 8px;text-align:left">Aging</th>
          <th style="padding:6px 8px;text-align:left">Status</th>
        </tr>
      </thead>
      <tbody>${tableRows}</tbody>
    </table>
    <p style="color:#6b7280;font-size:12px;margin-top:16px">Click an order number to view details in the admin dashboard.</p>
  `

  const recipients = (process.env.EXECUTIVE_NOTIFICATION_EMAILS || '')
    .split(',').map((e) => e.trim()).filter(Boolean)

  if (recipients.length > 0) {
    await sendEmail({
      to: recipients,
      subject: `MDF Supply Request Aging Dashboard — ${today}`,
      notificationType: 'executive_daily',
      html,
    })
  }

  return NextResponse.json({ ok: true, sent: recipients.length, openCount: open.length })
}
