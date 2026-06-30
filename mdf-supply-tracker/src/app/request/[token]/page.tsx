export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import RequestForm from '@/components/request/RequestForm'

interface PageProps {
  params: Promise<{ token: string }>
}

export default async function RequestPage({ params }: PageProps) {
  const { token } = await params
  const supabase = createSupabaseServiceClient()

  // Token lookup — server-side, scoped to this token only
  const { data: requester } = await supabase
    .from('app_users')
    .select('id, name, email, role, active')
    .eq('request_token', token)
    .eq('role', 'requester')
    .single()

  if (!requester || !requester.active) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-sm w-full text-center">
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Invalid Link</h1>
          <p className="text-gray-500 text-sm">
            This request link is not valid or has been deactivated. Please contact your supervisor
            or the MDF supply team for a new link.
          </p>
        </div>
      </div>
    )
  }

  // Fetch only accounts this requester is permitted to access
  const { data: permissions } = await supabase
    .from('requester_account_permissions')
    .select('account_id, accounts(id, name)')
    .eq('requester_id', requester.id)

  const accounts = (permissions || [])
    .map((p: any) => p.accounts as { id: string; name: string } | null)
    .filter(Boolean) as { id: string; name: string }[]

  // Fetch active catalog items — only requester-safe fields
  const { data: catalogItems } = await supabase
    .from('supply_catalog')
    .select('id, item_name, category, unit_of_measure')
    .eq('active', true)
    .order('category', { ascending: true })
    .order('item_name', { ascending: true })

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-lg mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Supply Request</h1>
          <p className="text-gray-500 text-sm mt-1">MDF Partners</p>
        </div>
        <RequestForm
          requester={{ id: requester.id, name: requester.name }}
          accounts={accounts}
          catalogItems={catalogItems || []}
          token={token}
        />
      </div>
    </div>
  )
}
