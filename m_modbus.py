import threading
import time
from operator import truediv

import minimalmodbus

class ModbusFunctions:
    def __init__(self, app_ref):
        self.functions_event = threading.Event()
        self.functions_thread = None  # Referencja do wątku
        self.action = 0
        self.f_adr = 0
        self.f_reg = 0
        self.f_val = 0
        self.main_ref = app_ref

    def start_functions(self, bus_ref):
        """Uruchamia wątek odpytywania, jeśli nie jest jeszcze aktywny."""
        self.bus = bus_ref
        if self.functions_thread is None or not self.functions_thread.is_alive():
            self.functions_thread = threading.Thread(target=self.functions_loop, daemon=True)
            self.functions_thread.start()
            print("Thread RUN")

    def functions_loop(self):
        """Pętla wykonująca się w tle (w osobnym wątku)."""
        delay = 0
        while True:
            # Sprawdzamy czy połączenie Modbus jest aktywne i skonfigurowane
            if hasattr(self.main_ref, 'app_bus_status') and self.main_ref.app_bus_status is not False:

                #with self.modbus_lock:
                    if self.functions_event.is_set():
                        delay = 0
                        try:
                            if self.action == 5:
                                self.bus.mm.write_bit(self.f_reg, self.f_val)
                                #time.sleep(0.1)
                                self.main_ref.after(0, self.main_ref.outputs_switch_state, (self.f_reg, self.f_val))
                                self.functions_event.clear()
                        except Exception as e:
                            # Logujemy błąd, ale nie wywalamy aplikacji (np. chwilowy brak odpowiedzi)
                            print(f"[Functions Error]: {e}")
                    else :
                        delay += 1
                        if delay == 4:
                            delay = 0
                            try:
                                # Pobieramy parametry bieżącej karty z konfiguracji
                                inputs = self.main_ref.sett_man.get_mod_inputs(self.main_ref.active_module)

                                if inputs > 0:
                                    # Funkcja zwraca listę wartości, np. [0, 1, 0, 0]
                                    in_states = self.bus.mm.read_bits(
                                        registeraddress=1,
                                        number_of_bits=inputs,
                                        functioncode=2
                                    )
                                    #time.sleep(0.1)

                                    # Wywołujemy bezpieczną aktualizację GUI z wątku głównego
                                    self.main_ref.after(0, self.main_ref.input_indicators, in_states)

                            except Exception as e:
                                # Logujemy błąd, ale nie wywalamy aplikacji (np. chwilowy brak odpowiedzi)
                                print(f"[Thread Func Error]: {e}")

            time.sleep(0.1)

    def functions_close(self):
        # Flaga na False kończy pętlę while w wątku tła
        self.functions_event.clear()
        if self.functions_thread and self.functions_thread.is_alive():
            self.functions_thread.join(timeout=1.0) # Czekamy maksymalnie sekundę na zamknięcie wątku

    def functions_wrb(self, mod_adr, reg, val):
        while not self.functions_event.is_set():
            self.action = 5
            self.f_adr = mod_adr
            self.f_reg = reg
            self.f_val = val
            self.functions_event.set()
