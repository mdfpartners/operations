import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'

export async function POST(request: NextRequest) {
  const { name, website, active } = await request.json()
  if (!name?.trim()) return NextResponse.json({ error: 'Vendor name is required' }, { status: 400 })
  const supabase = createSupabaseServiceClient()
  const { data, error } = await supabase.from('vendors').insert({
    name: name.trim(),
    website: website?.trim() || null,
    active: active !== false,
  }).select().single()
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}