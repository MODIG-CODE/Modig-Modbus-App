import serial
import serial.tools.list_ports
import time
import minimalmodbus

class SerialManager:

    p_list = {}

    ser = serial.Serial(
        port=None,
        baudrate=19200,     # Prędkość transmisji (częsta dla Modbus)
        bytesize=serial.EIGHTBITS,  # 8 bitów danych
        parity=serial.PARITY_NONE,   # Brak parzystości
        stopbits=serial.STOPBITS_ONE, # 1 bit stopu
        timeout=1          # Maksymalny czas oczekiwania na odpowiedź (w sekundach)
    )

    #mm = minimalmodbus.Instrument(ser, 1)

    def list_get(self):
        self.p_list = serial.tools.list_ports.comports()

        if self.p_list:
            for port in self.p_list:
                print(f">>> {port.device} {port.description}")  # np. "COM3"
                #print(f"Opis: {port.description}")  # np. "USB-SERIAL CH340 (COM3)"
                #print("-" * 20)
            return True
        return False

    def try_open(self, port_name):
        # first - close actual, if need
        if self.ser.port is not None:
            if self.ser.isOpen():
                try:
                    self.ser.close()
                except Exception as e:
                    return False

        # second - set new port
        try:
            self.ser.setPort(port_name)
        except Exception as e:
            return False

        # then - try open new
        if self.ser.isOpen():
            #print(f"Port {port_name} is not available")
            return False
        else:
            try:
                self.ser.open()
                self.mm = minimalmodbus.Instrument(self.ser, 1)
                #print(f"Port {port_name} is ready")
                return True
            except Exception as e:
                pass
                #print(f"Port {port_name} is not available")
        return False

    def ser_close(self):
        if self.ser.port is not None:
            if self.ser.isOpen():
                try:
                    self.ser.close()
                    #print(f"Port {self.ser.port} is closed now")
                    return True
                except Exception as e:
                    pass
                    #print(f"Port {self.ser.port} close fail")
        return False

    def mm_wr_bit(self, adr, val):
        if self.ser.isOpen():
            try:
                self.mm.write_bit(adr, val)
                return True
            except Exception as e:
                pass
        return False
