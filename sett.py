import json
import os

# Słownik z domyślnymi ustawieniami na wypadek, gdyby pliku jeszcze nie było
DEF_SETT = {
    "theme": "System",
    "default_module": "Karta Przekaźnikowa 1"
}

class SettingsManager:
    file_name = "ModigModbusConfig.json"
    sett_conf = {}

    def init_file(self):
        # 1. Sprawdzenie czy plik NIE istnieje
        if not os.path.exists(self.file_name):
            print("Plik konfiguracyjny nie istnieje. Tworzę nowy...")
            try:
                with open(self.file_name, "w", encoding="utf-8") as plik:
                    json.dump(DEF_SETT, plik, indent=4)

            except Exception as e:
                print(f"Błąd tworzenia pliku, ustawiam domyślne")
                self.sett_conf = DEF_SETT
                return False

        # 2. Jeśli plik istnieje, odczytujemy go
        print("Wczytuję dane z pliku konfiguracyjnyego... ")
        try:
            with open(self.file_name, "r", encoding="utf-8") as plik:
                self.sett_conf = json.load(plik)
                return True
        except Exception as e:
            print(f"Błąd podczas odczytu pliku, ustawiam domyślne")
            self.sett_conf = DEF_SETT
            return False

#setti = SettingsManager()
