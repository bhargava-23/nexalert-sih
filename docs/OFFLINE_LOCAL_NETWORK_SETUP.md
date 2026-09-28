# NexAlert Offline Local Network Setup

## Overview

NexAlert operates in emergency scenarios where internet connectivity may be unavailable. The system provides a local Wi-Fi network that citizens can connect to for emergency alerts and situational awareness.

**SSID**: `Nexalert_Field_Net_`

## Network Architecture

```
ESP32 Nodes
    ↓ (Local MQTT)
Raspberry Pi
    ├── Local MQTT Broker (mosquitto)
    ├── Local Backend (FastAPI on :8000)
    ├── Local Citizen UI (Vite dev server or static files on :5174)
    └── Wi-Fi Access Point (hostapd)
            ↓
    Citizens' Phones/Devices
```

## Raspberry Pi Configuration

### 1. Install Required Packages

```bash
sudo apt update
sudo apt install -y hostapd dnsmasq iptables-persistent
```

### 2. Configure hostapd (Wi-Fi Access Point)

Create `/etc/hostapd/hostapd.conf`:

```ini
# Interface
interface=wlan0
driver=nl80211

# SSID and Network Configuration
ssid=Nexalert_Field_Net_
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0

# Open network (no password for emergency access)
# In production, consider WPA2 with a well-known password
wpa=0

# Optional: WPA2 configuration (commented out for open access)
# wpa=2
# wpa_passphrase=NexAlert2026
# wpa_key_mgmt=WPA-PSK
# wpa_pairwise=TKIP
# rsn_pairwise=CCMP
```

Enable hostapd:
```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
```

### 3. Configure dnsmasq (DHCP and DNS)

Backup original config:
```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```

Create `/etc/dnsmasq.conf`:

```ini
# Interface to bind to
interface=wlan0

# DHCP range
dhcp-range=192.168.4.10,192.168.4.250,255.255.255.0,24h

# DNS server (point to self for captive portal)
dhcp-option=6,192.168.4.1

# Captive portal detection responses
address=/#/192.168.4.1

# Specific captive portal domains
address=/connectivitycheck.gstatic.com/192.168.4.1
address=/clients3.google.com/192.168.4.1
address=/captive.apple.com/192.168.4.1
address=/www.msftconnecttest.com/192.168.4.1

# Log queries for debugging (disable in production)
log-queries
log-dhcp
```

Enable dnsmasq:
```bash
sudo systemctl enable dnsmasq
```

### 4. Configure Static IP for wlan0

Edit `/etc/dhcpcd.conf` and add:

```ini
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

### 5. Configure IP Forwarding and NAT (if needed)

If the Raspberry Pi has internet access via eth0 and you want to share it:

Enable IP forwarding in `/etc/sysctl.conf`:
```ini
net.ipv4.ip_forward=1
```

Apply:
```bash
sudo sysctl -p
```

Configure iptables NAT:
```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
```

Save iptables rules:
```bash
sudo netfilter-persistent save
```

### 6. Start Services

```bash
sudo systemctl restart dhcpcd
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

Verify:
```bash
sudo systemctl status hostapd
sudo systemctl status dnsmasq
ip addr show wlan0  # Should show 192.168.4.1
```

## Backend Configuration

### Captive Portal Endpoints

The backend (`main.py`) already includes captive portal detection endpoints:

- `/generate_204` - Android captive portal detection
- `/hotspot-detect.html` - iOS captive portal detection
- `/ncsi.txt` - Windows captive portal detection
- `/` - Root redirect to Citizen UI

### WebSocket for Local Realtime Updates

Endpoint: `ws://192.168.4.1:8000/ws/emergency-updates`

The backend includes a WebSocket endpoint at `/ws/emergency-updates` for realtime emergency state updates without requiring internet.

## Citizen UI Configuration

### Environment Configuration

The Citizen UI must support both online and offline modes:

**Online Mode** (with internet):
- Backend: `https://api.nexalert.example.com` or configured URL
- Realtime: Web Push notifications
- Maps: Live OSM tiles from internet

**Offline Local Mode** (no internet, local network):
- Backend: `http://192.168.4.1:8000`
- Realtime: WebSocket at `ws://192.168.4.1:8000/ws/emergency-updates`
- Maps: Cached tiles or vector fallback

### Auto-Detection Strategy

The Citizen UI should detect which mode to use:

1. Try to reach online backend with short timeout (2 seconds)
2. If timeout/failure, try local backend at `http://192.168.4.1:8000`
3. If local backend responds, switch to offline local mode
4. Subscribe to WebSocket for realtime updates

