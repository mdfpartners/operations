export const runtime = 'edge'
export const dynamic = 'force-dynamic'

import { createSupabaseServiceClient } from '@/lib/supabase/server'
import SettingsClient from '@/components/admin/SettingsClient'

export default async function SettingsPage() {
  const supabase = createSupabaseServiceClient()
  const { data } = await supabase.from('app_settings').select('key, value')
  const settings: Record<string, string> = {}
  for (const row of data || []) {
    settings[row.key] = row.value || ''
  }
  return <SettingsClient settings={settings} />
}
