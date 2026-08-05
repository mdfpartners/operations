export const runtime = 'edge'

import { supabaseFetch } from '@/lib/supabase/edge-fetch'
import RequesterManager from '@/components/admin/RequesterManager'

export default async function RequestersPage() {
  const [requesters, accounts] = await Promise.all([
    supabaseFetch(
      'app_users?select=id,name,email,phone,role,request_token,active,requester_account_permissions(account_id,accounts(id,name))&order=name',
      { revalidate: 30, tags: ['requesters'] }
    ),
    supabaseFetch(
      'accounts?select=id,name&active=eq.true&order=name',
      { revalidate: 30, tags: ['accounts'] }
    ),
  ])

  const baseUrl = process.env.APP_BASE_URL || 'https://operations-black-sigma.vercel.app'

  return (
    <RequesterManager
      requesters={requesters as any[]}
      accounts={accounts as any[]}
      baseUrl={baseUrl}
    />
  )
}
