from statistics import variance

from sett import SettingsManager
from serial_bus import SerialManager
import customtkinter as ctk

ctk.set_appearance_mode("System")  # Tryb: "System", "Dark" lub "Light"
ctk.set_default_color_theme("blue")  # Motyw kolorystyczny: "blue", "green", "dark-blue"

DEF_VERSION = "1.2 beta"

DEF_LEFT_PANEL_L = "gray70"
DEF_LEFT_PANEL_D = "gray30"
DEF_OPMENU_FG_L = "#84b3d6"
DEF_OPMENU_FG_D = "#4C92C3"
DEF_OPMENUBUTT_FG_L = "#3C749C"
DEF_OPMENUBUTT_FG_D = "#3C749C"

DEF_GRIDPANELS_FG_L = "gray80"
DEF_GRIDPANELS_FG_D = "gray20"
DEF_GRIDPANELS_ACT_FG_L = "#9ddbcf"
DEF_GRIDPANELS_ACT_FG_D = "#226056"

DEF_MODULE_SEL_L = "#fbd68d"
DEF_MODULE_SEL_D = "#b78806"

DEF_IN_OUT_LABELS_L = "#ED3229"
DEF_IN_OUT_LABELS_D = "#ED3229"

DEF_FRAMEM_TX = "#4C92C3"
DEF_FRAMEM_RX = "#4CC3B0"

