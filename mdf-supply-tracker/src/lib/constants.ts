import type { OrderStatus, UrgencyLevel } from '@/types'

export const ORDER_STATUSES: { value: OrderStatus; label: string }[] = [
  { value: 'submitted', label: 'Submitted' },
  { value: 'purchased', label: 'Purchased' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'complete_received', label: 'Complete / Received' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'delayed', label: 'Delayed' },
]

export const OPEN_STATUSES: OrderStatus[] = ['submitted', 'purchased', 'delivered', 'delayed']

export const URGENCY_LEVELS: { value: UrgencyLevel; label: string }[] = [
  { value: 'normal_replenishment', label: 'Normal Replenishment' },
  { value: 'running_low', label: 'Running Low' },
  { value: 'out_of_stock', label: 'Out of Stock' },
  { value: 'emergency_service_impacting', label: 'Emergency — Service Impacting' },
]

export const STATUS_LABELS: Record<OrderStatus, string> = {
  submitted: 'Submitted',
  purchased: 'Purchased',
  delivered: 'Delivered',
  complete_received: 'Complete / Received',
  cancelled: 'Cancelled',
  delayed: 'Delayed',
}

export const URGENCY_LABELS: Record<UrgencyLevel, string> = {
  normal_replenishment: 'Normal Replenishment',
  running_low: 'Running Low',
  out_of_stock: 'Out of Stock',
  emergency_service_impacting: 'Emergency — Service Impacting',
}

export const STATUS_COLORS: Record<OrderStatus, string> = {
  submitted: 'bg-blue-100 text-blue-800',
  purchased: 'bg-yellow-100 text-yellow-800',
  delivered: 'bg-purple-100 text-purple-800',
  complete_received: 'bg-green-100 text-green-800',
  cancelled: 'bg-gray-100 text-gray-800',
  delayed: 'bg-red-100 text-red-800',
}

export const URGENCY_COLORS: Record<UrgencyLevel, string> = {
  normal_replenishment: 'bg-gray-100 text-gray-700',
  running_low: 'bg-yellow-100 text-yellow-800',
  out_of_stock: 'bg-orange-100 text-orange-800',
  emergency_service_impacting: 'bg-red-100 text-red-800',
}

export const AGING_COLORS: Record<string, string> = {
  '0': 'bg-green-100 text-green-700',
  '1': 'bg-green-100 text-green-700',
  '2': 'bg-yellow-100 text-yellow-700',
  '3': 'bg-yellow-100 text-yellow-700',
  '4-7': 'bg-orange-100 text-orange-700',
  '8+': 'bg-red-100 text-red-800',
}
