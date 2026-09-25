"""
Rice Lake 720i - Serial Reader
الإعدادات: 2400 / 7 bits / Odd parity / 1 stop bit
الميزان بيبعت تلقائياً: 90KGM\r\n
"""
import serial
import threading
import time
import re

BAUD_RATE = 9600
DATA_BITS = 7
PARITY    = 'O'
STOP_BITS = 1
PORT      = 'COM3'


class ScaleReader:
    def __init__(self):
        self._ser           = None
        self._thread        = None
        self._running       = False
        self._lock          = threading.Lock()
        self.current_weight = 0.0
        self.is_connected   = False
        self.last_error     = ''
        self.last_hex       = ''   # ← آخر HEX مستقبل للـ debug
        self.port           = PORT

    def connect(self, port=None):
        if port:
            self.port = port
        try:
            self.disconnect()
            self._ser = serial.Serial(
                port     = self.port,
                baudrate = BAUD_RATE,
                bytesize = DATA_BITS,
                parity   = serial.PARITY_ODD,
                stopbits = serial.STOPBITS_ONE,
                timeout  = 1,
            )
            self._ser.reset_input_buffer()
            self._running    = True
            self.is_connected = True
            self.last_error   = ''
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            print(f"✅ Connected to {self.port}")
            return True
        except Exception as e:
            self.last_error   = str(e)
            self.is_connected = False
            print(f"[X] Connect error: {e}")
            return False

    def disconnect(self):
        self._running = False
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except:
                pass
        self._ser         = None
        self.is_connected = False

    def _read_loop(self):
        buf = b''
        while self._running:
            try:
                if self._ser and self._ser.is_open and self._ser.in_waiting > 0:
                    raw = self._ser.read(self._ser.in_waiting)

                    # احفظ الـ HEX للـ debug
                    with self._lock:
                        self.last_hex = ' '.join(f'{b:02X}' for b in raw)

                    buf += raw

                    # ابحث عن نهاية السطر
                    while b'\r' in buf or b'\n' in buf:
                        idx = -1
                        for i, b in enumerate(buf):
                            if b in (0x0D, 0x0A):
                                idx = i
                                break
                        if idx < 0:
                            break

                        line_bytes = buf[:idx]
                        buf = buf[idx+1:].lstrip(b'\r\n')

                        if line_bytes:
                            line = line_bytes.decode('ascii', errors='replace').strip()
                            if line:
                                weight = self._parse_line(line)
                                if weight is not None:
                                    with self._lock:
                                        self.current_weight = weight
                else:
                    time.sleep(0.01)

            except serial.SerialException as e:
                self.is_connected = False
                self.last_error   = str(e)
                print(f"[X] Serial error: {e}")
                time.sleep(3)
                self.connect(self.port)
                buf = b''
            except Exception as e:
                print(f"[X] Read error: {e}")
                time.sleep(0.1)
                buf = b''

    def _parse_line(self, line):
        """
        استخرج الوزن من السطر
        مثلاً: '90KGM' → 90.0 | '  6400 KG' → 6400.0
        """
        m = re.search(r'([+\-]?\s*\d+\.?\d*)', line)
        if m:
            try:
                w = float(m.group(1).replace(' ', ''))
                if w < 0:
                    w = 0
                print(f"⚖️ Weight: {w} kg  ← '{line}'")
                return w
            except:
                pass
        return None

    def get_weight(self):
        with self._lock:
            return self.current_weight


# Singleton
scale = ScaleReader()
