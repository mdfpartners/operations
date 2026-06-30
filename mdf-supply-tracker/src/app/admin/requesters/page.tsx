export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import RequesterManager from '@/components/admin/RequesterManager'

export default async function RequestersPage() {
  const supabase = await createSupabaseServiceClient()

  const { data: requesters } = await supabase
    .from('app_users')
    .select(`
      id, name, email, phone, role, request_token, active,
      requester_account_permissions(account_id, accounts(id, name))
    `)
    .order('name')

  const { data: accounts } = await supabase.from('accounts').select('id, name').eq('active', true).order('name')
  const baseUrl = process.env.APP_BASE_URL || ''

  return (
    <RequesterManager
      requesters={requesters as any[] || []}
      accounts={accounts as any[] || []}
      baseUrl={baseUrl}
    />
  )
}
