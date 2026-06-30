import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'

interface Context { params: Promise<{ id: string }> }

export async function PATCH(request: NextRequest, { params }: Context) {
  const { id } = await params
  const body = await request.json()
  const supabase = await createSupabaseServiceClient()
  const update: Record<string, unknown> = {}
  if (body.item_name !== undefined) update.item_name = body.item_name.trim()
  if (body.category !== undefined) update.category = body.category?.trim() || null
  if (body.unit_of_measure !== undefined) update.unit_of_measure = body.unit_of_measure?.trim() || null
  if (body.preferred_vendor_id !== undefined) update.preferred_vendor_id = body.preferred_vendor_id || null
  if (body.default_notes !== undefined) update.default_notes = body.default_notes?.trim() || null
  if (body.active !== undefined) update.active = body.active
  const { error } = await supabase.from('supply_catalog').update(update).eq('id', id)
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ ok: true })
}
