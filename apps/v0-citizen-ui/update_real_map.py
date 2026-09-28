import re

with open("/home/ericsri/NexAlert-Citizen-Safety-UI/artifacts/nexalert-citizen/src/components/real-map.tsx", "r") as f:
    content = f.read()

# Add logic to hide TileLayer and show a placeholder base geometry if offline
# Or just catch tile failures, but an easy way is network state
imports = "import { MapContainer, TileLayer, Marker, Popup, useMap, GeoJSON } from 'react-leaflet';"
content = content.replace("import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';", imports)

# We will need the incident geometries!
data_layer_old = """      {/* Leaflet Map - always renders */}
      <MapContainer
        center={userLocation ? [userLocation.lat, userLocation.lon] : defaultCenter}
        zoom={userLocation ? 13 : 5}
        className="h-full w-full"
        style={{ minHeight: '280px' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />"""
data_layer_new = """      {/* Leaflet Map - always renders */}
      <MapContainer
        center={userLocation ? [userLocation.lat, userLocation.lon] : defaultCenter}
        zoom={userLocation ? 13 : 5}
        className="h-full w-full"
        style={{ minHeight: '280px', background: !navigator.onLine ? '#e3f1ec' : undefined }}
        zoomControl={false}
      >
        {/* Offline local fallback for base map */}
        {!navigator.onLine && (
           <div className="absolute inset-0 z-0 flex items-center justify-center opacity-30 pointer-events-none">
              <span className="font-mono text-4xl text-[#195d52]">OFFLINE LOCAL MAP</span>
           </div>
        )}
        {navigator.onLine && (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        )}"""
if "OFFLINE LOCAL MAP" not in content:
    content = content.replace(data_layer_old, data_layer_new)

with open("/home/ericsri/NexAlert-Citizen-Safety-UI/artifacts/nexalert-citizen/src/components/real-map.tsx", "w") as f:
    f.write(content)
