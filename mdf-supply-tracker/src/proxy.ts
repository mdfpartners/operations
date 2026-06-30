import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'

const ADMIN_COOKIE = 'mdf_admin_session'
const ADMIN_PASSTHROUGH_PATHS = ['/admin/login']
const ADMIN_PASSTHROUGH_API = ['/api/admin/login', '/api/admin/logout']

function getSecret(): Uint8Array {
  const password = process.env.ADMIN_PASSWORD || ''
  return new TextEncoder().encode(`mdf-admin-jwt-${password}`)
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (!pathname.startsWith('/admin') && !pathname.startsWith('/api/admin')) {
    return NextResponse.next()
  }

  if (
    ADMIN_PASSTHROUGH_PATHS.includes(pathname) ||
    ADMIN_PASSTHROUGH_API.includes(pathname)
  ) {
    return NextResponse.next()
  }

  const token = request.cookies.get(ADMIN_COOKIE)?.value

  if (!token) {
    return redirectToLogin(request)
  }

  try {
    await jwtVerify(token, getSecret())
    return NextResponse.next()
  } catch {
    const response = redirectToLogin(request)
    response.cookies.delete(ADMIN_COOKIE)
    return response
  }
}

function redirectToLogin(request: NextRequest) {
  const loginUrl = new URL('/admin/login', request.url)
  loginUrl.searchParams.set('from', request.nextUrl.pathname)
  return NextResponse.redirect(loginUrl)
}

export const config = {
  matcher: ['/admin/:path*', '/api/admin/:path*'],
}
