export type Role = 'requester' | 'analyst' | 'executive' | 'admin'

export type OrderStatus =
  | 'submitted'
  | 'purchased'
  | 'delivered'
  | 'complete_received'
  | 'cancelled'
  | 'delayed'

export type UrgencyLevel =
  | 'normal_replenishment'
  | 'running_low'
  | 'out_of_stock'
  | 'emergency_service_impacting'

export type LineStatus = 'submitted' | 'purchased' | 'delivered' | 'complete_received' | 'cancelled'

export type AgingBucket = '0' | '1' | '2' | '3' | '4-7' | '8+'

export interface AppUser {
  id: string
  name: string
  email: string | null
  phone: string | null
  role: Role
  request_token: string | null
  active: boolean
  created_at: string
  updated_at: string
}

export interface Account {
  id: string
  name: string
  location: string | null
  active: boolean
  created_at: string
  updated_at: string
}

export interface RequesterAccountPermission {
  id: string
  requester_id: string
  account_id: string
  created_at: string
}

export interface Vendor {
  id: string
  name: string
  website: string | null
  active: boolean
  created_at: string
  updated_at: string
}

export interface SupplyCatalogItem {
  id: string
  item_name: string
  category: string | null
  unit_of_measure: string | null
  preferred_vendor_id: string | null
  default_notes: string | null
  active: boolean
  created_at: string
  updated_at: string
}

export interface SupplyRequest {
  id: string
  order_number: string
  requester_id: string
  account_id: string
  status: OrderStatus
  urgency: UrgencyLevel
  requester_notes: string | null
  internal_notes: string | null
  public_status_token: string
  submitted_at: string
  completed_at: string | null
  cancelled_at: string | null
  created_at: string
  updated_at: string
}

export interface RequestLineItem {
  id: string
  request_id: string
  catalog_item_id: string | null
  other_item_description: string | null
  quantity_requested: number
  quantity_purchased: number | null
  line_status: LineStatus
  created_at: string
  updated_at: string
}

export interface PurchaseDetail {
  id: string
  line_item_id: string
  vendor_id: string | null
  product_url: string | null
  product_name: string | null
  quantity_purchased: number | null
  unit_cost: number | null
  tax: number | null
  shipping: number | null
  total_cost: number | null
  order_confirmation_number: string | null
  estimated_delivery_date: string | null
  created_at: string
  updated_at: string
}

export interface AuditLog {
  id: string
  request_id: string | null
  actor_user_id: string | null
  actor_name: string
  action: string
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  notes: string | null
  created_at: string
}

export interface NotificationLog {
  id: string
  request_id: string | null
  recipient_email: string
  notification_type: string
  status: string
  sent_at: string | null
  error_message: string | null
  created_at: string
}

// Extended types with joins
export interface SupplyRequestWithDetails extends SupplyRequest {
  requester?: AppUser
  account?: Account
  line_items?: RequestLineItemWithDetails[]
}

export interface RequestLineItemWithDetails extends RequestLineItem {
  catalog_item?: SupplyCatalogItem
  purchase_details?: PurchaseDetail[]
}
