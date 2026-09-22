import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'

export async function POST(request: NextRequest) {
  const body = await request.json()
  const { item_name, category, unit_of_measure, preferred_vendor_id, default_notes, active } = body
  if (!item_name?.trim()) return NextResponse.json({ error: 'Item name is required' }, { status: 400 })
  const supabase = createSupabaseServiceClient()
  const { data, error } = await supabase.from('supply_catalog').insert({
    item_name: item_name.trim(),
    category: category?.trim() || null,
    unit_of_measure: unit_of_measure?.trim() || null,
    preferred_vendor_id: preferred_vendor_id || null,
    default_notes: default_notes?.trim() || null,
    active: active !== false,
  }).select().single()
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}
