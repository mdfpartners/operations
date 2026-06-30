import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { randomBytes } from 'crypto'

function generateToken(): string {
  return randomBytes(24).toString('hex')
}

export async function POST(request: NextRequest) {
  const { name, email, phone, role, active, accountIds } = await request.json()
  if (!name?.trim()) return NextResponse.json({ error: 'Name is required' }, { status: 400 })
  const supabase = await createSupabaseServiceClient()
  const token = role === 'requester' ? generateToken() : null
  const { data: user, error } = await supabase.from('app_users').insert({
    name: name.trim(),
    email: email?.trim() || null,
    phone: phone?.trim() || null,
    role: role || 'requester',
    request_token: token,
    active: active !== false,
  }).select().single()
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  if (accountIds?.length && role === 'requester') {
    await supabase.from('requester_account_permissions').insert(
      accountIds.map((aid: string) => ({ requester_id: user.id, account_id: aid }))
    )
  }

  return NextResponse.json(user)
}
