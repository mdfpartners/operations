export const dynamic = 'force-dynamic'

import { unstable_cache } from 'next/cache'
import { createSupabaseServiceClient } from '@/lib/supabase/server'
import CatalogManager from '@/components/admin/CatalogManager'

const getCatalogData = unstable_cache(
  async () => {
    const supabase = createSupabaseServiceClient()
    const [{ data: items }, { data: vendors }] = await Promise.all([
      supabase
        .from('supply_catalog')
        .select('*, preferred_vendor:vendors(id, name)')
        .order('category', { ascending: true })
        .order('item_name', { ascending: true }),
      supabase
        .from('vendors')
        .select('id, name')
        .eq('active', true)
        .order('name'),
    ])
    return { items: items || [], vendors: vendors || [] }
  },
  ['catalog-data'],
  { revalidate: 30, tags: ['catalog', 'vendors'] }
)

export default async function CatalogPage() {
  const { items, vendors } = await getCatalogData()
  return <CatalogManager items={items as any[]} vendors={vendors as any[]} />
}
