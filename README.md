# RSI Videofied Alarm - Home Assistant Integration

Custom integration for RSI Videofied alarm panels

![](assets/Rsi.png)

## Features

- Native Home Assistant alarm control panel entity (no MQTT required compare to https://github.com/Frifri400-B/rsi-alarm-gateway)
- Arm / Disarm from Home Assistant UI
- Real-time state updates
- Panel connection status binary sensor
- PIN code protection in Home Assistant UI
- Automatic reconnection if panel disconnects

### Exposed sensors

| Sensor | Default state |
|---|---|
| `alarm_alert` | - |
| `alarm_alert_source` | - |
| `alarm_arm` | - |
| `alarm_arm_source` | - |
| `alarm_autoprotection` | - |
| `alarm_autoprotection_source` | -|
| `alarm_ping` | - |
| `alarm_power` | - |

## Installation via HACS

1. In HACS → **Custom repositories** → add this repo URL → category **Integration**
2. Search "RSI Videofied" → Install
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → RSI Videofied Alarm**
5. Fill in the port (default 888) and your PIN code

## Alarm configuration

Refer to your alarm panel [installation guide](documentations/)

## Configuration

| Field | Description | Default |
|---|---|---|
| Device name | Name shown in HA | RSI Videofied Alarm |
| Port | TCP port the panel connects to | 888 |
| Alarm PIN | Code required in HA UI to arm/disarm | N/A |

## How it works

The integration starts a TCP server that the RSI panel connects to (same protocol as the Frontel monitoring software). It implements the full RSI authentication handshake and sends a STATUS heartbeat every 60 seconds to keep the connection alive.

### States

| HA State | Meaning |
|---|---|
| `disarmed` | Panel disarmed |
| `arming` | Arm command sent, waiting for panel confirmation |
| `armed_away` | Panel armed (confirmed by EVENT 24) |
| `triggered` | Intrusion / tamper / panic detected |

### Panel event mapping

| Panel event | HA state |
|---|---|
| EVENT,24 | armed_away |
| EVENT,25 | disarmed |
| EVENT,1 / 3 / 5 / 29 / 32 / 34 | triggered |

## Requirements

- `pycryptodome >= 3.9.0` (installed automatically)
- The RSI panel must be configured to connect to your Home Assistant server IP on port 888
- [Hacs](https://www.hacs.xyz/)

## Credits

This project is inspired by [rsi-alarm-gateway](https://github.com/Mickaelh51/rsi-alarm-gateway) by [@Mickaelh51](https://github.com/Mickaelh51). The original project provided the       foundation for the RSI Videofied protocol implementation.