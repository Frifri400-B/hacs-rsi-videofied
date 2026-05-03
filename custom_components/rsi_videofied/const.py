DOMAIN = "rsi_videofied"

CONF_PORT        = "port"
CONF_ALARM_CODE  = "alarm_code"
CONF_ALARM_NAME  = "alarm_name"

DEFAULT_PORT       = 888
DEFAULT_ALARM_NAME = "RSI Videofied Alarm"

STATE_DISARMED    = "disarmed"
STATE_ARMING      = "arming"
STATE_ARMED_AWAY  = "armed_away"
STATE_ARMED_HOME  = "armed_home"
STATE_ARMED_NIGHT = "armed_night"
STATE_TRIGGERED   = "triggered"

CMD_ARM    = "ARMING,1"
CMD_DISARM = "ARMING,0"
CMD_STATUS = "STATUS"

EVENT_INTRUSION     = "1"
EVENT_TAMPER        = "3"
EVENT_PANIC         = "5"
EVENT_ARMED         = "24"
EVENT_DISARMED      = "25"
EVENT_ALARM_TEST    = "29"
EVENT_PANIC_SMOKE   = "32"
EVENT_PANIC_MEDICAL = "34"

UNKNOWN_SOURCE = "Nothing"

ALARM_SENSORS = [
    {"key": "alarm_arm",                  "name": "Arm State",              "device_class": "lock",         "entity_type": "binary_sensor"},
    {"key": "alarm_arm_source",           "name": "Arm Source",             "device_class": None,           "entity_type": "sensor"},
    {"key": "alarm_power",                "name": "Power",                  "device_class": "plug",         "entity_type": "binary_sensor"},
    {"key": "alarm_autoprotection",       "name": "Autoprotection",         "device_class": "safety",       "entity_type": "binary_sensor"},
    {"key": "alarm_autoprotection_source","name": "Autoprotection Source",  "device_class": None,           "entity_type": "sensor"},
    {"key": "alarm_alert",                "name": "Alert",                  "device_class": "problem",      "entity_type": "binary_sensor"},
    {"key": "alarm_alert_source",         "name": "Alert Source",           "device_class": None,           "entity_type": "sensor"},
    {"key": "alarm_ping",                 "name": "Ping",                   "device_class": None,           "entity_type": "sensor"},
]

PANEL_SENSORS = [
    {"key": "panel_serial",           "name": "Serial Number",        "icon": "mdi:identifier"},
    {"key": "panel_last_connection",  "name": "Last Connection",      "icon": "mdi:lan-connect",   "device_class": "timestamp"},
    {"key": "panel_uptime",           "name": "Uptime",               "icon": "mdi:timer-outline", "device_class": "duration", "unit": "s"},
    {"key": "panel_firmware",         "name": "Firmware Version",     "icon": "mdi:chip"},
]

CONNECTIVITY_SENSOR = {"key": "panel_connected", "name": "Panel Connected", "device_class": "connectivity"}
