export const dynamic = 'force-dynamic'

import { unstable_cache } from 'next/cache'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import SimpleManager from '@/components/admin/SimpleManager'

const getVendors = unstable_cache(
  async () => {
    const supabase = createSupabaseServiceClient()
    const { data } = await supabase.from('vendors').select('*').order('name')
    return data || []
  },
  ['vendors-list'],
  { revalidate: 30, tags: ['vendors'] }
)

export default async function VendorsPage() {
  const vendors = await getVendors()
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
