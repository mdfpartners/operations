import { toZonedTime } from 'date-fns-tz'
import type { AgingBucket, OrderStatus } from '@/types'

const APP_TIMEZONE = process.env.APP_TIMEZONE || 'America/Chicago'

export function getCalendarDaysOutstanding(
  submittedAt: string,
  status: OrderStatus,
  completedAt: string | null,
  cancelledAt: string | null
): number {
  const submitted = toZonedTime(new Date(submittedAt), APP_TIMEZONE)

  let endDate: Date
  if (status === 'complete_received' && completedAt) {
    endDate = toZonedTime(new Date(completedAt), APP_TIMEZONE)
  } else if (status === 'cancelled' && cancelledAt) {
    endDate = toZonedTime(new Date(cancelledAt), APP_TIMEZONE)
  } else {
    endDate = toZonedTime(new Date(), APP_TIMEZONE)
  }

  // Calendar days difference
  const submittedDay = new Date(
    submitted.getFullYear(),
    submitted.getMonth(),
    submitted.getDate()
  )
  const endDay = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate())
  const msPerDay = 1000 * 60 * 60 * 24
  return Math.max(0, Math.round((endDay.getTime() - submittedDay.getTime()) / msPerDay))
}

export function getAgingBucket(
  submittedAt: string,
  status: OrderStatus,
  completedAt: string | null,
  cancelledAt: string | null
): AgingBucket {
  const days = getCalendarDaysOutstanding(submittedAt, status, completedAt, cancelledAt)
  if (days === 0) return '0'
  if (days === 1) return '1'
  if (days === 2) return '2'
  if (days === 3) return '3'
  if (days <= 7) return '4-7'
  return '8+'
}

export const AGING_BUCKET_ORDER: AgingBucket[] = ['0', '1', '2', '3', '4-7', '8+']
