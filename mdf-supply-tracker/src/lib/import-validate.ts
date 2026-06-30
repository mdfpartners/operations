export type ImportType =
  | 'accounts'
  | 'requesters'
  | 'vendors'
  | 'supply_catalog'
  | 'requester_account_permissions'

export interface PreviewRow {
  rowNumber: number
  data: Record<string, string>
  action: 'insert' | 'update' | 'rejected'
  errors: string[]
}

// Returns duplicate key for each import type
export function getDuplicateKey(type: ImportType, row: Record<string, string>): string {
  switch (type) {
    case 'accounts': return (row.account_name || '').toLowerCase().trim()
    case 'requesters': return (row.email || '').toLowerCase().trim()
    case 'vendors': return (row.vendor_name || '').toLowerCase().trim()
    case 'supply_catalog': return `${(row.item_name || '').toLowerCase().trim()}|${(row.category || '').toLowerCase().trim()}`
    case 'requester_account_permissions': return `${(row.requester_email || '').toLowerCase().trim()}|${(row.account_name || '').toLowerCase().trim()}`
  }
}

export function validateRow(type: ImportType, row: Record<string, string>): string[] {
  const errors: string[] = []
  switch (type) {
    case 'accounts':
      if (!row.account_name?.trim()) errors.push('account_name is required')
      break
    case 'requesters':
      if (!row.name?.trim()) errors.push('name is required')
      if (row.role && !['requester','analyst','executive','admin'].includes(row.role)) {
        errors.push('role must be one of: requester, analyst, executive, admin')
      }
      break
    case 'vendors':
      if (!row.vendor_name?.trim()) errors.push('vendor_name is required')
      break
    case 'supply_catalog':
      if (!row.item_name?.trim()) errors.push('item_name is required')
      break
    case 'requester_account_permissions':
      if (!row.requester_email?.trim()) errors.push('requester_email is required')
      if (!row.account_name?.trim()) errors.push('account_name is required')
      break
  }
  return errors
}
