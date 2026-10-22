import threading
import time
import minimalmodbus
from dataclasses import dataclass
from queue import Queue

@dataclass
class ModbusCommand:
    action: str
    adr: int
    reg: int
    val: int

class ModbusFunctions:
    def __init__(self, app_ref):
        self.command_event = threading.Event()
        self.functions_event = threading.Event()
        self.functions_thread = threading.Thread(target=self.functions_loop, daemon=True)
        self.main_ref = app_ref
        self.mcom = ModbusCommand
        self.c_queue = Queue(maxsize=5)

    def start_functions(self, serial_port):
        """Uruchamia wątek odpytywania, jeśli nie jest jeszcze aktywny."""
        if self.functions_thread is None or not self.functions_thread.is_alive():
            self.functions_thread = threading.Thread(target=self.functions_loop, daemon=True)

        try:
            self.mm = minimalmodbus.Instrument(serial_port, 1)
            self.functions_event.set()
            self.functions_thread.start()
            print("Thread RUN")
            return True

        except Exception as e:
            print(f"[Modbus Functions Error]: {e}")
            #self.functions_event.clear()
            self.functions_close()

    def functions_loop(self):
        """Pętla wykonująca się w tle (w osobnym wątku)."""
        rdelay = 0
        wdelay = 0
        while self.functions_event.is_set():
            time.sleep(0.1)
            if self.mm.serial.is_open:
                if wdelay < 3: wdelay += 1

                if not self.c_queue.empty():
                    rdelay = 0
                    if not wdelay < 3:
                        wdelay = 0
                        self.mcom = self.c_queue.get(block=False)
                        self.mm.address = self.mcom.adr
                        try:
                            if self.mcom.action == "wrb":
                                self.mm.write_bit(
                                    registeraddress=self.mcom.reg,
                                    value=self.mcom.val,
                                    functioncode=5)
                                #time.sleep(0.1)
                                self.main_ref.after(0, self.main_ref.outputs_switch_state, (self.mcom.reg, self.mcom.val))

                            elif self.mcom.action == "rdb":
                                in_states = self.mm.read_bits(
                                    registeraddress=self.mcom.reg,
                                    number_of_bits=self.mcom.val,
                                    functioncode=1
                                )
                                #time.sleep(0.1)
                                for i in range(16 - len(in_states)):
                                    in_states.append(0)

                                new_states = in_states[8:] + in_states[:8]
                                self.main_ref.after(0, self.main_ref.outputs_all_switch_state, new_states)

                        except Exception as e:
                            print(f"[Functions Error]: {e}")
                else :
                    if rdelay < 4:
                        rdelay += 1
                    else :
                        rdelay = 0
                        wdelay = 2
                        try:
                            inputs = self.main_ref.module.inputs

                            if inputs > 0:
                                if inputs < 16: inputs = 16
                                self.mm.address = self.main_ref.module.adr
                                # Funkcja zwraca listę wartości, np. [0, 1, 0, 0]
                                in_states = self.mm.read_bits(
                                    registeraddress=self.main_ref.module.offset,
                                    number_of_bits=inputs,
                                    functioncode=2
                                )
                                new_states = in_states[8:] + in_states[:8]
                                #time.sleep(0.1)
                                self.main_ref.after(0, self.main_ref.input_indicators, new_states)
                        except Exception as e:
                            print(f"[Thread Func Error]: {e}")

    def functions_close(self):
        self.command_event.clear()
        self.functions_event.clear()
        if self.functions_thread and self.functions_thread.is_alive():
            self.functions_thread.join(timeout=1.0) # Czekamy maksymalnie sekundę na zamknięcie wątku

    def functions_command(self, com):
        try:
            self.c_queue.put(com, block=False)
        except Exception as e:
            print(f"Kolejka komend pełna")

