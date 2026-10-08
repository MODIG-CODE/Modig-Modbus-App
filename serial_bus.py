import serial
import serial.tools.list_ports
import time

class SerialManager:

    p_list = {}

    def list_get(self):
        self.p_list = serial.tools.list_ports.comports()

        if not self.p_list:
            print("Not find COMs...")
        else:
            for port in self.p_list:
                print(f">>> {port.device} {port.description}")  # np. "COM3"
                #print(f"Opis: {port.description}")  # np. "USB-SERIAL CH340 (COM3)"
                #print("-" * 20)
