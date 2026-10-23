import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import { type ImportType, type PreviewRow } from '@/lib/import-validate'
import { randomBytes } from 'crypto'

function generateToken(): string {
  return randomBytes(24).toString('hex')
}

function parseBool(v: string | undefined): boolean {
  if (v === undefined || v === '') return true
  return v.toLowerCase() === 'true' || v === '1'
}

function nonEmpty(v: string | undefined): string | null {
  return v?.trim() || null
}

export async function POST(request: NextRequest) {
  const { type, rows, fileName }: { type: ImportType; rows: PreviewRow[]; fileName: string } =
    await request.json()

  const supabase = createSupabaseServiceClient()
  const importable = rows.filter((r) => r.action !== 'rejected')
  const rejected = rows.filter((r) => r.action === 'rejected')
  const duplicateCount = rejected.filter((r) =>
    r.errors.some((e) => e.includes('Duplicate'))
  ).length

  let inserted = 0
  let updated = 0

  if (type === 'accounts') {
    const existing: any[] = (await supabase.from('accounts').select('id, name')).data || []
    const nameToId = new Map(existing.map((a: any) => [a.name.toLowerCase().trim(), a.id]))
    for (const row of importable) {
      const name = row.data.account_name.trim()
      const existingId = nameToId.get(name.toLowerCase())
      const payload: any = {}
      if (name) payload.name = name
      if (nonEmpty(row.data.location) !== null) payload.location = nonEmpty(row.data.location)
      if (row.data.active !== undefined) payload.active = parseBool(row.data.active)
      if (existingId) {
        await supabase.from('accounts').update(payload).eq('id', existingId)
        updated++
      } else {
        await supabase.from('accounts').insert({ name, location: nonEmpty(row.data.location), active: parseBool(row.data.active) })
        inserted++
      }
    }
  } else if (type === 'vendors') {
    const existing = (await supabase.from('vendors').select('id, name')).data || []
    const nameToId = new Map(existing.map((v: any) => [v.name.toLowerCase().trim(), v.id]))
    for (const row of importable) {
      const name = row.data.vendor_name.trim()
      const existingId = nameToId.get(name.toLowerCase())
      const payload: any = {}
      if (name) payload.name = name
      if (nonEmpty(row.data.website) !== null) payload.website = nonEmpty(row.data.website)
      if (row.data.active !== undefined) payload.active = parseBool(row.data.active)
      if (existingId) {
        await supabase.from('vendors').update(payload).eq('id', existingId)
        updated++
      } else {
        await supabase.from('vendors').insert({ name, website: nonEmpty(row.data.website), active: parseBool(row.data.active) })
        inserted++
      }
    }
  } else if (type === 'requesters') {
    const existing: any[] = (await supabase.from('app_users').select('id, email, request_token')).data || []
    const emailToUser = new Map(existing.map((u: any) => [u.email?.toLowerCase().trim(), u]))
    for (const row of importable) {
      const email = nonEmpty(row.data.email)
      const existingUser = email ? emailToUser.get(email.toLowerCase()) : null
      if (existingUser) {
        const payload: any = {}
        if (nonEmpty(row.data.name)) payload.name = nonEmpty(row.data.name)
        if (email) payload.email = email
        if (nonEmpty(row.data.phone)) payload.phone = nonEmpty(row.data.phone)
        if (row.data.active !== undefined) payload.active = parseBool(row.data.active)
        await supabase.from('app_users').update(payload).eq('id', existingUser.id)
        updated++
      } else {
        const role = row.data.role?.trim() || 'requester'
        await supabase.from('app_users').insert({
          name: row.data.name.trim(),
          email,
          phone: nonEmpty(row.data.phone),
          role,
          request_token: role === 'requester' ? generateToken() : null,
          active: parseBool(row.data.active),
        })
        inserted++
      }
    }
  } else if (type === 'supply_catalog') {
    const existing = (await supabase.from('supply_catalog').select('id, item_name, category')).data || []
    const vendorList = (await supabase.from('vendors').select('id, name')).data || []
    const vendorNameToId = new Map(vendorList.map((v: any) => [v.name.toLowerCase().trim(), v.id]))
    const catKey = (item_name: string, category: string) => `${item_name.toLowerCase().trim()}|${(category || '').toLowerCase().trim()}`
    const itemKeyToId = new Map(existing.map((i: any) => [catKey(i.item_name, i.category || ''), i.id]))
    for (const row of importable) {
      const key = catKey(row.data.item_name, row.data.category || '')
      const existingId = itemKeyToId.get(key)
      const vendorId = row.data.preferred_vendor_name ? vendorNameToId.get(row.data.preferred_vendor_name.toLowerCase().trim()) || null : null
      if (existingId) {
        const payload: any = {}
        if (nonEmpty(row.data.item_name)) payload.item_name = nonEmpty(row.data.item_name)
        if (nonEmpty(row.data.category)) payload.category = nonEmpty(row.data.category)
        if (nonEmpty(row.data.unit_of_measure)) payload.unit_of_measure = nonEmpty(row.data.unit_of_measure)
        if (vendorId !== null) payload.preferred_vendor_id = vendorId
        if (nonEmpty(row.data.default_notes)) payload.default_notes = nonEmpty(row.data.default_notes)
        if (row.data.active !== undefined) payload.active = parseBool(row.data.active)
        await supabase.from('supply_catalog').update(payload).eq('id', existingId)
        updated++
      } else {
        await supabase.from('supply_catalog').insert({
          item_name: row.data.item_name.trim(),
          category: nonEmpty(row.data.category),
          unit_of_measure: nonEmpty(row.data.unit_of_measure),
          preferred_vendor_id: vendorId,
          default_notes: nonEmpty(row.data.default_notes),
          active: parseBool(row.data.active),
        })
        inserted++
      }
    }
  } else if (type === 'requester_account_permissions') {
    const users = (await supabase.from('app_users').select('id, email')).data || []
    const accounts = (await supabase.from('accounts').select('id, name')).data || []
    const emailToId = new Map(users.map((u: any) => [u.email?.toLowerCase().trim(), u.id]))
    const nameToAccId = new Map(accounts.map((a: any) => [a.name.toLowerCase().trim(), a.id]))
    const existingPerms = (await supabase.from('requester_account_permissions').select('requester_id, account_id')).data || []
    const permSet = new Set(existingPerms.map((p: any) => `${p.requester_id}|${p.account_id}`))
    for (const row of importable) {
      const reqId = emailToId.get(row.data.requester_email?.toLowerCase().trim())
      const accId = nameToAccId.get(row.data.account_name?.toLowerCase().trim())
      if (!reqId || !accId) { rejected.push({ ...row, errors: ['Requester email or account not found in database'] }); continue }
      const key = `${reqId}|${accId}`
      if (!permSet.has(key)) {
        await supabase.from('requester_account_permissions').insert({ requester_id: reqId, account_id: accId })
        inserted++
        permSet.add(key)
      } else {
        updated++
      }
    }
  }

  // Audit log
  await supabase.from('audit_log').insert({
    actor_name: 'Admin',
    action: 'bulk_import',
    new_value: {
      import_type: type,
      file_name: fileName,
      total: rows.length,
      inserted,
      updated,
      rejected: rejected.length,
      duplicates: duplicateCount,
    },
    notes: `Bulk import: ${type}`,
  })

  return NextResponse.json({
    summary: {
      total: rows.length,
      inserted,
      updated,
      rejected: rejected.length,
      duplicates: duplicateCount,
    },
  })
}
