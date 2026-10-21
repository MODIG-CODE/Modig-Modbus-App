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
                    self.bus.mm.address = self.mcom.adr

                    try:
                        if self.mcom.action == "wrb":
                            self.bus.mm.write_bit(
                                registeraddress=self.mcom.reg,
                                value=self.mcom.val,
                                functioncode=5)
                            #time.sleep(0.1)
                            self.main_ref.after(0, self.main_ref.outputs_switch_state, (self.mcom.reg, self.mcom.val))

                        elif self.mcom.action == "rdb":
                            in_states = self.bus.mm.read_bits(
                                registeraddress=self.mcom.reg,
                                number_of_bits=self.mcom.val,
                                functioncode=1
                            )
                            #time.sleep(0.1)
                            for i in range(16 - len(in_states)):
                                in_states.append(0)

                            new_states = in_states[8:] + in_states[:8]
                            self.main_ref.after(0, self.main_ref.outputs_all_switch_state, new_states)

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
                                if inputs < 16: inputs = 16
                                self.bus.mm.address = self.main_ref.module.adr
                                # Funkcja zwraca listę wartości, np. [0, 1, 0, 0]
                                in_states = self.bus.mm.read_bits(
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
        while self.command_event.is_set():
            pass
        self.mcom = com
        self.command_event.set()
