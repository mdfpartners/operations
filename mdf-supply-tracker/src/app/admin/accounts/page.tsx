export const runtime = 'edge'

import { supabaseFetch } from '@/lib/supabase/edge-fetch'
import SimpleManager from '@/components/admin/SimpleManager'

export default async function AccountsPage() {
  const accounts = await supabaseFetch('accounts?select=*&order=name', {
    revalidate: 30,
    tags: ['accounts'],
  })

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
