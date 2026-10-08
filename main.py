import customtkinter as ctk

# Ustawienia globalne wyglądu aplikacji
ctk.set_appearance_mode("System")  # Tryb: "System", "Dark" lub "Light"
ctk.set_default_color_theme("blue")  # Motyw kolorystyczny: "blue", "green", "dark-blue"


class RelayControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Konfiguracja głównego okna
        self.title("Panel Sterowania Przekaźnikami Modbus")
        self.geometry("900x550")
        self.minsize(800, 450)

        # Konfiguracja siatki (Grid) dla całego okna
        self.grid_columnconfigure(1, weight=1)  # Główny panel rozciąga się w poziomie
        self.grid_rowconfigure(0, weight=1)  # Oba panele rozciągają się w pionie

        # --- ZMIENNE STANU ---
        self.aktywna_karta = "Karta Przekaźnikowa 1"
        self.stany_przekaznikow = {i: False for i in range(1, 9)}  # Symulacja stanu 8 przekaźników

        # --- TWORZENIE ELEMENTÓW INTERFEJSU ---
        self.stworz_boczny_panel()
        self.stworz_glowny_panel()

    def stworz_boczny_panel(self):
        """Tworzy boczny panel nawigacyjny do wyboru kart."""
        self.boczny_panel = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.boczny_panel.grid(row=0, column=0, sticky="nsew")
        self.boczny_panel.grid_rowconfigure(4, weight=1)  # Popycha dolne elementy w dół

        # Tytuł sekcji
        self.logo_label = ctk.CTkLabel(self.boczny_panel, text="URZĄDZENIA", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        # Przyciski wyboru kart (jako przykłady)
        self.btn_karta1 = ctk.CTkButton(self.boczny_panel, text="Karta Modbus ID: 1", fg_color="transparent",
                                        text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w",
                                        command=lambda: self.zmien_karte("Karta Przekaźnikowa 1"))
        self.btn_karta1.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_karta2 = ctk.CTkButton(self.boczny_panel, text="Karta Modbus ID: 2", fg_color="transparent",
                                        text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w",
                                        command=lambda: self.zmien_karte("Karta Przekaźnikowa 2"))
        self.btn_karta2.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Opcje na dole panelu (Wybór motywu)
        self.theme_label = ctk.CTkLabel(self.boczny_panel, text="Motyw:", anchor="w")
        self.theme_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.theme_optionmenu = ctk.CTkOptionMenu(self.boczny_panel, values=["Dark", "Light", "System"],
                                                  command=self.zmien_motyw)
        self.theme_optionmenu.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.theme_optionmenu.set("System")

    def stworz_glowny_panel(self):
        """Tworzy główny obszar z nagłówkiem i kafelkami przekaźników."""
        self.glowny_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.glowny_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Konfiguracja siatki dla kafelków (np. 4 kolumny)
        for i in range(4):
            self.glowny_panel.grid_columnconfigure(i, weight=1, uniform="kafelek")

        # Nagłówek informujący o wybranej karcie
        self.naglowek_label = ctk.CTkLabel(self.glowny_panel, text=self.aktywna_karta,
                                           font=ctk.CTkFont(size=24, weight="bold"))
        self.naglowek_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 20), sticky="w")

        # Generowanie 8 kafelków (2 rzędy po 4 kafelki)
        self.kafelki_przekaznikow = {}
        for idx in range(1, 9):
            rzad = 1 if idx <= 4 else 2
            kolumna = (idx - 1) % 4

            # Pojedynczy kafelek jako CTkFrame
            kafelek = ctk.CTkFrame(self.glowny_panel, corner_radius=12)
            kafelek.grid(row=rzad, column=kolumna, padx=10, pady=10, sticky="nsew")
            kafelek.grid_columnconfigure(0, weight=1)

            # Etykieta wewnątrz kafelka
            label = ctk.CTkLabel(kafelek, text=f"Przekaźnik {idx}", font=ctk.CTkFont(size=14, weight="bold"))
            label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

            # Nowoczesny przełącznik (Switch) zamiast klasycznego przycisku
            switch = ctk.CTkSwitch(kafelek, text="Wyłączony", command=lambda i=idx: self.przelacz_przekaznik(i))
            switch.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="w")

            # Zapisujemy referencję do przełącznika, by móc zmieniać jego stan z poziomu kodu
            self.kafelki_przekaznikow[idx] = switch

    # --- LOGIKA DIALOGU I AKCJI ---
    def zmien_karte(self, nazwa_karty):
        """Wywoływane po kliknięciu karty w bocznym panelu."""
        self.aktywna_karta = nazwa_karty
        self.naglowek_label.configure(text=nazwa_karty)
        print(f"Przełączono widok na: {nazwa_karty}")
        # TODO: Tutaj dodasz w przyszłości odczyt aktualnego stanu przekaźników przez Modbus dla nowej karty

    def przelacz_przekaznik(self, numer_przekaznika):
        """Wywoływane przy zmianie pozycji przełącznika."""
        switch = self.kafelki_przekaznikow[numer_przekaznika]
        nowy_stan = switch.get() == 1  # True jeśli włączony, False jeśli wyłączony

        # Aktualizacja tekstu obok przełącznika
        if nowy_stan:
            switch.configure(text="Włączony", progress_color="green")
            print(f"[{self.aktywna_karta}] Włączam przekaźnik nr {numer_przekaznika}")
            # TODO: Tutaj dodasz wysłanie ramki Modbus RTU: Włącz (np. write_bit(numer, 1))
        else:
            switch.configure(text="Wyłączony")
            print(f"[{self.aktywna_karta}] Wyłączam przekaźnik nr {numer_przekaznika}")
            # TODO: Tutaj dodasz wysłanie ramki Modbus RTU: Wyłącz (np. write_bit(numer, 0))

    def zmien_motyw(self, nowy_motyw):
        """Zmienia motyw kolorystyczny całej aplikacji w locie."""
        ctk.set_appearance_mode(nowy_motyw)


if __name__ == "__main__":
    app = RelayControlApp()
    app.mainloop()
