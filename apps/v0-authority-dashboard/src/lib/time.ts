/**
 * Time utilities for IST (Asia/Kolkata) display
 * All user-facing timestamps must be in IST
 */

/**
 * Format ISO timestamp to IST date-time string
 */
export function formatIST(isoTimestamp: string): string {
  try {
    const date = new Date(isoTimestamp);
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return '—';
  }
}

/**
 * Format ISO timestamp to IST time only
 */
export function formatISTTime(isoTimestamp: string): string {
  try {
    const date = new Date(isoTimestamp);
    return date.toLocaleTimeString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return '—';
  }
}

/**
 * Format relative time (e.g. "5 min ago") from ISO timestamp
 * Uses IST as reference
 */
export function formatRelativeTime(isoTimestamp: string): string {
  try {
    const date = new Date(isoTimestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr = Math.floor(diffMin / 60);

    if (diffSec < 60) {
      return `${diffSec} sec ago`;
    } else if (diffMin < 60) {
      return `${diffMin} min ago`;
    } else if (diffHr < 24) {
      return `${diffHr} hr ago`;
    } else {
      const diffDays = Math.floor(diffHr / 24);
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    }
  } catch {
    return '—';
  }
}

/**
 * Get current IST time string
 */
export function getCurrentIST(): string {
  return new Date().toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}
