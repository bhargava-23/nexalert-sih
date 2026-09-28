/**
 * Notification Settings Component
 * Manages Web Push notification subscription flow
 */

import { useState, useEffect } from 'react';
import { Bell, Check, AlertTriangle, Loader2 } from 'lucide-react';
import {
  isPushSupported,
  getNotificationPermission,
  setupPushNotifications,
  getExistingSubscription,
  isSubscriptionCompatible,
  unsubscribeFromPush,
  type DiagnosticResult
} from '@/lib/web-push';

type NotificationState =
  | { status: 'checking' }
  | { status: 'not-supported' }
  | { status: 'not-subscribed' }
  | { status: 'subscribed'; subscription_id: string }
  | { status: 'subscribing' }
  | { status: 'error'; error: string; diagnostic?: DiagnosticResult };

export function NotificationSettings() {
  const [state, setState] = useState<NotificationState>({ status: 'checking' });

  useEffect(() => {
    checkNotificationState();
  }, []);

  async function checkNotificationState() {
    try {
      // Check if push is supported
      if (!isPushSupported()) {
        setState({ status: 'not-supported' });
        return;
      }

      // Check current permission
      const permission = getNotificationPermission();
      if (permission === 'denied') {
        setState({ status: 'not-subscribed' });
        return;
      }

      // Check if already subscribed
      const existingSub = await getExistingSubscription();
      if (existingSub && permission === 'granted') {
        // IMPORTANT: Check if subscription uses current VAPID key
        const isCompatible = await isSubscriptionCompatible();

        if (!isCompatible) {
          // VAPID key has changed - need to renew subscription
          console.log('[NotificationSettings] VAPID key changed - renewing subscription');
          setState({ status: 'not-subscribed' });
          return;
        }

        // Subscription is valid and compatible
        setState({ status: 'subscribed', subscription_id: 'existing' });
      } else {
        setState({ status: 'not-subscribed' });
      }
    } catch (error) {
      console.error('[NotificationSettings] Check failed:', error);
      setState({ status: 'not-subscribed' });
    }
  }

  async function handleEnableNotifications() {
    setState({ status: 'subscribing' });

    try {
      // Run diagnostic setup
      const result = await setupPushNotifications();

      console.log('[NotificationSettings] Push notifications diagnostic complete:', result);

      // Store diagnostic results in error state for display
      if (result.diagnostic) {
        setState({
          status: 'error',
          error: 'Web Push Diagnostic Complete',
          diagnostic: result.diagnostic
        });
      } else {
        setState({ status: 'subscribed', subscription_id: result.subscription_id || 'diagnostic' });
      }
    } catch (error: any) {
      console.error('[NotificationSettings] Setup failed:', error);
      setState({
        status: 'error',
        error: error.message || 'Failed to enable notifications',
        diagnostic: (error as any).diagnostic
      });
    }
  }

  if (state.status === 'checking') {
    return (
      <div className="flex items-center gap-2 text-sm text-[#5a6763]">
        <Loader2 size={16} className="animate-spin" />
        Checking notification status...
      </div>
    );
  }

  if (state.status === 'not-supported') {
    return (
      <div className="rounded-xl border border-[#d9d3c6] bg-[#eeeae1] p-3 text-sm text-[#5a6763]">
        <AlertTriangle size={16} className="mb-1 inline text-[#a07a2d]" /> Push notifications are not supported in this browser.
      </div>
    );
  }

  if (state.status === 'subscribed') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-[#abd8ca] bg-[#d9efe8] px-3 py-2 text-sm text-[#195d52]">
        <Check size={16} />
        <span className="font-semibold">Notifications enabled</span>
      </div>
    );
  }

  if (state.status === 'subscribing') {
    return (
      <button
        type="button"
        disabled
        className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-[#195d52] bg-[#e3f1ec] text-sm font-bold text-[#195d52]"
      >
        <Loader2 size={18} className="animate-spin" />
        Enabling notifications...
      </button>
    );
  }

  if (state.status === 'error') {
    return (
      <div className="space-y-2">
        <div className="rounded-xl border border-[#e7b1a5] bg-[#f6d9d2] p-3 text-sm text-[#923d34]">
          <AlertTriangle size={16} className="mb-1 inline" /> {state.error}
        </div>

        {/* TEMPORARY WEB PUSH DIAGNOSTIC PANEL */}
        {state.diagnostic && (
          <div className="mt-4 space-y-2 rounded-xl border-2 border-[#5a6763] bg-[#f4f1ea] p-4 text-xs">
            <div className="mb-3 text-sm font-bold text-[#195d52]">🔍 Web Push Diagnostic</div>

            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="font-semibold">Service worker active:</span>
                <span className={state.diagnostic.serviceWorkerActive ? 'text-green-700' : 'text-red-700'}>
                  {state.diagnostic.serviceWorkerActive ? 'PASS' : 'FAIL'}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="font-semibold">PushManager available:</span>
                <span className={state.diagnostic.pushManagerAvailable ? 'text-green-700' : 'text-red-700'}>
                  {state.diagnostic.pushManagerAvailable ? 'PASS' : 'FAIL'}
                </span>
              </div>

              <div className="flex justify-between border-t border-[#d9d3c6] pt-1 mt-1">
                <span className="font-semibold">Service worker scope:</span>
                <span className="text-[#5a6763] break-all text-right max-w-[60%]">{state.diagnostic.scope}</span>
              </div>

              <div className="flex justify-between">
                <span className="font-semibold">Current origin:</span>
                <span className="text-[#5a6763] break-all text-right max-w-[60%]">{state.diagnostic.origin}</span>
              </div>

              <div className="flex justify-between border-t border-[#d9d3c6] pt-1 mt-1">
                <span className="font-semibold">VAPID key length:</span>
                <span className="text-[#5a6763]">{state.diagnostic.vapidKeyLength} bytes</span>
              </div>

              <div className="flex justify-between">
                <span className="font-semibold">VAPID first byte:</span>
                <span className="text-[#5a6763]">{state.diagnostic.vapidFirstByte}</span>
              </div>

              <div className="border-t-2 border-[#5a6763] pt-2 mt-2">
                <div className="font-bold text-[#195d52] mb-1">TEST A (no VAPID key):</div>
                <div className="flex justify-between">
                  <span className="font-semibold">Status:</span>
                  <span className={state.diagnostic.testA.status === 'PASS' ? 'text-green-700 font-bold' : 'text-red-700 font-bold'}>
                    {state.diagnostic.testA.status}
                  </span>
                </div>
                {state.diagnostic.testA.status === 'FAIL' && (
                  <>
                    <div className="mt-1">
                      <span className="font-semibold">Error name:</span> {state.diagnostic.testA.errorName}
                    </div>
                    <div className="mt-1">
                      <span className="font-semibold">Error message:</span> {state.diagnostic.testA.errorMessage}
                    </div>
                  </>
                )}
                {state.diagnostic.testA.status === 'PASS' && state.diagnostic.testA.endpoint && (
                  <div className="mt-1 break-all">
                    <span className="font-semibold">Endpoint:</span> {state.diagnostic.testA.endpoint}
                  </div>
                )}
              </div>

              <div className="border-t-2 border-[#5a6763] pt-2 mt-2">
                <div className="font-bold text-[#195d52] mb-1">TEST B (with NexAlert VAPID key):</div>
                <div className="flex justify-between">
                  <span className="font-semibold">Status:</span>
                  <span className={state.diagnostic.testB.status === 'PASS' ? 'text-green-700 font-bold' : 'text-red-700 font-bold'}>
                    {state.diagnostic.testB.status}
                  </span>
                </div>
                {state.diagnostic.testB.status === 'FAIL' && (
                  <>
                    <div className="mt-1">
                      <span className="font-semibold">Error name:</span> {state.diagnostic.testB.errorName}
                    </div>
                    <div className="mt-1">
                      <span className="font-semibold">Error message:</span> {state.diagnostic.testB.errorMessage}
                    </div>
                  </>
                )}
                {state.diagnostic.testB.status === 'PASS' && state.diagnostic.testB.endpoint && (
                  <div className="mt-1 break-all">
                    <span className="font-semibold">Endpoint:</span> {state.diagnostic.testB.endpoint}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={handleEnableNotifications}
          className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-[#195d52] bg-[#fff8f4] text-sm font-bold text-[#195d52] hover:bg-[#e3f1ec]"
        >
          <Bell size={18} />
          Try Again
        </button>
      </div>
    );
  }

  // not-subscribed
  return (
    <div className="space-y-3">
      <p className="text-sm text-[#5a6763]">
        Enable notifications to receive real-time hazard alerts on this device.
      </p>
      <button
        type="button"
        onClick={handleEnableNotifications}
        data-testid="button-enable-notifications"
        className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-[#195d52] bg-[#195d52] text-sm font-bold text-[#fff8f4] hover:bg-[#1f6860]"
      >
        <Bell size={18} />
        Enable Notifications
      </button>
    </div>
  );
}
