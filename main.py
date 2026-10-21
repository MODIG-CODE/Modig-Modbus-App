import threading
import time
from dataclasses import dataclass
from sett import SettingsManager
from serial_bus import SerialManager
from m_modbus import ModbusFunctions
from m_modbus import ModbusCommand
import customtkinter as ctk

ctk.set_appearance_mode("System")  # Tryb: "System", "Dark" lub "Light"
ctk.set_default_color_theme("blue")  # Motyw kolorystyczny: "blue", "green", "dark-blue"

DEF_VERSION = "1.3 beta"

DEF_LEFT_PANEL_L = "gray70"
DEF_LEFT_PANEL_D = "gray30"
DEF_OPMENU_FG_L = "#84b3d6"
DEF_OPMENU_FG_D = "#4C92C3"
DEF_OPMENUBUTT_FG_L = "#3C749C"
DEF_OPMENUBUTT_FG_D = "#3C749C"

DEF_OGRIDPANELS_FG_L = "gray80"
DEF_OGRIDPANELS_FG_D = "gray20"
DEF_OGRIDPANELS_ACT_FG_L = "#fbd68d"
DEF_OGRIDPANELS_ACT_FG_D = "#b78806"

DEF_IGRIDPANELS_FG_L = "gray80"
DEF_IGRIDPANELS_FG_D = "gray20"
DEF_IGRIDPANELS_ACT_FG_L = "#9ddbcf"
DEF_IGRIDPANELS_ACT_FG_D = "#226056"

DEF_MODULE_SEL_L = "#9db8ce"
DEF_MODULE_SEL_D = "#3C749C"

DEF_IN_OUT_LABELS_L = "#ED3229"
DEF_IN_OUT_LABELS_D = "#ED3229"

DEF_FRAMEM_TX = "#4C92C3"
DEF_FRAMEM_RX = "#4CC3B0"

#---------------------------

@dataclass
class ModbusModule:
    active: int
    type: str
    adr: int
    offset: int
    outputs: int
    inputs: int

class ModigModbusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja ustawień
        self.sett_man = SettingsManager()
        self.sett_man.init_file()
        self.module = ModbusModule
        self.module.active = self.sett_man.get_act_mod()

        self.app_bus_status = False
        self.app_bus = SerialManager()
        self.mfunc = ModbusFunctions(self)

        self.outputs_list = {}
        self.oframes_list = {}
        self.inputs_list = {}
        self.iframes_list = {}

        ctk.set_appearance_mode(self.sett_man.get_theme())
        ctk.set_default_color_theme("blue")

        # Konfiguracja głównego okna
        self.title("MODIG MODBUS APP ver " + DEF_VERSION)
        self.geometry("900x550")
        self.minsize(800, 600)

        # Konfiguracja siatki (Grid) dla całego okna
        self.grid_columnconfigure(1, weight=1)  # Główny panel rozciąga się w poziomie
        self.grid_rowconfigure(0, weight=1)  # Górna część (panele) zajmuje większość miejsca
        self.grid_rowconfigure(1, weight=0)  # Dolna część (diagnostyka) zajmuje mniej miejsca

        # --- TWORZENIE ELEMENTÓW INTERFEJSU ---
        self.left_panel_init()
        self.main_panel_init()
        self.module_switch(self.module.active)
        self.mod_panel_builder()
        self.bus_frames_panel_init()

        self.protocol("WM_DELETE_WINDOW", self.when_close_app)

        #-----------------------------------------------
        #my_mm = self.app_bus.serial_get()
        oryg_write =  self.app_bus.ser.write
        oryg_read = self.app_bus.ser.read

        def new_write(data):
            self.frame_log(1, data)
            return oryg_write(data)

        def new_read(size=1):
            data = oryg_read(size)
            if data:
                self.frame_log(0, data)
            return data

        self.app_bus.ser.write = new_write
        self.app_bus.ser.read = new_read

        self.mfunc.start_functions(self.app_bus)

    def when_close_app(self):
        if self.module.active is not self.sett_man.get_act_mod():
            self.sett_man.new_val("def_mod", self.module.active)
        print("Zamykanie aplikacji...")
        self.mfunc.functions_close()
        self.app_bus.ser_close()
        self.destroy()

    # -----------------------------------------------------------
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
            """name = (f"{self.sett_man.get_mod_type(idx)} "
                    f"(A:{self.sett_man.get_mod_adr(idx)}"
                    f" O:{self.sett_man.get_mod_outputs(idx)} "
                    f" I:{self.sett_man.get_mod_inputs(idx)})")"""
            name = f"{self.sett_man.get_mod_type(idx)} (Adr:{self.sett_man.get_mod_adr(idx)})"
            g_item = ctk.CTkButton(self.left_panel, text=name,
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
        self.theme_optionmenu.set(self.sett_man.get_theme())
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
        if self.app_bus.try_open(wybrany_port):
            print(f"Port selected: {wybrany_port}, and ready")
            # Sukces: zmieniamy kolory menu na zielone (obsługuje od razu Light i Dark mode)
            # Format ["kolor_jasny", "kolor_ciemny"]
            self.com_optionmenu.configure(
                fg_color=["#4CC3B0", "#3CB3A0"],      # Zielony panel
                button_color=["#4CC3B0", "#3CB3A0"],
                state="disabled"
            )
            self.btn_refresh.configure(text="CLOSE")
            self.app_bus_status = True
        else:
            self.app_bus_status = False
            print(f"Port selected: {wybrany_port}, and FAIL")
            self.com_optionmenu.configure(
                fg_color=["#ED3229", "#DD2219"],      # Czerwony panel
                button_color=["#ED3229", "#DD2219"],
                state="normal"
            )
            self.btn_refresh.configure(text="Refresh")

    def theme_switch(self, new_theme):
        ctk.set_appearance_mode(new_theme)
        self.sett_man.new_val("theme", new_theme)

    # -----------------------------------------------------------
    def main_panel_init(self):
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def module_switch(self, mod_index):
        self.module.active = mod_index
        self.module.type = self.sett_man.get_mod_type(self.module.active)
        self.module.adr = self.sett_man.get_mod_adr(self.module.active)
        self.module.offset = self.sett_man.get_mod_off(self.module.active)
        self.module.outputs = self.sett_man.get_mod_outputs(self.module.active)
        self.module.inputs = self.sett_man.get_mod_inputs(self.module.active)
        print(f"Switch Mod: {self.module.active}")
        self.mod_panel_builder()
        self.outputs_read()

    def mod_panel_builder(self):
        for widget in self.main_panel.winfo_children():
            widget.destroy()

        #-----------------------------------------
        mod_header = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        mod_header.pack(fill="x", pady=(0, 15))

        self.mod_label = ctk.CTkLabel(
            mod_header,
            text=f"{self.module.type} (Out: {self.module.outputs}, In: {self.module.inputs})",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        #self.mod_label.pack(anchor="w", pady=(0, 15))
        self.mod_label.pack(side="left", anchor="w")

        # Kontener na ustawienie adresu (po prawej stronie paska)
        adr_sel_frame = ctk.CTkFrame(mod_header, fg_color="transparent")
        adr_sel_frame.pack(side="right", anchor="e")

        address_label = ctk.CTkLabel(adr_sel_frame, text="Modbus Address (Slave ID):", font=ctk.CTkFont(size=12))
        address_label.pack(side="left", padx=(0, 5))

        # Pole tekstowe do wpisania adresu (sztywna szerokość width=50)
        self.address_entry = ctk.CTkEntry(adr_sel_frame, width=50, justify="center")
        self.address_entry.pack(side="left", padx=(0, 5))
        self.address_entry.insert(0, str(self.module.adr)) # Wstawiamy aktualnie zapisany adres

        # Przycisk zatwierdzający zmianę adresu
        btn_adres_accept = ctk.CTkButton(
            adr_sel_frame,
            text="Save",
            width=60,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self.new_address_save
        )
        btn_adres_accept.pack(side="left")

        #---------------------------------------------------------
        self.outputs_list = {}
        self.oframes_list = {}
        if self.module.outputs > 0:
            outputs_label = ctk.CTkLabel(self.main_panel, text="OUTPUTS (Relays):",
                                         text_color=(DEF_IN_OUT_LABELS_L, DEF_IN_OUT_LABELS_D),
                                         font=ctk.CTkFont(size=14, weight="bold"))
            outputs_label.pack(anchor="w", pady=(5, 5))
            outputs_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
            outputs_frame.pack(fill="x", pady=(0, 15))

            # Konfigurujemy siatkę na 4 kolumny wewnątrz sekcji wyjść
            for i in range(4):
                outputs_frame.grid_columnconfigure(i, weight=1, uniform="col")

            for idx in range(1, self.module.outputs + 1):
                row = (idx - 1) // 4
                col = (idx - 1) % 4

                o_item = ctk.CTkFrame(outputs_frame, corner_radius=10)
                o_item.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                self.oframes_list[idx] = o_item

                switch = ctk.CTkSwitch(o_item, progress_color=("gray20", "gray80"), command=lambda i=idx: self.outputs_switch(i))
                switch.pack(padx=15, pady=15, anchor="w")
                self.outputs_list[idx] = switch

                label_out = ctk.CTkLabel(o_item, text=f"Out {idx}", font=ctk.CTkFont(size=12, weight="bold"))
                #label_out.pack(padx=10, pady=(10, 2), anchor="w")
                label_out.place(relx=0.5, rely=0.5, anchor="w", x=20)  # Przesunięcie tekstu obok diody

                self.outputs_switch_state((idx, 0))

        #---------------------------------------------------------
        self.inputs_list = {}
        self.iframes_list = {}
        if self.module.inputs > 0:
            inputs_label = ctk.CTkLabel(self.main_panel, text="INPUTS:",
                                        text_color=(DEF_IN_OUT_LABELS_L, DEF_IN_OUT_LABELS_D),
                                        font=ctk.CTkFont(size=14, weight="bold"))
            inputs_label.pack(anchor="w", pady=(5, 5))

            inputs_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
            inputs_frame.pack(fill="x", pady=(0, 15))

            for i in range(4):
                inputs_frame.grid_columnconfigure(i, weight=1, uniform="col")

            for idx in range(1, self.module.inputs + 1):
                row = (idx - 1) // 4
                col = (idx - 1) % 4

                i_item = ctk.CTkFrame(inputs_frame, corner_radius=10)
                i_item.configure(fg_color=[DEF_IGRIDPANELS_FG_L, DEF_IGRIDPANELS_FG_D])
                i_item.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                self.iframes_list[idx] = i_item

                indicator = ctk.CTkLabel(i_item, font=ctk.CTkFont(size=18, weight="bold"))
                indicator.pack(padx=15, pady=12, anchor="w")
                self.inputs_list[idx] = indicator
                self.input_indicator_state(idx, 0)

                label_in = ctk.CTkLabel(i_item, text=f"Input {idx}", font=ctk.CTkFont(size=12, weight="bold"))
                label_in.place(relx=0.5, rely=0.5, anchor="w", x=10)  # Przesunięcie tekstu obok diody

    def new_address_save(self):
        """Pobiera adres z pola Entry, waliduje go i zapisuje do konfiguracji."""
        raw_text = self.address_entry.get()

        try:
            new_adr = int(raw_text)
            if 1 <= new_adr <= 255:
                self.module.adr = new_adr
                self.sett_man.new_mod_val(self.module.active, "adr", new_adr)
            else:
                print("Błąd: Adres Modbus musi mieścić się w zakresie od 1 do 247.")
                self.addres_entry.delete(0, "end")
                self.addres_entry.insert(0, self.module.adr)

        except ValueError:
            print("Błąd: Wprowadzona wartość nie jest liczbą całkowitą!")
            self.addres_entry.delete(0, "end")
            self.addres_entry.insert(0, self.module.adr)

    def outputs_switch(self, output_index):
        """Wywoływane przy zmianie pozycji przełącznika."""
        switch = self.outputs_list[output_index]
        switch_new_state = switch.get()

        #result = False
        if self.app_bus_status:
            if self.module.offset == 0: output_index -= 1
            command = ModbusCommand(
                action="wrb",
                adr=self.module.adr,
                reg=output_index,
                val=switch_new_state
            )
            self.mfunc.functions_command(command)

    def outputs_read(self):
        if self.app_bus_status:
            command = ModbusCommand(
                action="rdb",
                adr=self.module.adr,
                reg=self.module.offset,
                val=16
            )
            self.mfunc.functions_command(command)

    def outputs_all_switch_state(self, new_states):
        for idx in range(1, self.module.outputs + 1):
            self.outputs_switch_state((idx, new_states[idx-1]))

    def outputs_switch_state(self, index_state):
        switch = self.outputs_list[index_state[0]]
        frame = self.oframes_list[index_state[0]]
        if index_state[1] == 1:
            switch.configure(text="ON")
            switch.select()
            frame.configure(fg_color=[DEF_OGRIDPANELS_ACT_FG_L, DEF_OGRIDPANELS_ACT_FG_D])
        else:
            switch.configure(text="OFF")
            switch.deselect()
            frame.configure(fg_color=[DEF_OGRIDPANELS_FG_L, DEF_OGRIDPANELS_FG_D])

    def input_indicators(self, read_states):
        for idx, state in enumerate(read_states, start=1):
            if idx in self.inputs_list:
                self.input_indicator_state(idx, state)

    def input_indicator_state(self, index, state):
        indicator = self.inputs_list[index]
        iframe = self.iframes_list[index]

        if state == 1:
            indicator.configure(text="● ACT", text_color="#4CC3B0")  # Zielony dla aktywnego wejścia)
            iframe.configure(fg_color=[DEF_IGRIDPANELS_ACT_FG_L, DEF_IGRIDPANELS_ACT_FG_D])
        else:
            indicator.configure(text="● IDLE", text_color="gray")
            iframe.configure(fg_color=[DEF_IGRIDPANELS_FG_L, DEF_OGRIDPANELS_FG_D])

    # -----------------------------------------------------------
    def bus_frames_panel_init(self):
        """Tworzy dolne okno tekstowe do podglądu ramek HEX."""
        # Pole tekstowe (zablokowane do edycji dla użytkownika: state="disabled")
        self.diag_text = ctk.CTkTextbox(self, height=60, font=ctk.CTkFont(family="Courier", size=12))
        self.diag_text.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.diag_text.configure(state="disabled")

        self.diag_text._textbox.tag_config("tx", foreground=DEF_FRAMEM_TX)
        self.diag_text._textbox.tag_config("rx", foreground=DEF_FRAMEM_RX)

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

    # -----------------------------------------------------------
if __name__ == "__main__":
    app = ModigModbusApp()
    app.mainloop()
