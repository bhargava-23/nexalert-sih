// NexAlert Citizen Utility Functions
// Real calculations only - NO hardcoded emergency states

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format ISO timestamp to IST display
 * Backend timestamps are UTC, display in IST
 */
export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * Get time elapsed since timestamp
 */
export function getTimeSince(isoString: string): string {
  const date = new Date(isoString)
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

/**
 * Calculate distance between two points using Haversine formula
 * Returns distance in kilometers
 */
export function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371 // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

/**
 * Calculate bearing/direction between two points
 * Returns compass direction (N, NE, E, SE, S, SW, W, NW)
 */
export function getDirection(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): string {
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const y = Math.sin(dLon) * Math.cos((lat2 * Math.PI) / 180)
  const x =
    Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
    Math.sin((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.cos(dLon)
  const bearing = ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360

  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  const index = Math.round(bearing / 45) % 8
  return directions[index]
}

/**
 * Format distance for display
 */
export function formatDistance(km: number): string {
  if (km < 1) return `${Math.round(km * 1000)}m`
  return `${km.toFixed(1)}km`
}

/**
 * Get hazard type display name
 */
export function getHazardTypeName(hazardType: string): string {
  const names: Record<string, string> = {
    fire: 'Fire',
    flood: 'Flood',
    earthquake: 'Earthquake',
    landslide: 'Landslide',
    cyclone: 'Cyclone',
  }
  return names[hazardType.toLowerCase()] || hazardType.toUpperCase()
}

/**
 * Get hazard type icon
 */
export function getHazardIcon(hazardType: string): string {
  const icons: Record<string, string> = {
    fire: '🔥',
    flood: '🌊',
    earthquake: '📳',
    landslide: '⛰️',
    cyclone: '🌀',
  }
  return icons[hazardType.toLowerCase()] || '⚠️'
}

/**
 * Format numeric value with fallback
 */
export function formatValue(
  value: number | null | undefined,
  decimals: number = 1
): string {
  if (value == null) return 'N/A'
  return value.toFixed(decimals)
}
