import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { sendRequesterStatusUpdate } from '@/lib/email'
import type { OrderStatus } from '@/types'

const ALLOWED_STATUSES: OrderStatus[] = [
  'submitted', 'purchased', 'delivered', 'complete_received', 'cancelled', 'delayed',
]

const STATUS_THAT_NOTIFY: OrderStatus[] = [
  'purchased', 'delayed', 'delivered', 'complete_received', 'cancelled',
]

interface Context {
  params: Promise<{ id: string }>
}

export async function PATCH(request: NextRequest, { params }: Context) {
  const { id } = await params
  const { status, internalNotes } = await request.json()

  if (status && !ALLOWED_STATUSES.includes(status)) {
    return NextResponse.json({ error: 'Invalid status' }, { status: 400 })
  }

  const supabase = await createSupabaseServiceClient()

  const { data: existing } = await supabase
    .from('supply_requests')
    .select(`id, status, order_number, public_status_token, requester_name, requester_email, account:accounts(name)`)
    .eq('id', id)
    .single()

  if (!existing) return NextResponse.json({ error: 'Order not found' }, { status: 404 })

  const updateData: Record<string, unknown> = {}
  if (status !== undefined) updateData.status = status
  if (internalNotes !== undefined) updateData.internal_notes = internalNotes || null
  if (status === 'complete_received') updateData.completed_at = new Date().toISOString()
  if (status === 'cancelled') updateData.cancelled_at = new Date().toISOString()

  await supabase.from('supply_requests').update(updateData).eq('id', id)

  const oldStatus = existing.status
  const account = (existing as any).account as { name: string } | null
  const requesterEmail = (existing as any).requester_email as string | null

  // Audit log
  if (status && status !== oldStatus) {
    await supabase.from('audit_log').insert({
      request_id: id,
      actor_name: 'Admin',
      action: 'status_changed',
      old_value: { status: oldStatus },
      new_value: { status },
      notes: `Status changed from ${oldStatus} to ${status}`,
    })

    // Notify requester if they provided an email
    if (STATUS_THAT_NOTIFY.includes(status) && requesterEmail) {
      await sendRequesterStatusUpdate({
        requestId: id,
        orderNumber: existing.order_number,
        accountName: account?.name || '',
        newStatus: status,
        requesterEmail,
        publicStatusToken: existing.public_status_token,
      }).catch((err) => console.error('Status update email error', err))
    }
  }

  if (internalNotes !== undefined && internalNotes !== existing) {
    await supabase.from('audit_log').insert({
      request_id: id,
      actor_name: 'Admin',
      action: 'internal_notes_updated',
    })
  }

  return NextResponse.json({ ok: true })
}
