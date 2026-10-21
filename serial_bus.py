import serial
import serial.tools.list_ports
#import minimalmodbus
#import time

class SerialManager:

    p_list = {}

    sp = serial.Serial(
        port=None,
        baudrate=19200,     # Prędkość transmisji (częsta dla Modbus)
        bytesize=serial.EIGHTBITS,  # 8 bitów danych
        parity=serial.PARITY_NONE,   # Brak parzystości
        stopbits=serial.STOPBITS_ONE, # 1 bit stopu
        timeout=0.5          # Maksymalny czas oczekiwania na odpowiedź (w sekundach)
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
        if self.sp.port is not None:
            if self.sp.isOpen():
                try:
                    self.sp.close()
                except Exception as e:
                    return False

        # second - set new port
        try:
            self.sp.setPort(port_name)
        except Exception as e:
            return False

        # then - try open new
        if self.sp.isOpen():
            #print(f"Port {port_name} is not available")
            return False
        else:
            try:
                self.sp.open()
                #print(f"Port {port_name} is ready")
                return True
            except Exception as e:
                pass
                #print(f"Port {port_name} is not available")
        return False

    def ser_close(self):
        if self.sp.port is not None:
            if self.sp.isOpen():
                try:
                    self.sp.close()
                    #print(f"Port {self.sp.port} is closed now")
                    return True
                except Exception as e:
                    pass
                    #print(f"Port {self.sp.port} close fail")
        return False
    