### Serving the Citizen UI Locally

**Option 1: Static Build (Production)**

Build the Citizen UI:
```bash
cd /home/ericsri/NexAlert-Citizen-Safety-UI/artifacts/nexalert-citizen
npm run build
```

Serve via nginx on Raspberry Pi:
```bash
sudo apt install nginx
sudo cp -r dist/* /var/www/html/nexalert/
```

Configure nginx to serve at `http://192.168.4.1:80`

**Option 2: Dev Server (Development)**

Run Vite dev server on Raspberry Pi:
```bash
cd /home/ericsri/NexAlert-Citizen-Safety-UI/artifacts/nexalert-citizen
npm run dev -- --host 0.0.0.0 --port 5174
```

Access at `http://192.168.4.1:5174`

## Captive Portal Behavior

### Expected Flow

1. **Citizen connects to `Nexalert_Field_Net_`**
   - Phone receives DHCP address (192.168.4.10-250)
   - Phone's OS performs captive portal detection

2. **Captive Portal Detection**
   - Android: Requests `http://connectivitycheck.gstatic.com/generate_204`
   - iOS: Requests `http://captive.apple.com/hotspot-detect.html`
   - Windows: Requests `http://www.msftconnecttest.com/ncsi.txt`
   - dnsmasq redirects all domains to 192.168.4.1
   - Backend responds with appropriate captive portal response

3. **Automatic Portal Open**
   - On supported devices/OSes, a captive portal dialog opens automatically
   - The portal shows the Citizen UI served from the Raspberry Pi
   - User sees emergency state, incident map, and realtime updates

4. **Manual Access (if auto-open fails)**
   - User opens browser manually
   - Navigates to any domain (all redirect to 192.168.4.1)
   - Or directly to `http://192.168.4.1:8000` or `http://192.168.4.1:5174`

### Important Notes

- **Web applications cannot force a phone to join Wi-Fi automatically**. The user must manually connect to the `Nexalert_Field_Net_` SSID.
- **Captive portal auto-open** is an OS feature triggered by the captive portal detection mechanism, not by the web application.
- The system can only make the portal open automatically **after** the user has connected to the Wi-Fi network.

## Emergency States

The offline local system supports the same emergency states as the online system:

- **NORMAL** - No active incidents
- **EMERGENCY** - Active incident(s) requiring immediate attention
- **DEGRADED** - System operating with reduced sensor coverage or data quality
- **OFFLINE LOCAL** - Operating without internet, local network only
- **RESOLVED** - Incident resolved, returning to normal

## Testing Offline Mode

### Test Checklist

1. **Network Setup**
   ```bash
   # On Raspberry Pi
   sudo systemctl status hostapd dnsmasq
   ip addr show wlan0  # Verify 192.168.4.1
   ```

2. **Backend Health**
   ```bash
   curl http://192.168.4.1:8000/health
   ```

3. **Captive Portal Endpoints**
   ```bash
   curl http://192.168.4.1:8000/generate_204
   curl http://192.168.4.1:8000/hotspot-detect.html
   curl http://192.168.4.1:8000/ncsi.txt
   ```

4. **WebSocket Connection**
   ```bash
   # Using websocat or similar tool
   websocat ws://192.168.4.1:8000/ws/emergency-updates
   # Should connect and respond to "ping" with "pong"
   ```

5. **Phone Connection**
   - Connect phone to `Nexalert_Field_Net_`
   - Verify captive portal opens automatically (OS-dependent)
   - If not automatic, open browser and navigate to any domain
   - Verify redirect to Citizen UI
   - Verify incident data loads from local backend
   - Verify WebSocket connection for realtime updates

6. **Simulate Internet Outage**
   ```bash
   # Disconnect eth0 on Raspberry Pi
   sudo ip link set eth0 down
   # Verify system continues operating locally
   # Verify Citizen UI switches to offline mode
   # Verify WebSocket updates continue working
   ```

## Offline Map Strategy

### Challenge

OpenStreetMap tiles require internet access. In offline mode, live tile loading will fail.

### Solutions

**Option 1: Cached Tiles (Recommended)**

Pre-cache OSM tiles for the deployment region before going offline:

```javascript
// In Citizen UI, use leaflet-offline or similar
import { TileLayerOffline } from 'leaflet.offline';

const tileLayerOffline = new TileLayerOffline(
  'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  { attribution: '© OpenStreetMap contributors' }
);

// Pre-download tiles for region
// Bounds: deployment area (e.g., 13.0-13.3 lat, 77.4-77.8 lon)
// Zoom levels: 10-16
```

