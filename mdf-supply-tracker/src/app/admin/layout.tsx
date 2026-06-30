import Link from 'next/link'
import LogoutButton from '@/components/admin/LogoutButton'

const navLinks = [
  { href: '/admin/orders', label: 'Orders' },
  { href: '/admin/catalog', label: 'Catalog' },
  { href: '/admin/vendors', label: 'Vendors' },
  { href: '/admin/accounts', label: 'Accounts' },
  { href: '/admin/requesters', label: 'Requesters' },
  { href: '/admin/import', label: 'Import / Export' },
  { href: '/admin/reports', label: 'Reports' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-6">
              <Link href="/admin/orders" className="text-base font-bold text-gray-900 shrink-0">
                MDF Supply Tracker
              </Link>
              <div className="hidden sm:flex items-center gap-1">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="px-3 py-1.5 text-sm text-gray-600 rounded-md hover:bg-gray-100 hover:text-gray-900"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
            <LogoutButton />
          </div>
        </div>
        {/* Mobile nav */}
        <div className="sm:hidden border-t border-gray-100 px-4 py-2 flex flex-wrap gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="px-2 py-1 text-xs text-gray-600 rounded hover:bg-gray-100"
            >
              {link.label}
            </Link>
          ))}
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">{children}</main>
    </div>
  )
}
