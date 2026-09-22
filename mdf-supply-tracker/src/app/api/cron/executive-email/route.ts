import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { sendEmail } from '@/lib/email'
import { getNotificationEmails } from '@/lib/notification-settings'
import { getAgingBucket } from '@/lib/aging'
import { OPEN_STATUSES, STATUS_LABELS } from '@/lib/constants'
import type { OrderStatus } from '@/types'
import { toZonedTime } from 'date-fns-tz'

function daysSince(isoTimestamp: string): number {
  const ms = Date.now() - new Date(isoTimestamp).getTime()
  return Math.floor(ms / 86400000)
}

export async function GET(request: NextRequest) {
  // Protect with CRON_SECRET
  // Vercel sends: Authorization: Bearer <CRON_SECRET>
  // Manual triggers can use ?secret= or x-cron-secret header
  if (process.env.CRON_SECRET) {
    const authHeader = request.headers.get('authorization')
    const bearerSecret = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : null
    const secret = bearerSecret || request.nextUrl.searchParams.get('secret') || request.headers.get('x-cron-secret')
    if (secret !== process.env.CRON_SECRET) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
  }

  const tz = process.env.APP_TIMEZONE || 'America/Chicago'
  const supabase = createSupabaseServiceClient()

  const { data: orders } = await supabase
    .from('supply_requests')
    .select(`
      id, order_number, status, urgency, submitted_at, completed_at, cancelled_at, status_changed_at,
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
    // Days in current status (falls back to overall aging if column not yet available)
    const statusDays = o.status_changed_at ? daysSince(o.status_changed_at) : daysSince(o.submitted_at)
    const statusLabel = STATUS_LABELS[o.status as OrderStatus]
    // Highlight rows stuck in current status for 3+ days
    const rowBg = statusDays >= 3 ? 'background:#fef9c3' : ''
    return `<tr style="${rowBg}">
      <td style="padding:6px 10px"><a href="${baseUrl}/admin/orders/${o.id}" style="color:#1d4ed8">${o.order_number}</a></td>
      <td style="padding:6px 10px">${account?.name || '—'}</td>
      <td style="padding:6px 10px;text-align:center">${bucket}d</td>
      <td style="padding:6px 10px">${statusLabel}</td>
      <td style="padding:6px 10px;text-align:center;color:${statusDays >= 3 ? '#b45309' : '#374151'};font-weight:${statusDays >= 3 ? '600' : 'normal'}">${statusDays}d in stage</td>
    </tr>`
  }).join('')

  const html = `
    <div style="font-family:sans-serif;max-width:720px;margin:0 auto">
      <h2 style="color:#111827;margin-bottom:4px">MDF Supply Request Aging Dashboard</h2>
      <p style="color:#6b7280;margin-top:0">${today}</p>
      <div style="display:flex;gap:24px;margin-bottom:16px">
        <div style="background:#f3f4f6;border-radius:6px;padding:10px 16px;text-align:center">
          <div style="font-size:24px;font-weight:700;color:#111827">${open.length}</div>
          <div style="font-size:12px;color:#6b7280">Open Orders</div>
        </div>
        <div style="background:#fee2e2;border-radius:6px;padding:10px 16px;text-align:center">
          <div style="font-size:24px;font-weight:700;color:#b91c1c">${eightPlus.length}</div>
          <div style="font-size:12px;color:#6b7280">8+ Day Orders</div>
        </div>
        <div style="background:#ffedd5;border-radius:6px;padding:10px 16px;text-align:center">
          <div style="font-size:24px;font-weight:700;color:#c2410c">${emergency.length}</div>
          <div style="font-size:12px;color:#6b7280">Emergency / OOS</div>
        </div>
      </div>
      <table border="0" cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;border:1px solid #e5e7eb;border-radius:6px;overflow:hidden">
        <thead>
          <tr style="background:#f9fafb;border-bottom:1px solid #e5e7eb">
            <th style="padding:8px 10px;text-align:left;font-size:12px;color:#6b7280;font-weight:600">Order #</th>
            <th style="padding:8px 10px;text-align:left;font-size:12px;color:#6b7280;font-weight:600">Account</th>
            <th style="padding:8px 10px;text-align:center;font-size:12px;color:#6b7280;font-weight:600">Total Age</th>
            <th style="padding:8px 10px;text-align:left;font-size:12px;color:#6b7280;font-weight:600">Status</th>
            <th style="padding:8px 10px;text-align:center;font-size:12px;color:#6b7280;font-weight:600">In Stage</th>
          </tr>
        </thead>
        <tbody style="border-top:1px solid #e5e7eb">
          ${tableRows || '<tr><td colspan="5" style="padding:16px;text-align:center;color:#9ca3af">No open orders</td></tr>'}
        </tbody>
      </table>
      <p style="color:#9ca3af;font-size:11px;margin-top:12px">Rows highlighted in yellow have been in the same stage for 3+ days. Click an order number to view details.</p>
    </div>
  `

  const recipients = await getNotificationEmails('executive_notification_emails')

  if (recipients.length > 0) {
    await sendEmail({
      to: recipients,
      subject: `MDF Supply Tracker — ${open.length} open order${open.length !== 1 ? 's' : ''} (${today})`,
      notificationType: 'executive_daily',
      html,
    })
  }

  return NextResponse.json({ ok: true, sent: recipients.length, openCount: open.length })
}
