# NexAlert ESP32-S3 Firmware Build Instructions

**Status**: Firmware is **build-ready** — all code complete, awaiting ESP-IDF toolchain

---

## Prerequisites

### 1. ESP-IDF Installation Required

**Target Hardware**: ESP32-S3  
**Expected ESP-IDF Version**: **5.1.x or later** (ESP32-S3 support)

**ESP-IDF is NOT currently installed on this machine.**

---

## Installation Steps (One-Time Setup)

### Windows Installation

1. **Download ESP-IDF 5.1.x or later**:
   ```
   https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/windows-setup.html
   ```

2. **Run the ESP-IDF installer** (recommended method):
   - Download: `https://dl.espressif.com/dl/esp-idf/`
   - Install to: `C:\esp-idf` (default) or custom location
   - Installer will set up Python environment and toolchains automatically

3. **Verify installation**:
   ```powershell
   # Open "ESP-IDF PowerShell" from Start Menu
   idf.py --version
   ```

4. **Expected output**:
   ```
   ESP-IDF v5.1.x
   ```

---

## Build Commands

### Method 1: Using ESP-IDF PowerShell (Recommended)

1. **Launch ESP-IDF PowerShell** from Windows Start Menu

2. **Navigate to firmware directory**:
   ```powershell
   cd C:\projects\nexalert-sih\firmware
   ```

3. **Set target** (first time only):
   ```powershell
   idf.py set-target esp32s3
   ```

4. **Build firmware**:
   ```powershell
   idf.py build
   ```

5. **Flash to device** (ESP32-S3 connected via USB):
   ```powershell
   idf.py -p COM3 flash monitor
   ```
   Replace `COM3` with actual COM port (check Device Manager)

---

### Method 2: Using Regular PowerShell/CMD

1. **Activate ESP-IDF environment** (adjust path if installed elsewhere):
   ```powershell
   C:\esp-idf\export.ps1
   ```
   Or for CMD:
   ```cmd
   C:\esp-idf\export.bat
   ```

2. **Navigate to firmware directory**:
   ```powershell
   cd C:\projects\nexalert-sih\firmware
   ```

3. **Follow build steps 3-5 from Method 1**

---

## Repository Configuration

### Target Configuration (Verified)

File: `firmware/sdkconfig.defaults`

```ini
CONFIG_IDF_TARGET="esp32s3"
CONFIG_ESPTOOLPY_FLASHSIZE_8MB=y
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.csv"
```

### Hardware Configuration (Track 3A)

**Sensors** (I2C bus: GPIO8 SDA, GPIO9 SCL):
- BME680 environmental sensor (I2C address 0x77/0x76)
  - Temperature, humidity, pressure, gas resistance
- MPU6050 accelerometer (I2C address 0x68)
  - Vibration detection (m/s²)
- MQ-2 gas sensor (ADC GPIO4)
  - Raw ADC reading (0-4095)

**Network Configuration** (Locked):
- WiFi SSID: `NexAlert_Field_Net`
- MQTT Broker: `10.42.0.1:1883`
- MQTT Topic: `Nexalert/telemetry/node1`
- NTP Server: `10.42.0.1`
- Node ID: `NODE-001`

---

## Expected Build Output

### Successful Build

```
Project build complete. To flash, run:
 idf.py -p (PORT) flash
or
 idf.py -p (PORT) flash monitor (to flash and monitor)

Binary output:
 - firmware/build/nexalert-esp32s3.bin
 - firmware/build/bootloader/bootloader.bin
 - firmware/build/partition_table/partition-table.bin
```

### Build Artifacts Location

```
firmware/build/
├── nexalert-esp32s3.bin          # Main firmware binary
├── nexalert-esp32s3.elf          # ELF file with debug symbols
├── bootloader/
│   └── bootloader.bin
├── partition_table/
│   └── partition-table.bin
└── compile_commands.json         # For IDE integration
```

---

## Common Build Issues & Fixes

### Issue 1: Missing Python Dependencies

**Symptom**:
```
ModuleNotFoundError: No module named 'click'
```

