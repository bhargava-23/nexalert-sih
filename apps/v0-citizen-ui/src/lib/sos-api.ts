/**
 * SOS Emergency Request API client
 * Handles SOS requests to the backend
 */

const BACKEND_URL = import.meta.env.VITE_API_BASE_URL || 'https://raspberrypi.tail39c545.ts.net';

export interface SOSRequest {
  location_lat?: number;
  location_lon?: number;
  message?: string;
  device_info?: string;
}

export interface SOSResponse {
  sos_id: string;
  status: string;
  location_lat?: number;
  location_lon?: number;
  message?: string;
  device_info?: string;
  created_at: string;
  updated_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

/**
 * Send SOS request to backend
 */
export async function sendSOSRequest(request: SOSRequest): Promise<SOSResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/sos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`SOS request failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('[SOS] Request sent successfully:', data);
    return data;
  } catch (error) {
    console.error('[SOS] Failed to send request:', error);
    throw error;
  }
}

/**
 * Get all SOS requests
 */
export async function getSOSRequests(status?: string): Promise<SOSResponse[]> {
  try {
    const url = new URL(`${BACKEND_URL}/api/v1/sos`);
    if (status) {
      url.searchParams.set('status', status);
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`Failed to get SOS requests: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('[SOS] Failed to get requests:', error);
    throw error;
  }
}

/**
 * Update SOS request status
 */
export async function updateSOSStatus(
  sosId: string,
  status: string
): Promise<SOSResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/sos/${sosId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status })
    });

    if (!response.ok) {
      throw new Error(`Failed to update SOS status: ${response.status}`);
    }

    const data = await response.json();
    console.log('[SOS] Status updated successfully:', data);
    return data;
  } catch (error) {
    console.error('[SOS] Failed to update status:', error);
    throw error;
  }
}
