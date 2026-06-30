export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import SimpleManager from '@/components/admin/SimpleManager'

export default async function AccountsPage() {
  const supabase = await createSupabaseServiceClient()
  const { data: accounts } = await supabase.from('accounts').select('*').order('name')
  return (
    <SimpleManager
      title="Accounts"
      items={accounts as any[] || []}
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
