export const runtime = 'edge'

import { supabaseFetch } from '@/lib/supabase/edge-fetch'
import SimpleManager from '@/components/admin/SimpleManager'

export default async function VendorsPage() {
  const vendors = await supabaseFetch('vendors?select=*&order=name', {
    revalidate: 30,
    tags: ['vendors'],
  })

  return (
    <SimpleManager
      title="Vendors"
      items={vendors as any[]}
      apiBase="/api/admin/vendors"
      fields={[
        { key: 'name', label: 'Vendor Name', required: true },
        { key: 'website', label: 'Website', type: 'url' },
        { key: 'active', label: 'Active', type: 'checkbox' },
      ]}
      columns={[
        { key: 'name', label: 'Name' },
        { key: 'website', label: 'Website', type: 'url' },
      ]}
    />
  )
}
