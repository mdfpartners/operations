export const runtime = 'edge'

import { supabaseFetch } from '@/lib/supabase/edge-fetch'
import CatalogManager from '@/components/admin/CatalogManager'

export default async function CatalogPage() {
  const [items, vendors] = await Promise.all([
    supabaseFetch(
      'supply_catalog?select=*,preferred_vendor:vendors(id,name)&order=category.asc,item_name.asc',
      { revalidate: 30, tags: ['catalog'] }
    ),
    supabaseFetch(
      'vendors?select=id,name&active=eq.true&order=name',
      { revalidate: 30, tags: ['vendors'] }
    ),
  ])

  return <CatalogManager items={items as any[]} vendors={vendors as any[]} />
}
