'use client'

export default function LogoutButton() {
  async function handleLogout() {
    await fetch('/api/admin/logout', { method: 'POST' })
    window.location.href = '/admin/login'
  }

  return (
    <button
      onClick={handleLogout}
      className="text-xs text-gray-500 hover:text-gray-800 px-2 py-1 rounded hover:bg-gray-100"
    >
      Sign out
    </button>
  )
}
