/**
 * Direct Supabase REST fetch helpers that let Next.js cache the response
 * at the edge via `next: { revalidate }`. The Supabase JS client doesn't
 * expose the underlying fetch options, so we call the REST API directly.
 */

const supabaseUrl = () => process.env.NEXT_PUBLIC_SUPABASE_URL!
const serviceKey = () => process.env.SUPABASE_SERVICE_ROLE_KEY!

function headers() {
  const key = serviceKey()
  return {
    'apikey': key,
    'Authorization': `Bearer ${key}`,
    'Content-Type': 'application/json',
  }
}

interface FetchOptions {
  revalidate?: number
  tags?: string[]
}

export async function supabaseFetch<T = any>(
  path: string,
  opts: FetchOptions = {}
): Promise<T[]> {
  const url = `${supabaseUrl()}/rest/v1/${path}`
  const res = await fetch(url, {
    headers: headers(),
    next: {
      revalidate: opts.revalidate ?? 30,
      tags: opts.tags,
    },
  })
  if (!res.ok) return []
  return res.json()
}
