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

SENSOR_DEFINITIONS = [
    {"key": "panel_connected", "name": "Panel Connected",      "device_class": "connectivity", "entity_type": "binary_sensor"},
]
