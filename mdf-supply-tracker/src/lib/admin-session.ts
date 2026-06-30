import { SignJWT, jwtVerify } from 'jose'

const COOKIE_NAME = 'mdf_admin_session'
const SESSION_DURATION_HOURS = 10

function getSecret(): Uint8Array {
  const password = process.env.ADMIN_PASSWORD
  if (!password) throw new Error('ADMIN_PASSWORD environment variable is not set')
  return new TextEncoder().encode(`mdf-admin-jwt-${password}`)
}

export async function createSessionToken(): Promise<string> {
  const secret = getSecret()
  return new SignJWT({ role: 'admin' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_DURATION_HOURS}h`)
    .sign(secret)
}

export async function verifySessionToken(token: string): Promise<boolean> {
  try {
    const secret = getSecret()
    await jwtVerify(token, secret)
    return true
  } catch {
    return false
  }
}

export const ADMIN_COOKIE_NAME = COOKIE_NAME
export const SESSION_MAX_AGE_SECONDS = SESSION_DURATION_HOURS * 3600
