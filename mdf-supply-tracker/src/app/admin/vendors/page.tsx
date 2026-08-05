export const revalidate = 30

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import SimpleManager from '@/components/admin/SimpleManager'

export default async function VendorsPage() {
  const supabase = await createSupabaseServiceClient()
  const { data: vendors } = await supabase.from('vendors').select('*').order('name')
  return (
    <SimpleManager
      title="Vendors"
      items={vendors as any[] || []}
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
