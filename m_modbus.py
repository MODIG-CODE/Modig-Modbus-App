import threading
import time
from dataclasses import dataclass

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
        self.functions_thread = None  # Referencja do wątku
        self.main_ref = app_ref
        self.mcom = ModbusCommand

    def start_functions(self, bus_ref):
        """Uruchamia wątek odpytywania, jeśli nie jest jeszcze aktywny."""
        self.bus = bus_ref
        if self.functions_thread is None or not self.functions_thread.is_alive():
            self.functions_event.set()
            self.functions_thread = threading.Thread(target=self.functions_loop, daemon=True)
            self.functions_thread.start()
            print("Thread RUN")

    def functions_loop(self):
        """Pętla wykonująca się w tle (w osobnym wątku)."""
        delay = 0
        while self.functions_event.is_set():
            time.sleep(0.1)
            if hasattr(self.main_ref, 'app_bus_status') and self.main_ref.app_bus_status is not False:

                if self.command_event.is_set():
                    delay = 0
                    try:
                        if self.mcom.action == "wrb":
                            self.bus.mm.write_bit(self.mcom.reg, self.mcom.val)
                            #time.sleep(0.1)
                            self.main_ref.after(0, self.main_ref.outputs_switch_state, (self.mcom.reg, self.mcom.val))

                        self.command_event.clear()
                    except Exception as e:
                        print(f"[Functions Error]: {e}")
                else :
                    delay += 1
                    if delay == 4:
                        delay = 0
                        try:
                            inputs = self.main_ref.module.inputs

                            if inputs > 0:
                                # Funkcja zwraca listę wartości, np. [0, 1, 0, 0]
                                in_states = self.bus.mm.read_bits(
                                    registeraddress=1,
                                    number_of_bits=inputs,
                                    functioncode=2
                                )
                                #time.sleep(0.1)
                                self.main_ref.after(0, self.main_ref.input_indicators, in_states)
                        except Exception as e:
                            print(f"[Thread Func Error]: {e}")

    def functions_close(self):
        self.command_event.clear()
        self.functions_event.clear()
        if self.functions_thread and self.functions_thread.is_alive():
            self.functions_thread.join(timeout=1.0) # Czekamy maksymalnie sekundę na zamknięcie wątku

    def functions_command(self, com):
        while self.command_event.is_set():
            pass
        self.mcom = com
        self.command_event.set()
