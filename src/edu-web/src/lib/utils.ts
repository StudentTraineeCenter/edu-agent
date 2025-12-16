import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { ClassValue } from 'clsx'

export function cn(...inputs: Array<ClassValue>) {
  return twMerge(clsx(inputs))
}

export const truncate = (text: string, length: number) => {
  return text.length > length ? text.slice(0, length) + '...' : text
}
