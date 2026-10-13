import threading
import time
import minimalmodbus

class ModbusFunctions:
    functions_event = threading.Event()
    functions_thread = None  # Referencja do wątku

    #def __init__(self, modbus):
    #    self.mf_bus = modbus

    def start_functions(self, app_ref):
        """Uruchamia wątek odpytywania, jeśli nie jest jeszcze aktywny."""
        self.main_ref = app_ref
        if self.functions_thread is None or not self.functions_thread.is_alive():
            self.functions_event.set()  # Ustawiamy flagę na True (wątek ma działać)
            self.functions_thread = threading.Thread(target=self._functions_loop, daemon=True)
            self.functions_thread.start()
            print("Wątek odpytywania Modbus został uruchomiony.")

    def _functions_loop(self):
        """Pętla wykonująca się w tle (w osobnym wątku)."""
        while self.functions_event.is_set():
            # Sprawdzamy czy połączenie Modbus jest aktywne i skonfigurowane
            if hasattr(self.main_ref, 'app_bus_status') and self.main_ref.app_bus_status is not False:

                # Blokujemy port przed wywołaniem odczytu
                with self.main_ref.modbus_lock:

                    try:
                        # Pobieramy parametry bieżącej karty z konfiguracji
                        inputs = self.main_ref.sett_man.get_mod_inputs(self.main_ref.active_module)

                        if inputs > 0:
                            # Funkcja zwraca listę wartości, np. [0, 1, 0, 0]
                            in_states = self.main_ref.app_bus.mm.read_bits(
                                registeraddress=1,
                                number_of_bits=inputs,
                                functioncode=2
                            )

                            # Wywołujemy bezpieczną aktualizację GUI z wątku głównego
                            self.after(0, self.main_ref.input_indicators, in_states)

                    except Exception as e:
                        # Logujemy błąd, ale nie wywalamy aplikacji (np. chwilowy brak odpowiedzi)
                        print(f"[Functions Error]: {e}")

            # Czas oczekiwania pomiędzy odpytaniami (np. 300 ms - optymalne dla statusów)
            time.sleep(0.3)

    def functions_close(self):
        # Flaga na False kończy pętlę while w wątku tła
        self.functions_event.clear()
        if self.functions_thread and self.polling_thread.is_alive():
            self.functions_thread.join(timeout=1.0) # Czekamy maksymalnie sekundę na zamknięcie wątku
