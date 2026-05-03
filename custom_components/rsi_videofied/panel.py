# coding: utf-8
import logging
import socket
import threading

from Crypto.Cipher import AES
from Crypto import Random
import codecs

_LOGGER = logging.getLogger(__name__)
decode_hex = codecs.getdecoder("hex_codec")

_recv_buffers: dict = {}


def recv_message(conn):
    key = id(conn)
    if key not in _recv_buffers:
        _recv_buffers[key] = b""
    while b'\x1a' not in _recv_buffers[key]:
        try:
            chunk = conn.recv(4096)
        except socket.timeout:
            raise
        if not chunk:
            _recv_buffers.pop(key, None)
            raise ConnectionError("Connection closed by peer")
        _recv_buffers[key] += chunk
    idx = _recv_buffers[key].index(b'\x1a')
    msg = _recv_buffers[key][:idx].decode(errors='replace')
    _recv_buffers[key] = _recv_buffers[key][idx + 1:]
    return msg


def clear_recv_buffer(conn):
    _recv_buffers.pop(id(conn), None)


def generate_preshared_key(serial: str) -> str:
    return (
        serial[4] + '0' + serial[15] + serial[11] + '0' + serial[5] +
        serial[13] + serial[6] + serial[8] + serial[12] + serial[7] +
        serial[14] + '1' + '0' + serial[10] + serial[9] + serial[7] +
        serial[10] + serial[4] + serial[15] + serial[13] + serial[6] +
        serial[12] + '0' + serial[8] + '0' + serial[14] + '1' +
        serial[11] + serial[11] + '0' + serial[5]
    )


def get_challenge_response(key: str, challenge: str) -> str:
    cipher = AES.new(decode_hex(key)[0], AES.MODE_ECB)
    return cipher.encrypt(decode_hex(challenge)[0]).hex().upper()


def delete_x1a(s: str) -> str:
    return s[:-1] if s.endswith('\x1a') else s


