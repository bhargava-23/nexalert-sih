#!/bin/bash
# NexAlert Raspberry Pi Setup Script
# Installs Mosquitto MQTT broker and Python dependencies

set -e

echo "=== NexAlert Raspberry Pi Setup ==="
echo "Track A: Hardware Vertical Slice - Milestone 1"
echo ""

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install Mosquitto MQTT broker
echo "Installing Mosquitto MQTT broker..."
sudo apt-get install -y mosquitto mosquitto-clients

# Enable and start Mosquitto
echo "Enabling Mosquitto service..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Verify installations
echo ""
echo "=== Verification ==="
mosquitto -h | head -n 1
python3 -c "import paho.mqtt.client as mqtt; print(f'paho-mqtt: {mqtt.__version__}')"
python3 -c "import jsonschema; print(f'jsonschema: {jsonschema.__version__}')"

echo ""
echo "=== Setup Complete ==="
echo "Mosquitto broker running on localhost:1883"
echo "To start subscriber: python3 pi_mqtt_subscriber.py"