**Option 2: Vector Fallback**

When OSM tiles fail to load, render backend geometry on a plain canvas:

```javascript
// Detect tile load failure
tileLayer.on('tileerror', () => {
  // Switch to vector-only mode
  // Render incident geometry, node locations as SVG/canvas
  // Show simplified map with just emergency data
});
```

**Option 3: Static Base Map**

Include a low-resolution static base map image covering the deployment region:

```javascript
// Use ImageOverlay with pre-rendered map
L.imageOverlay(
  '/assets/base-map-region.png',
  [[13.0, 77.4], [13.3, 77.8]]
).addTo(map);
```

### Backend Geometry (Always Available Offline)

The backend serves incident geometry as GeoJSON via:
- `GET /api/incidents/{incident_id}/geometries`

This geometry is **always available offline** because it comes from the local backend's PostGIS database, not from external APIs.

The Citizen UI should render:
- Incident centroid (marker)
- CURRENT zone (red polygon)
- WARNING zone (orange polygon)
- PROJECTION zone (yellow polygon)
- Node locations (markers)

These render correctly even without OSM tiles.

## Security Considerations

### Open Network

The default configuration uses an **open Wi-Fi network** (no password) for emergency access. This prioritizes citizen safety over network security.

**Rationale**:
- Citizens in emergencies don't have time to ask for passwords
- The network only provides access to local emergency information
- No internet access or sensitive data exposure in pure offline mode

**If WPA2 is required**, use a well-known password and communicate it clearly:
```ini
# In /etc/hostapd/hostapd.conf
wpa=2
wpa_passphrase=NexAlert2026
wpa_key_mgmt=WPA-PSK
```

### Data Privacy

- The local network only exposes emergency state and public incident data
- No personal data or credentials are transmitted over the local network
- Web Push subscriptions remain in the online backend database
- Phone numbers are never transmitted over the local Wi-Fi network

## Troubleshooting

### Captive Portal Not Opening Automatically

**Symptoms**: Phone connects to Wi-Fi but captive portal doesn't open

**Causes**:
- dnsmasq not redirecting captive portal domains
- Backend not responding to captive portal detection URLs
- OS-specific captive portal behavior

**Solutions**:
1. Test captive portal endpoints manually: `curl http://192.168.4.1:8000/generate_204`
2. Check dnsmasq logs: `sudo journalctl -u dnsmasq -f`
3. Verify DNS resolution: `nslookup connectivitycheck.gstatic.com 192.168.4.1`
4. Some Android devices require DNS response, not just IP redirect
5. Instruct users to open browser manually if auto-open fails

### Backend Not Reachable

**Symptoms**: Cannot reach `http://192.168.4.1:8000`

**Solutions**:
1. Verify backend is running: `curl http://127.0.0.1:8000/health`
2. Check backend is bound to `0.0.0.0` not `127.0.0.1`
3. Check firewall: `sudo ufw status` (allow port 8000)
4. Verify wlan0 has IP: `ip addr show wlan0`

### WebSocket Connection Fails

**Symptoms**: Citizen UI cannot connect to `ws://192.168.4.1:8000/ws/emergency-updates`

**Solutions**:
1. Test WebSocket manually: `websocat ws://192.168.4.1:8000/ws/emergency-updates`
2. Check backend logs for WebSocket errors
3. Verify CORS configuration allows WebSocket upgrade
4. Check browser console for connection errors

### No DHCP Address

**Symptoms**: Phone says "No internet" or doesn't get IP address

**Solutions**:
1. Check dnsmasq is running: `sudo systemctl status dnsmasq`
2. Verify DHCP range: `grep dhcp-range /etc/dnsmasq.conf`
3. Check dnsmasq logs: `sudo journalctl -u dnsmasq -f`
4. Restart dnsmasq: `sudo systemctl restart dnsmasq`

## Physical Hardware Validation Status

**IMPLEMENTATION STATUS**: Software configuration complete
**PHYSICAL VALIDATION**: PENDING

The software configuration and integration code is complete. Physical validation requires:

1. Raspberry Pi with Wi-Fi capability (built-in or USB adapter)
2. Actual deployment environment setup
3. Real phone/device testing for captive portal behavior
4. Range and coverage testing for the AP
5. Load testing with multiple concurrent citizens

Physical network setup and testing must be performed in the actual deployment environment.
