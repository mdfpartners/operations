export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { STATUS_LABELS } from '@/lib/constants'
import { getAgingBucket } from '@/lib/aging'

interface PageProps {
  params: Promise<{ token: string }>
}

export default async function PublicStatusPage({ params }: PageProps) {
  const { token } = await params
  const supabase = createSupabaseServiceClient()

  const { data: req } = await supabase
    .from('supply_requests')
    .select(`
      id, order_number, status, urgency, submitted_at, completed_at, cancelled_at,
      accounts(name),
      request_line_items(
        id, quantity_requested, line_status, other_item_description,
        supply_catalog(item_name, unit_of_measure),
        purchase_details(estimated_delivery_date)
      )
    `)
    .eq('public_status_token', token)
    .single()

  if (!req) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-sm w-full text-center">
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Order Not Found</h1>
          <p className="text-gray-500 text-sm">This status link is invalid or has expired.</p>
        </div>
      </div>
    )
  }

  const account = req.accounts as unknown as { name: string } | null
  const agingBucket = getAgingBucket(req.submitted_at, req.status as any, req.completed_at, req.cancelled_at)
  const lineItems = req.request_line_items as any[] || []

  // Earliest estimated delivery across all line items
  const deliveryDates = lineItems
    .flatMap((li: any) => (li.purchase_details || []).map((pd: any) => pd.estimated_delivery_date))
    .filter(Boolean)
  const estimatedDelivery = deliveryDates.sort()[0] || null

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-lg mx-auto px-4 py-8">
        <div className="mb-4">
          <h1 className="text-xl font-bold text-gray-900">Supply Request Status</h1>
          <p className="text-gray-500 text-sm">MDF Partners</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">Order Number</p>
              <p className="font-bold text-blue-700 text-lg">{req.order_number}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Status</p>
              <p className="font-semibold text-gray-900">{STATUS_LABELS[req.status as keyof typeof STATUS_LABELS]}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Account</p>
              <p className="text-gray-900">{account?.name}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Submitted</p>
              <p className="text-gray-900">
                {new Date(req.submitted_at).toLocaleDateString('en-US', {
                  timeZone: process.env.APP_TIMEZONE || 'America/Chicago',
                })}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Days Outstanding</p>
              <p className="text-gray-900">{agingBucket} day(s)</p>
            </div>
            {estimatedDelivery && (
              <div>
                <p className="text-xs text-gray-500">Est. Delivery</p>
                <p className="text-gray-900">{new Date(estimatedDelivery).toLocaleDateString('en-US')}</p>
              </div>
            )}
          </div>

          {lineItems.length > 0 && (
            <div className="border-t pt-4">
              <p className="text-sm font-semibold text-gray-800 mb-3">Items Requested</p>
              <ul className="space-y-2">
                {lineItems.map((li: any) => {
                  const itemName = li.supply_catalog?.item_name || li.other_item_description || 'Unknown item'
                  const uom = li.supply_catalog?.unit_of_measure
                  const lineStatus = li.line_status as string | undefined
                  const lineStatusLabel = lineStatus ? STATUS_LABELS[lineStatus as keyof typeof STATUS_LABELS] : null
                  return (
                    <li key={li.id} className="flex items-start justify-between gap-3 text-sm">
                      <span className="text-gray-800">
                        <span className="font-medium">{li.quantity_requested}{uom ? ` ${uom}` : 'x'}</span>
                        {' '}{itemName}
                      </span>
                      {lineStatusLabel && (
                        <span className="shrink-0 text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
                          {lineStatusLabel}
                        </span>
                      )}
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
        </div>
        <p className="text-xs text-gray-400 text-center mt-6">
          Questions? Contact the MDF supply team.
        </p>
      </div>
    </div>
  )
}