**Fix**:
```powershell
python -m pip install --user -r $IDF_PATH/requirements.txt
```

---

### Issue 2: Incorrect ESP-IDF Version

**Symptom**:
```
CMake Error: CONFIG_IDF_TARGET is set to 'esp32s3' but CMake is being run for 'esp32'
```

**Fix**:
```powershell
idf.py set-target esp32s3
idf.py fullclean
idf.py build
```

---

### Issue 3: USB Driver Issues (Windows)

**Symptom**:
```
Could not open port 'COM3': PermissionError
```

**Fix**:
1. Install CP210x USB-to-UART driver:
   ```
   https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
   ```
2. Check Device Manager → Ports (COM & LPT)
3. Use correct COM port in flash command

---

## Firmware Flash Commands

### Full Flash (First Time)

```powershell
idf.py -p COM3 erase-flash
idf.py -p COM3 flash
```

### Flash + Monitor (Recommended)

```powershell
idf.py -p COM3 flash monitor
```

Exit monitor: `Ctrl+]`

### Flash Specific Partition

```powershell
idf.py -p COM3 app-flash    # Application only
```

---

## Serial Monitor Commands

### View Live Logs

```powershell
idf.py -p COM3 monitor
```

### Expected Boot Output

```
I (318) cpu_start: Starting scheduler on CPU0
I (323) cpu_start: Starting scheduler on CPU1
I (323) main: NexAlert ESP32-S3 Node Starting...
I (333) node_config: Node ID: NODE-001
I (343) wifi_station: Connecting to WiFi SSID: NexAlert_Field_Net
I (2453) wifi_station: WiFi connected, IP: 10.42.0.xxx
I (2463) sntp_client: SNTP client initialized with server: 10.42.0.1
I (12473) sntp_client: SNTP synchronized: 2026-09-16 15:31:23 UTC
I (12483) mqtt_client: Connecting to broker: 10.42.0.1:1883
I (12593) mqtt_client: Connected to MQTT broker
I (12603) main: Publishing to topic: Nexalert/telemetry/node1
```

---

## Track 3A Implementation Status

### ✅ COMPLETE

- **Hardware JSON serializer** (`components/telemetry/hardware_json.c`)
  - Exact locked contract from recovered Arduino
  - NAN → JSON null serialization
  - Availability flags derived from sensor readings
  
- **Sensor drivers**:
  - BME680 driver (`components/sensors/bme680.c`)
  - MPU6050 driver (`components/sensors/mpu6050.c`)
  - MQ-2 driver (`components/sensors/mq2.c`)
  - I2C bus manager (`components/sensors/i2c_bus.c`)

- **SNTP/NTP client** (`components/network/sntp_client.c`)
  - Locked NTP server: 10.42.0.1
  - Wall-clock sync with uptime fallback

- **Main integration** (`main/main.c`)
  - Sensor acquisition loop
  - Hardware JSON generation
  - MQTT publishing
  - SNTP initialization

### ❌ BLOCKED

- **Firmware build** — ESP-IDF toolchain not installed
- **Hardware testing** — Requires ESP32-S3 device with sensors

---

## Next Steps

1. **Install ESP-IDF 5.1.x** following Windows installation guide
2. **Build firmware**: `idf.py build`
3. **Fix compilation errors** (if any)
4. **Flash to ESP32-S3 device**
5. **Verify runtime behavior**:
   - I2C sensor initialization
   - BME680/MPU6050/MQ-2 readings
   - SNTP synchronization with 10.42.0.1
   - MQTT publishing to Nexalert/telemetry/node1
   - Hardware JSON structure matches locked contract

---

## References

- **ESP-IDF Documentation**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/
- **Track 3A Final Report**: `firmware/TRACK_3A_FINAL_REPORT.md`
- **Hardware JSON Architecture**: `firmware/TRACK_3A_HARDWARE_JSON_ARCHITECTURE.md`
- **Locked Hardware JSON Contract**: See `TRACK_3A_FINAL_REPORT.md` Section "Hardware JSON Verification Result"

---

**END OF BUILD INSTRUCTIONS**