#---------------------------
class ModigModbusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja ustawień
        self.sett_man = SettingsManager()
        self.sett_man.init_file()
        self.app_bus = SerialManager()
        self.app_bus_status = False

        ctk.set_appearance_mode(self.sett_man.sett_conf.get("theme", "System"))
        ctk.set_default_color_theme("blue")

        # Konfiguracja głównego okna
        self.title("MODIG MODBUS APP ver " + DEF_VERSION)
        self.geometry("900x550")
        self.minsize(800, 600)

        # Konfiguracja siatki (Grid) dla całego okna
        self.grid_columnconfigure(1, weight=1)  # Główny panel rozciąga się w poziomie
        self.grid_rowconfigure(0, weight=1)  # Górna część (panele) zajmuje większość miejsca
        self.grid_rowconfigure(1, weight=0)  # Dolna część (diagnostyka) zajmuje mniej miejsca

        self.active_module = 1

        # --- TWORZENIE ELEMENTÓW INTERFEJSU ---
        self.left_panel_init()
        self.main_panel_init()
        self.mod_panel_builder(self.sett_man.sett_conf.get("def_mod", 1))
        self.bus_frames_panel_init()

        self.protocol("WM_DELETE_WINDOW", self.when_close_app)

    def left_panel_init(self):
        """Tworzy boczny panel nawigacyjny do wyboru kart."""
        self.left_panel = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=(DEF_LEFT_PANEL_L, DEF_LEFT_PANEL_D))
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        #self.left_panel.grid_rowconfigure(3, weight=1)  # Popycha dolne elementy w dół

        # --- SEKCJA PORTU COM ---
        self.com_label = ctk.CTkLabel(self.left_panel, text="SERIAL PORT", font=ctk.CTkFont(size=16, weight="bold"))
        self.com_label.grid(row=0, column=0, padx=20, pady=(5, 5), sticky="w")

        # Tworzymy rozwijane menu (OptionMenu) do wyboru portu COM
        self.com_optionmenu = ctk.CTkOptionMenu(
            self.left_panel,
            text_color=("gray10", "gray90"),
            text_color_disabled=("gray10", "gray90"),
            fg_color=(DEF_OPMENU_FG_L, DEF_OPMENU_FG_D),
            button_color=(DEF_OPMENUBUTT_FG_L, DEF_OPMENUBUTT_FG_D),
            state="normal",
            values=["Empty..."],
            command=self.port_selected)
        self.com_optionmenu.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")

        # Nowy, mniejszy przycisk do odświeżania listy portów
        self.btn_refresh = ctk.CTkButton(
            self.left_panel,
            text="Refresh",
            height=24,  # Mniejsza wysokość, by przycisk był zgrabny
            font=ctk.CTkFont(size=11),  # Nieco mniejsza czcionka
            fg_color=(DEF_MODULE_SEL_L, DEF_MODULE_SEL_D),  # Delikatniejszy kolor dopasowany do jasnego/ciemnego motywu
            text_color=("gray10", "gray90"),
            hover_color=(DEF_MODULE_SEL_D, DEF_MODULE_SEL_L),
            command=self.scan_ports)  # Podpięcie naszej nowej metody
        self.btn_refresh.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")

        # --------------------------------
        # Tytuł sekcji
        self.logo_label = ctk.CTkLabel(self.left_panel, text="MODULES", font=ctk.CTkFont(size=16, weight="bold"))
        self.logo_label.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")

        # Przyciski wyboru kart (jako przykłady)
        self.modules_list = {}
        for idx in range(1, 5):
            # Przyciski wyboru kart (jako przykłady)
            g_item = ctk.CTkButton(self.left_panel, text=f"Modbus Device {idx}",
                fg_color=(DEF_MODULE_SEL_L, DEF_MODULE_SEL_D),
                text_color=("gray10", "gray90"),
                hover_color=(DEF_MODULE_SEL_D, DEF_MODULE_SEL_L), anchor="w",
                command=lambda i=idx: self.module_switch(i))
            g_item.grid(row=(idx + 3), column=0, padx=20, pady=20, sticky="ew")
            self.modules_list[idx] = g_item

        #---------------------------------------------------
        # Opcje na dole panelu (Wybór motywu)
        self.theme_label = ctk.CTkLabel(self.left_panel, text="THEME", font=ctk.CTkFont(size=16, weight="bold"), anchor="w" )
        self.theme_label.grid(row=8, column=0, padx=20, pady=(20, 0), sticky="ew")
        self.theme_optionmenu = ctk.CTkOptionMenu(
            self.left_panel,
            text_color=("gray10", "gray90"),
            text_color_disabled=("gray10", "gray90"),
            fg_color=(DEF_OPMENU_FG_L, DEF_OPMENU_FG_D),
            button_color=(DEF_OPMENUBUTT_FG_L, DEF_OPMENUBUTT_FG_D),
            values=["Dark", "Light", "System"],
            command=self.theme_switch)
        self.theme_optionmenu.grid(row=9, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.theme_optionmenu.set("System")
        self.theme_optionmenu.set(self.sett_man.sett_conf.get("theme", "System"))
        self.scan_ports()

    def scan_ports(self):
        if self.app_bus_status:
            if self.app_bus.ser_close() is True:
                print("Serial port closed")

        self.app_bus_status = False
        self.btn_refresh.configure(text="Refresh")

        # Pobieramy aktualną listę portów z systemu
        self.app_bus.list_get()
        available_ports = [port.device for port in self.app_bus.p_list]
        if not available_ports:
            available_ports = ["Empty..."]

        self.com_optionmenu.configure(values=available_ports)
        self.com_optionmenu.set(available_ports[0])  # Ustawiamy pierwszy wykryty port jako aktywny
        self.com_optionmenu.configure(
            fg_color=[DEF_OPMENU_FG_L, DEF_OPMENU_FG_D],
            button_color=[DEF_OPMENUBUTT_FG_L, DEF_OPMENUBUTT_FG_D],
            state="normal"
        )
        print(f"Serial ports refresh")

    def port_selected(self, wybrany_port):
        """Wywoływane po wybraniu portu z listy rozwijanej."""
        self.app_bus_status = self.app_bus.try_open(wybrany_port)
        if self.app_bus_status:
            my_mm = self.app_bus.serial_get()
            oryg_write = my_mm.serial.write
            oryg_read = my_mm.serial.read

            def new_write(data):
                self.frame_log(1, data)
                return oryg_write(data)

            def new_read(size=1):
                data = oryg_read(size)
                if data:
                    self.frame_log(0, data)
                return data

            my_mm.serial.write = new_write
            my_mm.serial.read = new_read

            print(f"Port selected: {wybrany_port}, and ready")
            # Sukces: zmieniamy kolory menu na zielone (obsługuje od razu Light i Dark mode)
            # Format ["kolor_jasny", "kolor_ciemny"]
            self.com_optionmenu.configure(
                fg_color=["#4CC3B0", "#3CB3A0"],      # Zielony panel
                button_color=["#4CC3B0", "#3CB3A0"],
                state="disabled"
            )
            self.btn_refresh.configure(text="CLOSE")
        else:
            print(f"Port selected: {wybrany_port}, and FAIL")
            self.com_optionmenu.configure(
                fg_color=["#ED3229", "#DD2219"],      # Czerwony panel
                button_color=["#ED3229", "#DD2219"],
                state="normal"
            )
            self.btn_refresh.configure(text="Refresh")

    def when_close_app(self):
        """Metoda wywoływana automatycznie w momencie zamykania programu."""
        print("Zamykanie aplikacji...")
        if self.app_bus.ser_close() is True:
            print("Serial port closed")
        else:
            print("Serial port FAIL")
        # Ostateczne zamknięcie okna i zakończenie działania programu
        self.destroy()

    def main_panel_init(self):
        """Tworzy główny obszar z nagłówkiem i kafelkami przekaźników."""
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def mod_panel_builder(self, mod_index):
        """Czyści panel i buduje go na nowo dla konkretnego modułu."""
        self.active_module = mod_index

        # 1. CZYSZCZENIE: Pobieramy wszystkie dzieci kontenera i je niszczymy (usuwamy z pamięci)
        for widget in self.main_panel.winfo_children():
            widget.destroy()

        # Pobieramy parametry techniczne klikniętego modułu
        mod_params = self.sett_man.sett_conf.get(f"mod{self.active_module}")
        outs = mod_params.get("outputs", 4)
        ins = mod_params.get("inputs", 4)

        # 2. BUDOWANIE NAGŁÓWKA
        self.mod_panel_label = ctk.CTkLabel(
            self.main_panel,
            text=f"{mod_params.get("type", "MD20001")} (Out: {outs}, In: {ins})",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.mod_panel_label.pack(anchor="w", pady=(0, 15))

        # 3. KONTENER NA PRZEŁĄCZNIKI (WYJŚCIA)
        if outs > 0:
            outputs_label = ctk.CTkLabel(self.main_panel, text="OUTPUTS (Relays):",
                                         text_color=(DEF_IN_OUT_LABELS_L, DEF_IN_OUT_LABELS_D),
                                         font=ctk.CTkFont(size=14, weight="bold"))
            outputs_label.pack(anchor="w", pady=(5, 5))

            outputs_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
            outputs_frame.pack(fill="x", pady=(0, 15))

            # Konfigurujemy siatkę na 4 kolumny wewnątrz sekcji wyjść
            for i in range(4):
                outputs_frame.grid_columnconfigure(i, weight=1, uniform="col")

            self.outputs_list = {}
            self.oframe_list = {}
            for idx in range(1, outs + 1):
                row = (idx - 1) // 4
                col = (idx - 1) % 4

                o_item = ctk.CTkFrame(outputs_frame, corner_radius=10)
                o_item.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                self.oframe_list[idx] = o_item

                switch = ctk.CTkSwitch(o_item, text="OFF", command=lambda i=idx: self.outputs_switch(i))
                switch.pack(padx=20, pady=20, anchor="w")

                label_out = ctk.CTkLabel(o_item, text=f"Out {idx}", font=ctk.CTkFont(size=12, weight="bold"))
                #label_out.pack(padx=10, pady=(10, 2), anchor="w")
                label_out.place(relx=0.5, rely=0.5, anchor="w", x=20)  # Przesunięcie tekstu obok diody

                self.outputs_list[idx] = switch

        # 4. KONTENER NA KONTROLKI (WEJŚCIA cyfrowe)
        if ins > 0:
            inputs_label = ctk.CTkLabel(self.main_panel, text="INPUTS:",
                                        text_color=(DEF_IN_OUT_LABELS_L, DEF_IN_OUT_LABELS_D),
                                        font=ctk.CTkFont(size=14, weight="bold"))
            inputs_label.pack(anchor="w", pady=(5, 5))

            inputs_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
            inputs_frame.pack(fill="x")

            for i in range(4):
                inputs_frame.grid_columnconfigure(i, weight=1, uniform="col")

            self.inputs_list = {}
            for idx in range(1, ins + 1):
                row = (idx - 1) // 4
                col = (idx - 1) % 4

                i_item = ctk.CTkFrame(inputs_frame, corner_radius=10)
                i_item.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

                # Kontrolka wejścia jako mała okrągła dioda (zwykły Label stylizowany na kółko)
                # Domyślnie szara (brak sygnału), po odczycie stanu z Modbus zmienimy na czerwoną/zieloną
                dioda = ctk.CTkLabel(i_item,
                    text="● IDLE", text_color="gray",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                dioda.pack(padx=15, pady=12, anchor="w")

                # Dodatkowa tekstowa informacja wewnątrz kafelka
                label_in = ctk.CTkLabel(i_item, text=f"Input {idx}", font=ctk.CTkFont(size=12, weight="bold"))
                label_in.place(relx=0.5, rely=0.5, anchor="w", x=10)  # Przesunięcie tekstu obok diody

                self.inputs_list[idx] = dioda


    # --- LOGIKA DIALOGU I AKCJI ---
    def module_switch(self, mod_index):
        """Wywoływane po kliknięciu karty w bocznym panelu."""
        self.active_module = mod_index
        self.mod_panel_builder(self.active_module)
        #self.module_top_label.configure(text=module_name)
        print(f"Switch Mod: {self.active_module}")
        # TODO: Tutaj dodasz w przyszłości odczyt aktualnego stanu przekaźników przez Modbus dla nowej karty

    def outputs_switch(self, output_index):
        """Wywoływane przy zmianie pozycji przełącznika."""
        switch = self.outputs_list[output_index]
        switch_new_state = switch.get()
        frame = self.oframe_list[output_index]

        result = False
        if self.app_bus_status:
            result = self.app_bus.mm_wr_bit(output_index, switch_new_state)

        if result:
            # Aktualizacja tekstu obok przełącznika
            if switch_new_state == 1:
                print(f"[{self.active_module}] Set output {output_index}")
                switch.configure(text="ON", progress_color="green")
                frame.configure(fg_color=[DEF_GRIDPANELS_ACT_FG_L, DEF_GRIDPANELS_ACT_FG_D])
            else:
                print(f"[{self.active_module}] Reset output {output_index}")
                switch.configure(text="OFF")
                frame.configure(fg_color=[DEF_GRIDPANELS_FG_L, DEF_GRIDPANELS_FG_D])
        else:
            print(f"[{self.active_module}] Output {output_index} FAIL")
            #switch.toggle()

    def theme_switch(self, new_theme):
        """Zmienia motyw kolorystyczny całej aplikacji w locie."""
        ctk.set_appearance_mode(new_theme)
        self.sett_man.new_val("theme", new_theme)

    def bus_frames_panel_init(self):
        """Tworzy dolne okno tekstowe do podglądu ramek HEX."""
        # Pole tekstowe (zablokowane do edycji dla użytkownika: state="disabled")
        self.diag_text = ctk.CTkTextbox(self, height=60, font=ctk.CTkFont(family="Courier", size=12))
        self.diag_text.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.diag_text.configure(state="disabled")

        self.diag_text._textbox.tag_config("tx", foreground=DEF_FRAMEM_TX)  # Ładny niebieski dla nadawania
        self.diag_text._textbox.tag_config("rx", foreground=DEF_FRAMEM_RX)  # Żywy zielony dla odbierania

    def frame_log(self, kierunek, ramka_bytes):
        """Dodaje sformatowaną ramkę HEX do panelu na dole."""
        # Konwersja surowych bajtów na czytelny format HEX z odstępami, np. "01 05 00 00 FF 00"
        hex_string = " ".join(f"{b:02X}" for b in ramka_bytes)
        if kierunek == 1:
            prefix = "[TX]"
            tag_name = "tx"
        else:
            prefix = "[RX]"
            tag_name = "rx"

        tekst_logu = f"{prefix}: {hex_string}\n"

        # Odblokowanie pola, dopisanie tekstu na końcu i ponowne zablokowanie
        self.diag_text.configure(state="normal")
        self.diag_text.insert("end", tekst_logu, tag_name)
        self.diag_text.see("end")  # Automatyczne przewijanie do najnowszej linii
        self.diag_text.configure(state="disabled")


if __name__ == "__main__":
    app = ModigModbusApp()
    app.mainloop()
