import json
import os

class SettingsManager:
    file_name = "ModigModbusConfig.json"

    def init_file(self):

        # Słownik z domyślnymi ustawieniami na wypadek, gdyby pliku jeszcze nie było
        def_sett = {
            "motyw": "System",
            "ostatnia_karta": "Karta Przekaźnikowa 1"
        }

        # 1. Sprawdzenie czy plik NIE istnieje
        if not os.path.exists(self.file_name):
            print("Plik konfiguracyjny nie istnieje. Tworzę nowy z domyślnymi ustawieniami...")
            try:
                with open(self.file_name, "w", encoding="utf-8") as plik:
                    json.dump(def_sett, plik, indent=4)
                return def_sett
            except Exception as e:
                print(f"Błąd podczas tworzenia pliku konfiguracyjnego: {e}")
                return def_sett

        # 2. Jeśli plik istnieje, odczytujemy go
        else:
            print("Znaleziono plik konfiguracyjny. Wczytuję dane...")
            try:
                with open(self.file_name, "r", encoding="utf-8") as plik:
                    dane = json.load(plik)
                    return dane
            except Exception as e:
                print(f"Błąd podczas odczytu pliku (może jest uszkodzony?). Zwracam domyślne. Błąd: {e}")
                return def_sett

setti = SettingsManager()
