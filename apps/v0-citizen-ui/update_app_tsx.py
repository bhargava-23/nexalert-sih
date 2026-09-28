import re

with open("/home/ericsri/NexAlert-Citizen-Safety-UI/artifacts/nexalert-citizen/src/App.tsx", "r") as f:
    content = f.read()

# Make sure imports are present
if "from '@/lib/offline-ws'" not in content:
    content = content.replace("from '@/lib/backend-api';", "from '@/lib/backend-api';\nimport { offlineWs } from '@/lib/offline-ws';")

# Add Network Status components to context
ctx_type_old = """interface AppContextValue {
  currentEvent: EventRecord;
  refreshEvent: () => Promise<void>;
}"""

ctx_type_new = """export type NetworkState = 'NORMAL' | 'DEGRADED' | 'OFFLINE_LOCAL' | 'EMERGENCY' | 'RESOLVED';

interface AppContextValue {
  currentEvent: EventRecord;
  refreshEvent: () => Promise<void>;
  networkState: NetworkState;
}"""
content = content.replace(ctx_type_old, ctx_type_new)

# Update App component state
app_comp_old = """  const [currentEvent, setCurrentEvent] = useState<EventRecord>(defaultEvent);"""
app_comp_new = """  const [currentEvent, setCurrentEvent] = useState<EventRecord>(defaultEvent);
  const [networkState, setNetworkState] = useState<NetworkState>('NORMAL');"""
content = content.replace(app_comp_old, app_comp_new)

# Update App component useEffect
app_effect_old = """  useEffect(() => {
    fetchEmergency();

    // Refresh every 30 seconds
    const interval = setInterval(fetchEmergency, 30000);

    return () => clearInterval(interval);
  }, []);"""

app_effect_new = """  useEffect(() => {
    fetchEmergency();

    // Connection checker
    const checkConnection = async () => {
      try {
        // Ping our backend root to see if it's reachable locally/remotely
        const res = await fetch(import.meta.env.VITE_API_BASE_URL || 'http://192.168.29.178:8000/', { cache: 'no-store' });
        if (res.ok) {
           if (!navigator.onLine) {
               setNetworkState('OFFLINE_LOCAL');
           } else {
               setNetworkState('NORMAL');
           }
        }
      } catch (e) {
        setNetworkState('DEGRADED');
      }
    };
    checkConnection();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchEmergency();
      checkConnection();
    }, 30000);
    
    // Connect to Offline WS
    offlineWs.connect();
    const unsubscribeWs = offlineWs.subscribe((newEvent) => {
       setCurrentEvent(newEvent);
       setNetworkState('EMERGENCY');
    });

    return () => {
       clearInterval(interval);
       unsubscribeWs();
    };
  }, []);"""
if "offlineWs.connect()" not in content:
    content = content.replace(app_effect_old, app_effect_new)

# Update useMemo
memo_old = """  const value = useMemo(() => ({ currentEvent, refreshEvent }), [currentEvent]);"""
memo_new = """  const value = useMemo(() => ({ currentEvent, refreshEvent, networkState }), [currentEvent, networkState]);"""
content = content.replace(memo_old, memo_new)

with open("/home/ericsri/NexAlert-Citizen-Safety-UI/artifacts/nexalert-citizen/src/App.tsx", "w") as f:
    f.write(content)
