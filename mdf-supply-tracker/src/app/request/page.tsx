export const runtime = 'edge'
export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import RequestForm from '@/components/request/RequestForm'

export default async function RequestPage() {
  const supabase = createSupabaseServiceClient()

  const [{ data: accounts }, { data: catalogItems }] = await Promise.all([
    supabase
      .from('accounts')
      .select('id, name')
      .eq('active', true)
      .order('name'),
    supabase
      .from('supply_catalog')
      .select('id, item_name, category, unit_of_measure')
      .eq('active', true)
      .order('category', { ascending: true })
      .order('item_name', { ascending: true }),
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-lg mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Supply Request</h1>
          <p className="text-gray-500 text-sm mt-1">MDF Partners</p>
        </div>
        <RequestForm
          accounts={accounts || []}
          catalogItems={catalogItems || []}
        />
      </div>
    </div>
  )
}
