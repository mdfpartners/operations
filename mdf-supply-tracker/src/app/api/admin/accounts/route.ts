import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'

export async function POST(request: NextRequest) {
  const { name, location, active } = await request.json()
  if (!name?.trim()) return NextResponse.json({ error: 'Account name is required' }, { status: 400 })
  const supabase = createSupabaseServiceClient()
  const { data, error } = await supabase.from('accounts').insert({
    name: name.trim(),
    location: location?.trim() || null,
    active: active !== false,
  }).select().single()
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}