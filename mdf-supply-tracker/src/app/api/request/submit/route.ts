import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { sendInternalNewRequestNotification } from '@/lib/email'
import type { UrgencyLevel } from '@/types'

const ALLOWED_URGENCIES: UrgencyLevel[] = [
  'normal_replenishment',
  'running_low',
  'out_of_stock',
  'emergency_service_impacting',
]

export async function POST(request: NextRequest) {
  const body = await request.json()
  const { requesterName, accountId, urgency, notes, lineItems } = body

  if (!requesterName?.trim() || !accountId || !urgency || !lineItems?.length) {
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
  }

  if (!ALLOWED_URGENCIES.includes(urgency)) {
    return NextResponse.json({ error: 'Invalid urgency value' }, { status: 400 })
  }

  const supabase = createSupabaseServiceClient()

  // Validate account exists and is active
  const { data: account } = await supabase
    .from('accounts')
    .select('id, name')
    .eq('id', accountId)
    .eq('active', true)
    .single()

  if (!account) {
    return NextResponse.json({ error: 'Invalid account' }, { status: 400 })
  }

  // Validate and resolve line items
  const resolvedItems: {
    catalogItemId: string | null
    otherDescription: string | null
    quantity: number
    itemLabel: string
  }[] = []

  for (const li of lineItems) {
    const qty = parseFloat(li.quantity)
    if (!li.catalogItemId || isNaN(qty) || qty <= 0) {
      return NextResponse.json({ error: 'Invalid line item data' }, { status: 400 })
    }

    if (li.catalogItemId === 'other') {
      if (!li.otherDescription?.trim()) {
        return NextResponse.json({ error: 'Other item description is required' }, { status: 400 })
      }
      resolvedItems.push({
        catalogItemId: null,
        otherDescription: li.otherDescription.trim(),
        quantity: qty,
        itemLabel: li.otherDescription.trim(),
      })
    } else {
      const { data: catalogItem } = await supabase
        .from('supply_catalog')
        .select('id, item_name, active')
        .eq('id', li.catalogItemId)
        .eq('active', true)
        .single()

      if (!catalogItem) {
        return NextResponse.json({ error: 'Invalid catalog item' }, { status: 400 })
      }
      resolvedItems.push({
        catalogItemId: catalogItem.id,
        otherDescription: null,
        quantity: qty,
        itemLabel: catalogItem.item_name,
      })
    }
  }

  // Insert supply_request
  const { data: supplyRequest, error: insertError } = await supabase
    .from('supply_requests')
    .insert({
      requester_name: requesterName.trim(),
      account_id: accountId,
      urgency,
      requester_notes: notes?.trim() || null,
    })
    .select('id, order_number, submitted_at, public_status_token')
    .single()

  if (insertError || !supplyRequest) {
    console.error('Failed to insert supply request', insertError)
    return NextResponse.json({ error: 'Failed to create request' }, { status: 500 })
  }

  // Insert line items
  await supabase.from('request_line_items').insert(
    resolvedItems.map((li) => ({
      request_id: supplyRequest.id,
      catalog_item_id: li.catalogItemId,
      other_item_description: li.otherDescription,
      quantity_requested: li.quantity,
    }))
  )

  // Audit log
  await supabase.from('audit_log').insert({
    request_id: supplyRequest.id,
    actor_name: requesterName.trim(),
    action: 'request_submitted',
    new_value: { order_number: supplyRequest.order_number, urgency, account_id: accountId },
  })

  // Internal notification
  await sendInternalNewRequestNotification({
    requestId: supplyRequest.id,
    orderNumber: supplyRequest.order_number,
    accountName: account.name,
    requesterName: requesterName.trim(),
    urgency,
    submittedAt: supplyRequest.submitted_at,
    lineItems: resolvedItems.map((li) => ({ description: li.itemLabel, quantity: li.quantity })),
  }).catch((err) => console.error('Internal notification error', err))

  return NextResponse.json({
    orderNumber: supplyRequest.order_number,
    requestId: supplyRequest.id,
  })
}
