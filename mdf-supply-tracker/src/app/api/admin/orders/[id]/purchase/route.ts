import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'

interface Context {
  params: Promise<{ id: string }>
}

export async function POST(request: NextRequest, { params }: Context) {
  const { id } = await params
  const body = await request.json()

  const {
    lineItemId,
    purchaseDetailId,
    vendorId,
    productUrl,
    productName,
    quantityPurchased,
    unitCost,
    tax,
    shipping,
    totalCost,
    orderConfirmationNumber,
    estimatedDeliveryDate,
  } = body

  if (!lineItemId) return NextResponse.json({ error: 'lineItemId is required' }, { status: 400 })

  if (totalCost !== '' && totalCost !== null && parseFloat(totalCost) < 0) {
    return NextResponse.json({ error: 'Total cost must be >= 0' }, { status: 400 })
  }

  const supabase = createSupabaseServiceClient()

  // Verify line item belongs to this order
  const { data: lineItem } = await supabase
    .from('request_line_items')
    .select('id, request_id')
    .eq('id', lineItemId)
    .eq('request_id', id)
    .single()

  if (!lineItem) return NextResponse.json({ error: 'Line item not found' }, { status: 404 })

  const pd = {
    line_item_id: lineItemId,
    vendor_id: vendorId || null,
    product_url: productUrl || null,
    product_name: productName || null,
    quantity_purchased: quantityPurchased !== '' ? parseFloat(quantityPurchased) : null,
    unit_cost: unitCost !== '' ? parseFloat(unitCost) : null,
    tax: tax !== '' ? parseFloat(tax) : null,
    shipping: shipping !== '' ? parseFloat(shipping) : null,
    total_cost: totalCost !== '' ? parseFloat(totalCost) : null,
    order_confirmation_number: orderConfirmationNumber || null,
    estimated_delivery_date: estimatedDeliveryDate || null,
  }

  if (purchaseDetailId) {
    await supabase.from('purchase_details').update(pd).eq('id', purchaseDetailId)
  } else {
    await supabase.from('purchase_details').insert(pd)
  }

  // Update quantity_purchased on line item if provided
  if (quantityPurchased !== '') {
    await supabase
      .from('request_line_items')
      .update({ quantity_purchased: parseFloat(quantityPurchased) })
      .eq('id', lineItemId)
  }

  await supabase.from('audit_log').insert({
    request_id: id,
    actor_name: 'Admin',
    action: purchaseDetailId ? 'purchase_details_updated' : 'purchase_details_added',
    new_value: { line_item_id: lineItemId, total_cost: pd.total_cost },
  })

  return NextResponse.json({ ok: true })
}
