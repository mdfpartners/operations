import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'

interface Context { params: Promise<{ id: string }> }

export async function PATCH(request: NextRequest, { params }: Context) {
  const { id } = await params
  const body = await request.json()
  const supabase = await createSupabaseServiceClient()
  const update: Record<string, unknown> = {}
  if (body.name !== undefined) update.name = body.name.trim()
  if (body.email !== undefined) update.email = body.email?.trim() || null
  if (body.phone !== undefined) update.phone = body.phone?.trim() || null
  if (body.active !== undefined) update.active = body.active

  const { error } = await supabase.from('app_users').update(update).eq('id', id)
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // Update account permissions if provided
  if (body.accountIds !== undefined) {
    await supabase.from('requester_account_permissions').delete().eq('requester_id', id)
    if (body.accountIds.length > 0) {
      await supabase.from('requester_account_permissions').insert(
        body.accountIds.map((aid: string) => ({ requester_id: id, account_id: aid }))
      )
    }
  }

  return NextResponse.json({ ok: true })
}
