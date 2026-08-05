export const revalidate = 30

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import CatalogManager from '@/components/admin/CatalogManager'

export default async function CatalogPage() {
  const supabase = createSupabaseServiceClient()
  const { data: items } = await supabase
    .from('supply_catalog')
    .select('*, preferred_vendor:vendors(id, name)')
    .order('category', { ascending: true })
    .order('item_name', { ascending: true })

  const { data: vendors } = await supabase
    .from('vendors')
    .select('id, name')
    .eq('active', true)
    .order('name')

  return <CatalogManager items={items as any[] || []} vendors={vendors as any[] || []} />
}
