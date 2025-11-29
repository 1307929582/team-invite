import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.extend(utc)
dayjs.extend(timezone)

const TIMEZONE = 'Asia/Shanghai'

/**
 * 格式化日期时间（UTC+8）
 */
export function formatDate(date: string | Date | undefined | null, format = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!date) return '-'
  return dayjs.utc(date).tz(TIMEZONE).format(format)
}

/**
 * 格式化短日期（MM-DD HH:mm）
 */
export function formatShortDate(date: string | Date | undefined | null): string {
  return formatDate(date, 'MM-DD HH:mm')
}

/**
 * 格式化日期（YYYY-MM-DD）
 */
export function formatDateOnly(date: string | Date | undefined | null): string {
  return formatDate(date, 'YYYY-MM-DD')
}

/**
 * 获取 dayjs 对象（UTC+8）
 */
export function toLocalDate(date: string | Date | undefined | null) {
  if (!date) return null
  return dayjs.utc(date).tz(TIMEZONE)
}
