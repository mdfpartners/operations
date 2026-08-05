export const dynamic = 'force-dynamic'

import { unstable_cache } from 'next/cache'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import SimpleManager from '@/components/admin/SimpleManager'

const getAccounts = unstable_cache(
  async () => {
    const supabase = createSupabaseServiceClient()
    const { data } = await supabase.from('accounts').select('*').order('name')
    return data || []
  },
  ['accounts-list'],
  { revalidate: 30, tags: ['accounts'] }
)

export default async function AccountsPage() {
  const accounts = await getAccounts()
  return (
    <SimpleManager
      title="Accounts"
      items={accounts as any[]}
      apiBase="/api/admin/accounts"
      fields={[
        { key: 'name', label: 'Account Name', required: true },
        { key: 'location', label: 'Location' },
        { key: 'active', label: 'Active', type: 'checkbox' },
      ]}
      columns={[
        { key: 'name', label: 'Name' },
        { key: 'location', label: 'Location' },
      ]}
    />
  )
}
