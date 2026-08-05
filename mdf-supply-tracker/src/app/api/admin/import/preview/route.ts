import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import {
  type ImportType,
  type PreviewRow,
  getDuplicateKey,
  validateRow,
} from '@/lib/import-validate'

export async function POST(request: NextRequest) {
  const { type, rows }: { type: ImportType; rows: Record<string, string>[] } = await request.json()

  if (!rows?.length) return NextResponse.json({ rows: [] })

  const supabase = createSupabaseServiceClient()

  // Load existing records for match detection
  let existing: Record<string, unknown>[] = []
  switch (type) {
    case 'accounts':
      existing = (await supabase.from('accounts').select('id, name')).data || []
      break
    case 'requesters':
      existing = (await supabase.from('app_users').select('id, email, request_token')).data || []
      break
    case 'vendors':
      existing = (await supabase.from('vendors').select('id, name')).data || []
      break
    case 'supply_catalog':
      existing = (await supabase.from('supply_catalog').select('id, item_name, category')).data || []
      break
    case 'requester_account_permissions':
      const [reqRes, accRes, permRes] = await Promise.all([
        supabase.from('app_users').select('id, email'),
        supabase.from('accounts').select('id, name'),
        supabase.from('requester_account_permissions').select('requester_id, account_id'),
      ])
      existing = permRes.data || []
      break
  }

  // Build existing key sets
  const existingKeys = new Set<string>()
  for (const rec of existing) {
    let key = ''
    switch (type) {
      case 'accounts': key = ((rec.name as string) || '').toLowerCase().trim(); break
      case 'requesters': key = ((rec.email as string) || '').toLowerCase().trim(); break
      case 'vendors': key = ((rec.name as string) || '').toLowerCase().trim(); break
      case 'supply_catalog':
        key = `${((rec.item_name as string) || '').toLowerCase().trim()}|${((rec.category as string) || '').toLowerCase().trim()}`; break
    }
    if (key) existingKeys.add(key)
  }

  // Track intra-file duplicates
  const seenKeys = new Set<string>()
  const previewRows: PreviewRow[] = []

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]
    const errors = validateRow(type, row)
    const dupKey = getDuplicateKey(type, row)

    let action: 'insert' | 'update' | 'rejected' = 'insert'

    if (errors.length > 0) {
      action = 'rejected'
    } else if (dupKey && seenKeys.has(dupKey)) {
      errors.push('Duplicate entry appears earlier in this upload')
      action = 'rejected'
    } else {
      if (dupKey) seenKeys.add(dupKey)
      // Check against existing db records
      if (type !== 'requester_account_permissions' && existingKeys.has(dupKey)) {
        action = 'update'
      }
      // For permissions, we check after resolving email/name → ids (done at confirm time)
    }

    previewRows.push({ rowNumber: i + 1, data: row, action, errors })
  }

  return NextResponse.json({ rows: previewRows })
}
