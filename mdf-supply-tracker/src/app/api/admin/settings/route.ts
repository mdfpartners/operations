import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'

export async function GET() {
  const supabase = createSupabaseServiceClient()
  const { data } = await supabase.from('app_settings').select('key, value')
  const settings: Record<string, string> = {}
  for (const row of data || []) {
    settings[row.key] = row.value || ''
  }
  return NextResponse.json(settings)
}

export async function PATCH(request: NextRequest) {
  const body = await request.json()
  const supabase = createSupabaseServiceClient()

  const updates = Object.entries(body as Record<string, string>).map(([key, value]) => ({
    key,
    value,
    updated_at: new Date().toISOString(),
  }))

  const { error } = await supabase
    .from('app_settings')
    .upsert(updates, { onConflict: 'key' })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ ok: true })
}