class RSIPanel:
    def __init__(self, host: str, port: int, on_state_change, on_sensor_change, on_connected, on_disconnected):
        self._host = host
        self._port = port
        self._on_state_change  = on_state_change
        self._on_sensor_change = on_sensor_change
        self._on_connected     = on_connected
        self._on_disconnected  = on_disconnected

        self._server_sock: socket.socket | None = None
        self._conn:        socket.socket | None = None
        self._lock = threading.Lock()
        self._authenticated = False
        self._stop = threading.Event()
        self._heartbeat_stop = threading.Event()


    def start(self):
        t = threading.Thread(target=self._serve, daemon=True, name="rsi_panel_server")
        t.start()

    def stop(self):
        self._stop.set()
        self._heartbeat_stop.set()
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

    def arm(self) -> bool:
        return self._send("ARMING,1")

    def disarm(self) -> bool:
        return self._send("ARMING,0")

    @property
    def connected(self) -> bool:
        return self._conn is not None and self._authenticated


    def _serve(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._server_sock.bind((self._host, self._port))
        except OSError as e:
            _LOGGER.error("RSI: cannot bind to %s:%s — %s", self._host, self._port, e)
            return

        self._server_sock.listen(1)
        _LOGGER.info("RSI: listening on %s:%s", self._host, self._port)

        while not self._stop.is_set():
            try:
                self._server_sock.settimeout(2)
                conn, addr = self._server_sock.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            _LOGGER.info("RSI: panel connected from %s:%s", addr[0], addr[1])
            self._handle_connection(conn)

    def _handle_connection(self, conn: socket.socket):
        conn.settimeout(10)
        serial, key, firmware = self._authenticate(conn)
        if not serial:
            _LOGGER.warning("RSI: authentication failed")
            conn.close()
            return

        with self._lock:
            self._conn = conn
            self._authenticated = True

        self._on_connected(serial, firmware)

        self._heartbeat_stop.clear()
        hb = threading.Thread(target=self._heartbeat, daemon=True, name="rsi_heartbeat")
        hb.start()

        while not self._stop.is_set():
            try:
                msg = recv_message(conn)
            except socket.timeout:
                continue
            except Exception:
                _LOGGER.info("RSI: panel disconnected")
                break

            _LOGGER.debug("RSI ← %s", msg)
            self._dispatch(msg, conn)

        self._heartbeat_stop.set()
        with self._lock:
            self._conn = None
            self._authenticated = False
        clear_recv_buffer(conn)
        conn.close()
        self._on_disconnected()


    def _authenticate(self, conn):
        try:
            conn.send(b"IDENT,1000\x1a")
            raw = recv_message(conn)
            parts = raw.split(',')
            if parts[0] != 'IDENT' or len(parts) < 2:
                return None, None

            serial = parts[1]
            key = generate_preshared_key(serial)
            _LOGGER.info("RSI: serial=%s", serial)

            conn.send(('SETKEY,' + key + '\x1a').encode())
            conn.send(b"VERSION,2,0\x1a")

            challenge = Random.new().read(16).hex().upper()
            conn.send(('AUTH1,' + challenge + '\x1a').encode())

            raw = recv_message(conn)
            parts = raw.split(',')
            if parts[0] != 'AUTH2' or len(parts) < 3:
                return None, None

            panel_challenge = delete_x1a(parts[2])
            response = get_challenge_response(key, panel_challenge)
            conn.send(('AUTH3,' + response + '\x1a').encode())

            raw = recv_message(conn)
            if 'AUTH_SUCCESS' in raw:
                parts_auth = raw.split(',')
                firmware = parts_auth[5] if len(parts_auth) > 5 else None
                _LOGGER.info("RSI: authenticated (serial=%s firmware=%s)", serial, firmware)
                return serial, key, firmware

        except Exception as e:
            _LOGGER.error("RSI: auth error — %s", e)
        return None, None, None


    def _dispatch(self, message: str, conn: socket.socket):
        parts = message.split(',') if ',' in message else [message]
        mtype = parts[0]
        data  = parts[1:]

        if mtype == "ALARM":
            conn.send(b"ALARM_ACK\x1a")

        elif mtype == "LOG":
            conn.send(b"LOG_ACK\x1a")

        elif mtype == "FILE":
            try:
                file_msg = recv_message(conn)
                if 'FileVersion' in file_msg:
                    conn.send(b"FILE_ACK\x1a")
            except Exception:
                pass

        elif mtype == "REQACK":
            conn.send(b"ACK\x1a")

        elif mtype == "ARMING":
            _LOGGER.debug("RSI: ARMING confirmation %s", data)

        elif mtype == "EVENT":
            self._handle_event(data)

        elif mtype.startswith("OUTPUT"):
            _LOGGER.debug("RSI: OUTPUT data (ignored)")

        else:
            _LOGGER.debug("RSI: unknown message type '%s'", mtype)


    def _handle_event(self, event_data: list):
        from .const import (
            EVENT_INTRUSION, EVENT_TAMPER, EVENT_PANIC,
            EVENT_ARMED, EVENT_DISARMED, EVENT_ALARM_TEST,
            EVENT_PANIC_SMOKE, EVENT_PANIC_MEDICAL,
            STATE_ARMED_AWAY, STATE_DISARMED, STATE_TRIGGERED,
        )
        code = event_data[0] if event_data else "unknown"
        _LOGGER.info("RSI: event code=%s data=%s", code, event_data)

        state_map = {
            EVENT_INTRUSION:     STATE_TRIGGERED,
            EVENT_TAMPER:        STATE_TRIGGERED,
            EVENT_PANIC:         STATE_TRIGGERED,
            EVENT_PANIC_SMOKE:   STATE_TRIGGERED,
            EVENT_PANIC_MEDICAL: STATE_TRIGGERED,
            EVENT_ALARM_TEST:    STATE_TRIGGERED,
            EVENT_ARMED:         STATE_ARMED_AWAY,
            EVENT_DISARMED:      STATE_DISARMED,
        }
        new_state = state_map.get(code)
        if new_state:
            _LOGGER.info("RSI: state → %s", new_state)
            self._on_state_change(new_state)

        source = event_data[1] if len(event_data) > 1 else None
        badge  = event_data[2] if len(event_data) > 2 else None

        if code == EVENT_ARMED:
            self._on_sensor_change("alarm_arm", "ON")
            self._on_sensor_change("alarm_arm_source", badge or source or "Nothing")
        elif code == EVENT_DISARMED:
            self._on_sensor_change("alarm_arm", "OFF")
            self._on_sensor_change("alarm_arm_source", badge or source or "Nothing")
        elif code == EVENT_INTRUSION:
            self._on_sensor_change("alarm_alert", "ON")
            self._on_sensor_change("alarm_alert_source", source or "Nothing")
        elif code == EVENT_TAMPER:
            self._on_sensor_change("alarm_autoprotection", "ON")
            self._on_sensor_change("alarm_autoprotection_source", source or "Nothing")
        elif code in ("4",):
            self._on_sensor_change("alarm_autoprotection", "OFF")
            self._on_sensor_change("alarm_autoprotection_source", "Nothing")
        elif code == "19":
            self._on_sensor_change("alarm_power", "OFF")
        elif code == "20":
            self._on_sensor_change("alarm_power", "ON")
        elif code == "26":
            self._on_sensor_change("alarm_ping", "pong")
        elif code == "27":
            self._on_sensor_change("alarm_alert", "OFF")
            self._on_sensor_change("alarm_alert_source", "Nothing")


    def _heartbeat(self):
        while not self._heartbeat_stop.wait(60):
            _LOGGER.debug("RSI: heartbeat STATUS")
            self._send("STATUS")


    def _send(self, msg: str) -> bool:
        with self._lock:
            if not self._conn or not self._authenticated:
                _LOGGER.warning("RSI: panel not connected, cannot send '%s'", msg)
                return False
            try:
                self._conn.send((msg + '\x1a').encode())
                _LOGGER.debug("RSI → %s", msg)
                return True
            except Exception as e:
                _LOGGER.error("RSI: send error — %s", e)
                return False