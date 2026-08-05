export const dynamic = 'force-dynamic'

import { unstable_cache } from 'next/cache'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import RequesterManager from '@/components/admin/RequesterManager'

const getRequestersData = unstable_cache(
  async () => {
    const supabase = createSupabaseServiceClient()
    const [{ data: requesters }, { data: accounts }] = await Promise.all([
      supabase
        .from('app_users')
        .select(`
          id, name, email, phone, role, request_token, active,
          requester_account_permissions(account_id, accounts(id, name))
        `)
        .order('name'),
      supabase.from('accounts').select('id, name').eq('active', true).order('name'),
    ])
    return { requesters: requesters || [], accounts: accounts || [] }
  },
  ['requesters-data'],
  { revalidate: 30, tags: ['requesters', 'accounts'] }
)

export default async function RequestersPage() {
  const { requesters, accounts } = await getRequestersData()
  const baseUrl = process.env.APP_BASE_URL || 'https://operations-black-sigma.vercel.app'

  return (
    <RequesterManager
      requesters={requesters as any[]}
      accounts={accounts as any[]}
      baseUrl={baseUrl}
    />
  )
}
