import { Resend } from 'resend'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { getNotificationEmails } from '@/lib/notification-settings'

let resend: Resend | null = null

function getResend(): Resend | null {
  if (!process.env.RESEND_API_KEY) return null
  if (!resend) resend = new Resend(process.env.RESEND_API_KEY)
  return resend
}

function shouldSendRealEmails(): boolean {
  if (process.env.NODE_ENV === 'production') return true
  return process.env.SEND_REAL_EMAILS_IN_DEV === 'true'
}

interface SendEmailOptions {
  to: string[]
  subject: string
  html: string
  notificationType: string
  requestId?: string
}

export async function sendEmail(opts: SendEmailOptions): Promise<void> {
  const supabase = await createSupabaseServiceClient()

  if (!shouldSendRealEmails()) {
    console.log('[DEV EMAIL]', { to: opts.to, subject: opts.subject, html: opts.html })
    for (const email of opts.to) {
      await supabase.from('notification_log').insert({
        request_id: opts.requestId || null,
        recipient_email: email,
        notification_type: opts.notificationType,
        status: 'dev_logged',
        sent_at: new Date().toISOString(),
      })
    }
    return
  }

  const client = getResend()
  if (!client) {
    console.error('RESEND_API_KEY is missing in production — email not sent')
    for (const email of opts.to) {
      await supabase.from('notification_log').insert({
        request_id: opts.requestId || null,
        recipient_email: email,
        notification_type: opts.notificationType,
        status: 'error',
        sent_at: new Date().toISOString(),
        error_message: 'RESEND_API_KEY not configured',
      })
    }
    return
  }

  for (const email of opts.to) {
    try {
      await client.emails.send({
        from: 'MDF Supply Tracker <noreply@mdfpartners.com>',
        to: email,
        subject: opts.subject,
        html: opts.html,
      })
      await supabase.from('notification_log').insert({
        request_id: opts.requestId || null,
        recipient_email: email,
        notification_type: opts.notificationType,
        status: 'sent',
        sent_at: new Date().toISOString(),
      })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      console.error('Failed to send email to', email, errorMessage)
      await supabase.from('notification_log').insert({
        request_id: opts.requestId || null,
        recipient_email: email,
        notification_type: opts.notificationType,
        status: 'error',
        sent_at: new Date().toISOString(),
        error_message: errorMessage,
      })
    }
  }
}

// ============================================================
// Email templates
// ============================================================

export async function sendRequesterConfirmation(params: {
  requestId: string
  orderNumber: string
  accountName: string
  submittedAt: string
  requesterEmail: string
  publicStatusToken: string
}) {
  const baseUrl = process.env.APP_BASE_URL || ''
  const statusUrl = `${baseUrl}/status/${params.publicStatusToken}`

  await sendEmail({
    to: [params.requesterEmail],
    subject: `MDF Supply Request Received: ${params.orderNumber}`,
    notificationType: 'requester_confirmation',
    requestId: params.requestId,
    html: `
      <p>Hi,</p>
      <p>Your supply request has been received.</p>
      <ul>
        <li><strong>Order Number:</strong> ${params.orderNumber}</li>
        <li><strong>Account:</strong> ${params.accountName}</li>
        <li><strong>Submitted:</strong> ${new Date(params.submittedAt).toLocaleString('en-US', { timeZone: process.env.APP_TIMEZONE || 'America/Chicago' })}</li>
        <li><strong>Status:</strong> Submitted</li>
      </ul>
      <p><a href="${statusUrl}">View order status</a></p>
      <p>— MDF Partners Supply Team</p>
    `,
  })
}

export async function sendInternalNewRequestNotification(params: {
  requestId: string
  orderNumber: string
  accountName: string
  requesterName: string
  urgency: string
  submittedAt: string
  lineItems: { description: string; quantity: number }[]
}) {
  const recipientEmails = await getNotificationEmails('internal_notification_emails')
  if (recipientEmails.length === 0) return

  const baseUrl = process.env.APP_BASE_URL || ''
  const detailUrl = `${baseUrl}/admin/orders/${params.requestId}`
  const itemsHtml = params.lineItems
    .map((li) => `<li>${li.description} × ${li.quantity}</li>`)
    .join('')

  await sendEmail({
    to: recipientEmails,
    subject: `New Supply Request: ${params.orderNumber} - ${params.accountName}`,
    notificationType: 'internal_new_request',
    requestId: params.requestId,
    html: `
      <p>A new supply request has been submitted.</p>
      <ul>
        <li><strong>Order Number:</strong> ${params.orderNumber}</li>
        <li><strong>Account:</strong> ${params.accountName}</li>
        <li><strong>Requester:</strong> ${params.requesterName}</li>
        <li><strong>Urgency:</strong> ${params.urgency}</li>
        <li><strong>Submitted:</strong> ${new Date(params.submittedAt).toLocaleString('en-US', { timeZone: process.env.APP_TIMEZONE || 'America/Chicago' })}</li>
      </ul>
      <p><strong>Items requested:</strong></p>
      <ul>${itemsHtml}</ul>
      <p><a href="${detailUrl}">View order in admin</a></p>
    `,
  })
}

export async function sendRequesterStatusUpdate(params: {
  requestId: string
  orderNumber: string
  accountName: string
  newStatus: string
  requesterEmail: string
  publicStatusToken: string
}) {
  const baseUrl = process.env.APP_BASE_URL || ''
  const statusUrl = `${baseUrl}/status/${params.publicStatusToken}`

  const statusMessages: Record<string, string> = {
    purchased: 'Your supplies have been ordered.',
    delayed: 'Your order has been delayed. The supply team will follow up with more information.',
    delivered: 'Your supplies have been delivered to the site.',
    complete_received: 'Your supply request has been marked complete and received.',
    cancelled: 'Your supply request has been cancelled. Please contact the supply team if you have questions.',
  }

  await sendEmail({
    to: [params.requesterEmail],
    subject: `MDF Supply Request Update: ${params.orderNumber}`,
    notificationType: 'requester_status_update',
    requestId: params.requestId,
    html: `
      <p>Your supply request status has been updated.</p>
      <ul>
        <li><strong>Order Number:</strong> ${params.orderNumber}</li>
        <li><strong>Account:</strong> ${params.accountName}</li>
        <li><strong>New Status:</strong> ${params.newStatus}</li>
      </ul>
      <p>${statusMessages[params.newStatus] || ''}</p>
      <p><a href="${statusUrl}">View order status</a></p>
      <p>— MDF Partners Supply Team</p>
    `,
  })
}
