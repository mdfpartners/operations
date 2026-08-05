import { createSupabaseServiceClient } from '@/lib/supabase/server'

export async function getNotificationEmails(key: 'internal_notification_emails' | 'executive_notification_emails'): Promise<string[]> {
  try {
    const supabase = createSupabaseServiceClient()
    const { data } = await supabase
      .from('app_settings')
      .select('value')
      .eq('key', key)
      .single()
    if (!data?.value) return []
    return data.value.split('\n').map((e: string) => e.trim()).filter(Boolean)
  } catch {
    // Fall back to env var if DB unavailable
    const envKey = key === 'internal_notification_emails'
      ? 'INTERNAL_NOTIFICATION_EMAILS'
      : 'EXECUTIVE_NOTIFICATION_EMAILS'
    return (process.env[envKey] || '').split(',').map((e) => e.trim()).filter(Boolean)
  }
}
