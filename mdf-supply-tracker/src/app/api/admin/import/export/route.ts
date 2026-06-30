import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServiceClient } from '@/lib/supabase/server'

type ExportType = 'accounts' | 'requesters' | 'vendors' | 'supply_catalog' | 'requester_account_permissions'

function toCSV(headers: string[], rows: string[][]): string {
  const escape = (v: string) => {
    if (v.includes(',') || v.includes('"') || v.includes('\n')) {
      return `"${v.replace(/"/g, '""')}"`
    }
    return v
  }
  const lines = [headers.map(escape).join(',')]
  for (const row of rows) lines.push(row.map((c) => escape(String(c ?? ''))).join(','))
  return lines.join('\n')
}

export async function GET(request: NextRequest) {
  const type = request.nextUrl.searchParams.get('type') as ExportType
  const supabase = await createSupabaseServiceClient()

  let csv = ''
  let filename = `mdf_${type}_export.csv`

  if (type === 'accounts') {
    const { data } = await supabase.from('accounts').select('*').order('name')
    csv = toCSV(['account_name', 'location', 'active'], (data || []).map((a: any) => [a.name, a.location || '', String(a.active)]))
  } else if (type === 'vendors') {
    const { data } = await supabase.from('vendors').select('*').order('name')
    csv = toCSV(['vendor_name', 'website', 'active'], (data || []).map((v: any) => [v.name, v.website || '', String(v.active)]))
  } else if (type === 'requesters') {
    const { data } = await supabase.from('app_users').select('*').order('name')
    csv = toCSV(['name', 'email', 'phone', 'role', 'active'],
      (data || []).map((u: any) => [u.name, u.email || '', u.phone || '', u.role, String(u.active)]))
  } else if (type === 'supply_catalog') {
    const { data } = await supabase.from('supply_catalog').select('*, preferred_vendor:vendors(name)').order('category').order('item_name')
    csv = toCSV(['item_name', 'category', 'unit_of_measure', 'preferred_vendor_name', 'default_notes', 'active'],
      (data || []).map((i: any) => [i.item_name, i.category || '', i.unit_of_measure || '', i.preferred_vendor?.name || '', i.default_notes || '', String(i.active)]))
  } else if (type === 'requester_account_permissions') {
    const { data } = await supabase
      .from('requester_account_permissions')
      .select('requester:app_users(email), account:accounts(name)')
    csv = toCSV(['requester_email', 'account_name'],
      (data || []).map((p: any) => [p.requester?.email || '', p.account?.name || '']))
  } else {
    return NextResponse.json({ error: 'Invalid export type' }, { status: 400 })
  }

  return new NextResponse(csv, {
    headers: {
      'Content-Type': 'text/csv',
      'Content-Disposition': `attachment; filename="${filename}"`,
    },
  })
}
