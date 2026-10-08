from sett import SettingsManager
from serial_bus import SerialManager
import customtkinter as ctk

ctk.set_appearance_mode("System")  # Tryb: "System", "Dark" lub "Light"
ctk.set_default_color_theme("blue")  # Motyw kolorystyczny: "blue", "green", "dark-blue"

#---------------------------
class ModigModbusApp(ctk.CTk):
    def __init__(self):

        # Konfiguracja ustawień
        self.sett_man = SettingsManager()
        self.sett_man.init_file()

        #self.app_bus = SerialManager()

        restore_theme = self.sett_man.sett_conf.get("theme", "System")
        ctk.set_appearance_mode(restore_theme)
        ctk.set_default_color_theme("blue")

        # Konfiguracja głównego okna
        self.title("MODIG MODBUS APP")
        self.geometry("900x550")
        self.minsize(800, 450)

        # Konfiguracja siatki (Grid) dla całego okna
        self.grid_columnconfigure(1, weight=1)  # Główny panel rozciąga się w poziomie
        self.grid_rowconfigure(0, weight=1)  # Oba panele rozciągają się w pionie

        # --- ZMIENNE STANU ---
        self.active_module = "Karta Przekaźnikowa 1"
        self.outputs_state = {i: False for i in range(1, 9)}  # Symulacja stanu 8 przekaźników

        # --- TWORZENIE ELEMENTÓW INTERFEJSU ---
        self.left_panel_init()
        self.main_panel_init()

    def left_panel_init(self):
        """Tworzy boczny panel nawigacyjny do wyboru kart."""
        self.left_panel = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(4, weight=1)  # Popycha dolne elementy w dół

        # Tytuł sekcji
        self.logo_label = ctk.CTkLabel(self.left_panel, text="MODULES", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- SEKCJA PORTU COM ---
        #self.com_label = ctk.CTkLabel(self.left_panel, text="Serial port:", font=ctk.CTkFont(size=12))
        #self.com_label.grid(row=1, column=0, padx=20, pady=(5, 0), sticky="w")

        # Pobieramy listę dostępnych portów (tylko nazwy, np. ['COM3', 'COM4'])
        '''self.app_bus.list_get()
        available_ports = [port.device for port in self.app_bus.p_list]

        # Jeśli nie ma portów, dajemy informację zastępczą, żeby menu nie było puste
        if not available_ports:
            available_ports = ["Brak portów"]
        # Tworzymy rozwijane menu (OptionMenu) do wyboru portu COM
        self.com_optionmenu = ctk.CTkOptionMenu(self.left_panel, values=available_ports, command=self.port_selected)
        self.com_optionmenu.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.com_optionmenu.set(available_ports[0])  # Ustawiamy pierwszy wykryty port jako aktywny
        # --------------------------------
        '''

        # Przyciski wyboru kart (jako przykłady)
        self.btn_module1 = ctk.CTkButton(self.left_panel, text="Karta Modbus ID: 1", fg_color="transparent",
                                        text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w",
                                        command=lambda: self.module_switch("Karta Przekaźnikowa 1"))
        self.btn_module1.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_module2 = ctk.CTkButton(self.left_panel, text="Karta Modbus ID: 2", fg_color="transparent",
                                        text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w",
                                        command=lambda: self.module_switch("Karta Przekaźnikowa 2"))
        self.btn_module2.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Opcje na dole panelu (Wybór motywu)
        self.theme_label = ctk.CTkLabel(self.left_panel, text="Motyw:", anchor="w")
        self.theme_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.theme_optionmenu = ctk.CTkOptionMenu(self.left_panel, values=["Dark", "Light", "System"], command=self.theme_switch)
        self.theme_optionmenu.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.theme_optionmenu.set("System")
        restore_theme = self.sett_man.sett_conf.get("theme", "System")
        self.theme_optionmenu.set(restore_theme)

    def port_selected(self, wybrany_port):
        """Wywoływane po wybraniu portu z listy rozwijanej."""
        print(f"Wybrano port komunikacyjny: {wybrany_port}")
        # W przyszłości: tutaj przypiszemy ten port do naszego połączenia Modbus


    def main_panel_init(self):
        """Tworzy główny obszar z nagłówkiem i kafelkami przekaźników."""
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Konfiguracja siatki dla kafelków (np. 4 kolumny)
        for i in range(4):
            self.main_panel.grid_columnconfigure(i, weight=1, uniform="g_item")

        # Nagłówek informujący o wybranej karcie
        self.module_top_label = ctk.CTkLabel(self.main_panel, text=self.active_module,
                                           font=ctk.CTkFont(size=24, weight="bold"))
        self.module_top_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 20), sticky="w")

        # Generowanie 8 kafelków (2 rzędy po 4 kafelki)
        self.outputs_grid = {}
        for idx in range(1, 9):
            in_row = 1 if idx <= 4 else 2
            in_col = (idx - 1) % 4

            # Pojedynczy g_item jako CTkFrame
            g_item = ctk.CTkFrame(self.main_panel, corner_radius=12)
            g_item.grid(row=in_row, column=in_col, padx=10, pady=10, sticky="nsew")
            g_item.grid_columnconfigure(0, weight=1)

            # Etykieta wewnątrz kafelka
            label = ctk.CTkLabel(g_item, text=f"Output {idx}", font=ctk.CTkFont(size=14, weight="bold"))
            label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

            # Nowoczesny przełącznik (Switch) zamiast klasycznego przycisku
            switch = ctk.CTkSwitch(g_item, text="OFF", command=lambda i=idx: self.outputs_switch(i))
            switch.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="w")

            # Zapisujemy referencję do przełącznika, by móc zmieniać jego stan z poziomu kodu
            self.outputs_grid[idx] = switch

    # --- LOGIKA DIALOGU I AKCJI ---
    def module_switch(self, module_name):
        """Wywoływane po kliknięciu karty w bocznym panelu."""
        self.active_module = module_name
        self.module_top_label.configure(text=module_name)
        print(f"Module: {module_name}")
        # TODO: Tutaj dodasz w przyszłości odczyt aktualnego stanu przekaźników przez Modbus dla nowej karty

    def outputs_switch(self, output_index):
        """Wywoływane przy zmianie pozycji przełącznika."""
        switch = self.outputs_grid[output_index]
        switch_new_state = switch.get() == 1  # True jeśli włączony, False jeśli wyłączony

        # Aktualizacja tekstu obok przełącznika
        if switch_new_state:
            switch.configure(text="ON", progress_color="green")
            print(f"[{self.active_module}] Set output {output_index}")
            # TODO: Tutaj dodasz wysłanie ramki Modbus RTU: Włącz (np. write_bit(numer, 1))
        else:
            switch.configure(text="OFF")
            print(f"[{self.active_module}] Reset output {output_index}")
            # TODO: Tutaj dodasz wysłanie ramki Modbus RTU: Wyłącz (np. write_bit(numer, 0))

    def theme_switch(self, new_theme):
        """Zmienia motyw kolorystyczny całej aplikacji w locie."""
        ctk.set_appearance_mode(new_theme)
        self.sett_man.new_val("theme", new_theme)


if __name__ == "__main__":
    app = ModigModbusApp()
    app.mainloop()
