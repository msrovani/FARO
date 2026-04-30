/**
 * F.A.R.O. Logger - Structured logging utility
 * 
 * Provides safe logging that doesn't leak sensitive data in production.
 * In development: logs to console
 * In production: sends to error tracking service (Sentry) or stays silent
 */

const isDevelopment = process.env.NODE_ENV === 'development';
const isTest = process.env.NODE_ENV === 'test';

/**
 * Sanitize sensitive data from objects before logging
 */
function sanitizeForLogging(obj: Record<string, unknown> | null | undefined): Record<string, unknown> {
  if (!obj || typeof obj !== 'object') return {};
  
  const sensitiveKeys = ['password', 'token', 'secret', 'key', 'authorization', 'cookie', 'cpf', 'email'];
  const sanitized: Record<string, unknown> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const lowerKey = key.toLowerCase();
    if (sensitiveKeys.some(sk => lowerKey.includes(sk))) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      sanitized[key] = sanitizeForLogging(value as Record<string, unknown>);
    } else if (Array.isArray(value)) {
      sanitized[key] = value.map(item => 
        typeof item === 'object' && item !== null 
          ? sanitizeForLogging(item as Record<string, unknown>)
          : item
      );
    } else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
}

/**
 * Safe stringify that removes sensitive data
 */
function safeStringify(obj: unknown): string {
  try {
    if (obj === null || obj === undefined) return '';
    if (typeof obj === 'string') return obj;
    if (typeof obj === 'number' || typeof obj === 'boolean') return String(obj);
    if (typeof obj === 'object') {
      return JSON.stringify(sanitizeForLogging(obj as Record<string, unknown>), null, 2);
    }
    return String(obj);
  } catch {
    return '[Unable to stringify]';
  }
}

// ============================================================================
// Logger implementation
// ============================================================================
export const logger = {
  /**
   * Debug logging - only in development
   */
  debug: (message: string, meta?: Record<string, unknown>): void => {
    if (isDevelopment || isTest) {
      // eslint-disable-next-line no-console
      console.debug(`[DEBUG] ${message}`, meta ? safeStringify(meta) : '');
    }
    // Production: completely silent
  },

  /**
   * Info logging - development only for now
   */
  info: (message: string, meta?: Record<string, unknown>): void => {
    if (isDevelopment || isTest) {
      // eslint-disable-next-line no-console
      console.info(`[INFO] ${message}`, meta ? safeStringify(meta) : '');
    }
    // TODO: Send to analytics service in production if needed
  },

  /**
   * Warning logging
   */
  warn: (message: string, meta?: Record<string, unknown>): void => {
    if (isDevelopment || isTest) {
      // eslint-disable-next-line no-console
      console.warn(`[WARN] ${message}`, meta ? safeStringify(meta) : '');
    }
    // TODO: Send to error tracking service in production
  },

  /**
   * Error logging - never exposes sensitive data
   */
  error: (message: string, error?: Error | unknown, meta?: Record<string, unknown>): void => {
    if (isDevelopment || isTest) {
      // Development: full error details
      // eslint-disable-next-line no-console
      console.error(`[ERROR] ${message}`, error, meta ? safeStringify(meta) : '');
    } else {
      // Production: NEVER log to console
      // Send to error tracking service with sanitized data
      const sanitizedMeta = meta ? sanitizeForLogging(meta) : undefined;
      
      // Send to error tracking if available
      if (typeof window !== 'undefined') {
        const win = window as Window & { Sentry?: { captureException: (err: Error, ctx?: unknown) => void; captureMessage: (msg: string, ctx?: unknown) => void } };
        if (win.Sentry) {
          if (error instanceof Error) {
            win.Sentry.captureException(error, { extra: sanitizedMeta });
          } else {
            win.Sentry.captureMessage(message, { extra: sanitizedMeta });
          }
        }
      }
    }
  },

  /**
   * API error logging with automatic sanitization
   */
  apiError: (url: string | undefined, status: number | undefined, code?: string, message?: string): void => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.error(`[API Error] ${status} ${code}: ${url} - ${message}`);
    }
    // Production: Don't log API errors to console (handled by UI)
    // Only track 5xx errors for monitoring
    if (!isDevelopment && status && status >= 500) {
      if (typeof window !== 'undefined') {
        const win = window as Window & { Sentry?: { captureMessage: (msg: string, ctx?: unknown) => void } };
        win.Sentry?.captureMessage(`API ${status} Error`, {
          extra: { url: url?.split('?')[0], status, code }, // Remove query params
        });
      }
    }
  },

  /**
   * Group related logs (development only)
   */
  group: (label: string): void => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.group(label);
    }
  },

  groupEnd: (): void => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.groupEnd();
    }
  },
};

// Default export
export default logger;
