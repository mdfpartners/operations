export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import { getAgingBucket, getCalendarDaysOutstanding } from '@/lib/aging'
import type { OrderStatus } from '@/types'
import OrderDetailClient from '@/components/admin/OrderDetailClient'

interface PageProps {
  params: Promise<{ id: string }>
}

export default async function OrderDetailPage({ params }: PageProps) {
  const { id } = await params
  const supabase = createSupabaseServiceClient()

  // Fetch order first so we can get account_id for the related queries
  const { data: order } = await supabase
    .from('supply_requests')
    .select(`
      id, order_number, status, urgency, requester_notes, internal_notes,
      submitted_at, completed_at, cancelled_at, public_status_token, created_at, updated_at,
      account_id,
      requester:app_users(id, name, email),
      account:accounts(id, name),
      request_line_items(
        id, quantity_requested, quantity_purchased, line_status, other_item_description,
        catalog_item:supply_catalog(id, item_name, unit_of_measure, category),
        purchase_details(
          id, vendor_id, product_url, product_name, quantity_purchased,
          unit_cost, tax, shipping, total_cost, order_confirmation_number, estimated_delivery_date,
          vendor:vendors(id, name)
        )
      )
    `)
    .eq('id', id)
    .single()

  if (!order) notFound()

  const fourteenDaysAgo = new Date()
  fourteenDaysAgo.setDate(fourteenDaysAgo.getDate() - 14)

  // Run all secondary queries in parallel
  const [
    { data: recentRequests },
    { data: auditLog },
    { data: vendors },
  ] = await Promise.all([
    supabase
      .from('supply_requests')
      .select(`
        id, order_number, status, submitted_at,
        request_line_items(
          other_item_description,
          catalog_item:supply_catalog(item_name)
        )
      `)
      .eq('account_id', (order as any).account_id || '')
      .neq('id', id)
      .gte('submitted_at', fourteenDaysAgo.toISOString())
      .order('submitted_at', { ascending: false })
      .limit(10),
    supabase
      .from('audit_log')
      .select('id, actor_name, action, old_value, new_value, notes, created_at')
      .eq('request_id', id)
      .order('created_at', { ascending: false })
      .limit(50),
    supabase
      .from('vendors')
      .select('id, name')
      .eq('active', true)
      .order('name'),
  ])

  const agingBucket = getAgingBucket(
    order.submitted_at,
    order.status as OrderStatus,
    order.completed_at,
    order.cancelled_at
  )
  const daysOutstanding = getCalendarDaysOutstanding(
    order.submitted_at,
    order.status as OrderStatus,
    order.completed_at,
    order.cancelled_at
  )

  return (
    <OrderDetailClient
      order={order as any}
      agingBucket={agingBucket}
      daysOutstanding={daysOutstanding}
      recentRequests={recentRequests as any[] || []}
      auditLog={auditLog as any[] || []}
      vendors={vendors as any[] || []}
    />
  )
}
