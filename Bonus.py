"""
BetConstruct Bonus Raporu - Tek Dosya Versiyonu
Streamlit web uygulaması - API entegrasyonu, tarih filtreleme ve Excel export özellikleri ile
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
import requests
from ttkthemes import ThemedTk
import pandas as pd
from datetime import datetime, timedelta
import json
import os

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Ayarlar - Şifre Gerekli")
        self.geometry("400x300")
        self.resizable(False, False)
        
        self.parent = parent
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        
        # Şifre kontrolü
        self.password_frame = ttk.Frame(self)
        self.password_frame.pack(pady=20, padx=20, fill=tk.X)
        
        ttk.Label(self.password_frame, text="Ayarlara erişmek için şifre girin:").pack()
        self.password_entry = ttk.Entry(self.password_frame, show="*")
        self.password_entry.pack(pady=5, fill=tk.X)
        
        self.password_button = ttk.Button(self.password_frame, text="Giriş", command=self.check_password)
        self.password_button.pack(pady=5)
        
        # Ayarlar paneli (başlangıçta gizli)
        self.settings_frame = ttk.LabelFrame(self, text="API Ayarları")
        
        ttk.Label(self.settings_frame, text="Authentication Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.auth_key_entry = ttk.Entry(self.settings_frame, width=50)
        self.auth_key_entry.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)
        
        ttk.Label(self.settings_frame, text="Referer:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.referer_entry = ttk.Entry(self.settings_frame)
        self.referer_entry.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        
        ttk.Label(self.settings_frame, text="Origin:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.origin_entry = ttk.Entry(self.settings_frame)
        self.origin_entry.grid(row=2, column=1, sticky=tk.EW, pady=2, padx=5)
        
        self.save_button = ttk.Button(self.settings_frame, text="Kaydet", command=self.save_settings)
        self.save_button.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Şifre doğruysa ayarları yükle
        if self.settings.get("authenticated", False):
            self.show_settings()
    
    def load_settings(self):
        default_settings = {
            "auth_key": "5bb38a3120522e0c9342c9253343989e2e7a40bf551d819c0bc16cb21348928e",
            "referer": "https://backoffice.betconstruct.com/",
            "origin": "https://backoffice.betconstruct.com",
            "authenticated": False
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    return json.load(f)
        except:
            pass
            
        return default_settings
    
    def check_password(self):
        if self.password_entry.get() == "Omlet2025?":
            self.settings["authenticated"] = True
            self.show_settings()
        else:
            messagebox.showerror("Hata", "Yanlış şifre!")
    
    def show_settings(self):
        self.password_frame.pack_forget()
        self.settings_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Ayarları entry'lere yükle
        self.auth_key_entry.delete(0, tk.END)
        self.auth_key_entry.insert(0, self.settings.get("auth_key", ""))
        
        self.referer_entry.delete(0, tk.END)
        self.referer_entry.insert(0, self.settings.get("referer", ""))
        
        self.origin_entry.delete(0, tk.END)
        self.origin_entry.insert(0, self.settings.get("origin", ""))
    
    def save_settings(self):
        self.settings.update({
            "auth_key": self.auth_key_entry.get(),
            "referer": self.referer_entry.get(),
            "origin": self.origin_entry.get(),
            "authenticated": True
        })
        
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f)
        
        self.parent.update_api_settings(self.settings)
        messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
        self.destroy()

class BonusReportApp:
    def __init__(self):
        self.window = ThemedTk(theme="arc")
        self.window.title("BetConstruct Bonus Raporu")
        self.window.geometry("1200x800")
        self.window.minsize(1000, 600)
        
        # Stiller
        self.title_font = tkfont.Font(family="Arial", size=16, weight="bold")
        self.label_font = tkfont.Font(family="Arial", size=12)
        self.button_font = tkfont.Font(family="Arial", size=11)
        
        # Menü Çubuğu
        self.create_menu()
        
        # Ana içerik
        self.create_main_content()
        
        # API Ayarları
        self.settings_window = None
        self.api_settings = {
            "bonus_api_url": "https://backofficewebadmin.betconstruct.com/api/tr/Report/GetClientBonusReport",
            "headers": {
                "Authentication": "5bb38a3120522e0c9342c9253343989e2e7a40bf551d819c0bc16cb21348928e",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://backoffice.betconstruct.com/",
                "Origin": "https://backoffice.betconstruct.com",
                "X-Requested-With": "XMLHttpRequest"
            }
        }
        
        # Excel için veri listesi
        self.bonus_data = []
        
        # Ayarları yükle
        self.load_settings()
        
        self.window.mainloop()
    
    def create_menu(self):
        menubar = tk.Menu(self.window)
        
        # Dosya menüsü
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Excel'e Kaydet", command=self.save_bonus_to_excel)
        file_menu.add_command(label="Temizle", command=self.clear_results)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.window.quit)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        
        # Ayarlar menüsü
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="API Ayarları", command=self.open_settings)
        menubar.add_cascade(label="Ayarlar", menu=settings_menu)
        
        self.window.config(menu=menubar)
    
    def create_main_content(self):
        # Ana çerçeve
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlık
        ttk.Label(main_frame, text="BetConstruct Bonus Raporu", 
                 font=self.title_font).pack(pady=10)
        
        # Açıklama
        ttk.Label(main_frame, text="Tarih aralığını seçin ve o dönemde alınan tüm bonusları görüntüleyin.", 
                 font=self.label_font).pack(pady=5)
        
        # Filtreler
        filter_frame = ttk.LabelFrame(main_frame, text="Filtreler", padding=10)
        filter_frame.pack(fill=tk.X, pady=5)
        
        # İlk satır - Tarih aralığı
        row1_frame = ttk.Frame(filter_frame)
        row1_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1_frame, text="Başlangıç Tarihi:").pack(side=tk.LEFT, padx=5)
        self.start_date = ttk.Entry(row1_frame, width=12)
        self.start_date.pack(side=tk.LEFT, padx=2)
        self.start_date_btn = ttk.Button(row1_frame, text="📅", width=3, command=lambda: self.open_calendar('start'))
        self.start_date_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(row1_frame, text="Bitiş Tarihi:").pack(side=tk.LEFT, padx=5)
        self.end_date = ttk.Entry(row1_frame, width=12)
        self.end_date.pack(side=tk.LEFT, padx=2)
        self.end_date_btn = ttk.Button(row1_frame, text="📅", width=3, command=lambda: self.open_calendar('end'))
        self.end_date_btn.pack(side=tk.LEFT, padx=2)
        
        # Varsayılan tarih aralığını ayarla (son 7 gün)
        today = datetime.now()
        start_date = today - timedelta(days=7)
        
        start_format = start_date.strftime("%d-%m-%y")
        end_format = today.strftime("%d-%m-%y")
        
        self.start_date.insert(0, start_format)
        self.end_date.insert(0, end_format)
        
        # İkinci satır - İsteğe bağlı filtreler
        row2_frame = ttk.Frame(filter_frame)
        row2_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2_frame, text="Kullanıcı ID (isteğe bağlı):").pack(side=tk.LEFT, padx=5)
        self.client_id = ttk.Entry(row2_frame, width=15)
        self.client_id.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2_frame, text="Bonus Türü:").pack(side=tk.LEFT, padx=5)
        bonus_types = ["Tüm Bonuslar", "%10 ÇEVRİMSİZ SPOR BONUSU", "%100  SLOT BONUSU", 
                      "%100 CASİNO HOŞGELDİN BONUSU", "%100 PRAGMATİC SALI - PERŞEMBE",
                      "%100 SPOR HOŞGELDİN BONUSU", "%25 SPOR YATIRIM BONUSU", 
                      "%5 CASİNO HAFTALIK", "%5 SPOR HAFTALIK", "250 TL CASİNO DENEME BONUSU",
                      "250 TL DOĞUM GÜNÜ CASİNO BONUSU", "250 TL SPOR DENEME BONUSU",
                      "CASİNO BAĞLILIK BONUSU", "CASİNO CALL DAVET", "CASİNO ÇEVRİMSİZ BONUS",
                      "CASİNO DOĞUM GÜNÜ BONUSU", "CASİNO KAYIP BONUSU", 
                      "P.TESİ & ÇARŞAMBA %100 GÜNÜN İLK KAYIBINA", "SPOR BAĞLILIK BONUSU",
                      "SPOR CALL DAVET", "SPOR ÇEVRİMSİZ BONUS", "SPOR DOĞUM GÜNÜ BONUSU",
                      "SPOR KAYIP BONUSU", "YENİ CASİNO ŞANS BONUSU"]
        self.bonus_type_combo = ttk.Combobox(row2_frame, values=bonus_types, state="readonly", width=25)
        self.bonus_type_combo.set("Tüm Bonuslar")
        self.bonus_type_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2_frame, text="Maksimum Kayıt:").pack(side=tk.LEFT, padx=5)
        self.max_rows = ttk.Entry(row2_frame, width=8)
        self.max_rows.pack(side=tk.LEFT, padx=5)
        self.max_rows.insert(0, "100")
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.fetch_btn = ttk.Button(button_frame, text="Bonus Raporunu Getir", command=self.fetch_bonus_report)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(button_frame, text="Excel'e Kaydet", command=self.save_bonus_to_excel)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        self.save_btn.config(state=tk.DISABLED)
        
        self.summary_btn = ttk.Button(button_frame, text="Özet Rapor Oluştur", command=self.create_summary_report)
        self.summary_btn.pack(side=tk.LEFT, padx=5)
        self.summary_btn.config(state=tk.DISABLED)
        
        self.clear_btn = ttk.Button(button_frame, text="Temizle", command=self.clear_results)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Sonuçlar Alanı
        results_frame = ttk.LabelFrame(main_frame, text="Bonus Raporu", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview (tablo) oluştur
        self.create_results_treeview(results_frame)
        
        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def create_results_treeview(self, parent):
        # Treeview ve scrollbar için çerçeve
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sütunlar tanımla
        columns = ("Kullanıcı ID", "Kullanıcı Adı", "Bonus ID", "Bonus Türü", "Miktar", "Para Birimi", "Durum", "Tarih")
        
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # Sütun başlıklarını ayarla
        column_widths = {
            "Kullanıcı ID": 100,
            "Kullanıcı Adı": 150,
            "Bonus ID": 80,
            "Bonus Türü": 200,
            "Miktar": 100,
            "Para Birimi": 80,
            "Durum": 100,
            "Tarih": 150
        }
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=column_widths[col], minwidth=60)
        
        # Scrollbar ekle
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        
        self.results_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Yerleştir
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    def open_calendar(self, date_type):
        """Takvim açıp tarih seçimini sağlar"""
        calendar_window = tk.Toplevel(self.window)
        calendar_window.title("Tarih Seç")
        calendar_window.geometry("300x250")
        calendar_window.resizable(False, False)
        
        # Takvim widget'ı
        import calendar as cal
        
        # Şu anki tarihi al
        now = datetime.now()
        
        # Yıl ve ay seçimi
        year_month_frame = ttk.Frame(calendar_window)
        year_month_frame.pack(pady=10)
        
        ttk.Label(year_month_frame, text="Yıl:").pack(side=tk.LEFT, padx=5)
        year_var = tk.StringVar(value=str(now.year))
        year_combo = ttk.Combobox(year_month_frame, textvariable=year_var, width=6)
        year_combo['values'] = [str(y) for y in range(2020, now.year + 2)]
        year_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(year_month_frame, text="Ay:").pack(side=tk.LEFT, padx=5)
        month_var = tk.StringVar(value=str(now.month))
        month_combo = ttk.Combobox(year_month_frame, textvariable=month_var, width=4)
        month_combo['values'] = [str(m) for m in range(1, 13)]
        month_combo.pack(side=tk.LEFT, padx=5)
        
        # Takvim gösterimi
        calendar_frame = ttk.Frame(calendar_window)
        calendar_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Günler için butonlar
        self.day_buttons = []
        
        def update_calendar():
            # Önceki butonları temizle
            for btn in self.day_buttons:
                btn.destroy()
            self.day_buttons.clear()
            
            year = int(year_var.get())
            month = int(month_var.get())
            
            # Haftanın günleri
            days = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
            for i, day in enumerate(days):
                ttk.Label(calendar_frame, text=day, font=('Arial', 8, 'bold')).grid(row=0, column=i, padx=1, pady=1)
            
            # Ayın günleri
            month_calendar = cal.monthcalendar(year, month)
            for week_num, week in enumerate(month_calendar, 1):
                for day_num, day in enumerate(week):
                    if day == 0:
                        continue
                    
                    btn = ttk.Button(calendar_frame, text=str(day), width=3,
                                   command=lambda d=day: select_date(d))
                    btn.grid(row=week_num, column=day_num, padx=1, pady=1)
                    self.day_buttons.append(btn)
        
        def select_date(day):
            year = int(year_var.get())
            month = int(month_var.get())
            selected_date = datetime(year, month, day)
            formatted_date = selected_date.strftime("%d-%m-%y")
            
            if date_type == 'start':
                self.start_date.delete(0, tk.END)
                self.start_date.insert(0, formatted_date)
            else:
                self.end_date.delete(0, tk.END)
                self.end_date.insert(0, formatted_date)
            
            calendar_window.destroy()
        
        # İlk takvimi göster
        update_calendar()
        
        # Ay/yıl değiştiğinde takvimi güncelle
        year_combo.bind('<<ComboboxSelected>>', lambda e: update_calendar())
        month_combo.bind('<<ComboboxSelected>>', lambda e: update_calendar())
    
    def fetch_bonus_report(self):
        try:
            # Butonları devre dışı bırak
            self.fetch_btn.config(state=tk.DISABLED)
            self.status_var.set("Bonus raporu çekiliyor...")
            self.window.update_idletasks()
            
            # Tabloyu temizle
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Parametreleri al ve kontrol et
            start_date = self.start_date.get().strip()
            end_date = self.end_date.get().strip()
            client_id = self.client_id.get().strip()
            bonus_type = self.bonus_type_combo.get()
            max_rows = self.max_rows.get().strip()
            
            if not start_date or not end_date:
                messagebox.showerror("Hata", "Lütfen başlangıç ve bitiş tarihlerini girin!")
                return
            
            # Tarih formatını kontrol et ve düzelt
            try:
                start_dt = datetime.strptime(start_date, "%d-%m-%y")
                end_dt = datetime.strptime(end_date, "%d-%m-%y")
                
                # API için uygun formata çevir
                start_formatted = start_dt.strftime("%d-%m-%y - 00:00:00")
                end_formatted = end_dt.strftime("%d-%m-%y - 23:59:59")
                
            except ValueError:
                messagebox.showerror("Hata", "Tarih formatı hatalı! Lütfen dd-mm-yy formatında girin (örn: 21-07-25)")
                return
            
            # Maksimum kayıt sayısını kontrol et
            try:
                max_rows_int = int(max_rows) if max_rows else 100
                if max_rows_int <= 0:
                    max_rows_int = 100
            except ValueError:
                max_rows_int = 100
            
            # Request payload'u oluştur
            payload = {
                "ClientBonusId": "",
                "ClientId": client_id if client_id else "",
                "PartnerBonusId": "",
                "AcceptanceType": None,
                "BonusType": "1" if bonus_type == "Casino Kayıp Bonusu" else None,
                "BonusSource": None,
                "ByPassTotals": False,
                "EndDateLocal": None,
                "IsTest": None,
                "MaxRows": max_rows_int,
                "PartnerBonusEndDateLocal": end_formatted,
                "PartnerBonusStartDateLocal": start_formatted,
                "ResultFromDateLocal": None,
                "ResultToDateLocal": None,
                "ResultType": None,
                "SkeepRows": 0,
                "SportsbookProfileId": None,
                "StartDateLocal": None,
                "ToCurrencyId": "TRY"
            }
            
            # API çağrısı yap
            response = requests.post(
                self.api_settings["bonus_api_url"], 
                headers=self.api_settings["headers"], 
                json=payload
            )
            
            if response.status_code == 200:
                try:
                    # API yanıtını kontrol et
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' not in content_type:
                        error_msg = f"API yanıtı JSON formatında değil. Content-Type: {content_type}\nYanıt: {response.text[:500]}"
                        self.status_var.set("API yanıt formatı hatası.")
                        messagebox.showerror("Format Hatası", error_msg)
                        return
                    
                    data = response.json()
                    
                    # API yanıt kontrolü
                    if data.get('HasError', False):
                        error_msg = f"API Hatası: {data.get('AlertMessage', 'Bilinmeyen hata')}"
                        self.status_var.set("API hatası.")
                        messagebox.showerror("API Hatası", error_msg)
                        return
                    
                    # BetConstruct API yanıt yapısına göre bonus listesini al
                    bonus_list = None
                    
                    if isinstance(data, dict) and "Data" in data:
                        data_obj = data["Data"]
                        if isinstance(data_obj, dict) and "ClientBonusReportData" in data_obj:
                            bonus_report_data = data_obj["ClientBonusReportData"]
                            if isinstance(bonus_report_data, dict) and "Objects" in bonus_report_data:
                                bonus_list = bonus_report_data["Objects"]
                    
                    if bonus_list and len(bonus_list) > 0:
                        self.bonus_data = []
                        
                        for bonus in bonus_list:
                            if isinstance(bonus, dict):
                                # API yanıtından doğru alan isimlerini kullan
                                client_id = str(bonus.get("ClientId", ""))
                                client_login = str(bonus.get("ClientName", ""))  # ClientName alanı kullanıcı adını içeriyor
                                bonus_id = str(bonus.get("Id", ""))  # Id alanı bonus ID'si
                                bonus_name = str(bonus.get("Name", ""))  # Name alanı bonus türünü içeriyor
                                amount = float(bonus.get("Amount", 0))
                                currency = str(bonus.get("ClientCurrency", "TRY"))  # ClientCurrency alanı para birimini içeriyor
                                acceptance_type = bonus.get("AcceptanceType", 0)
                                creation_time = str(bonus.get("AcceptanceDateLocal", ""))  # AcceptanceDateLocal kabul tarihini içeriyor
                                
                                # Bonus türü filtrelemesi
                                if bonus_type != "Tüm Bonuslar":
                                    if bonus_name.strip().upper() != bonus_type.upper():
                                        continue
                                
                                # Treeview'a ekle
                                self.results_tree.insert("", "end", values=(
                                    str(client_id),
                                    str(client_login),
                                    str(bonus_id),
                                    str(bonus_name),
                                    f"{float(amount):.2f}",
                                    str(currency),
                                    self.get_bonus_status(acceptance_type),
                                    str(creation_time)
                                ))
                                
                                # Excel için veriyi sakla
                                self.bonus_data.append({
                                    "Kullanıcı ID": str(client_id),
                                    "Kullanıcı Adı": str(client_login),
                                    "Bonus ID": str(bonus_id),
                                    "Bonus Türü": str(bonus_name),
                                    "Miktar": float(amount),
                                    "Para Birimi": str(currency),
                                    "Durum": self.get_bonus_status(acceptance_type),
                                    "Tarih": str(creation_time)
                                })
                        
                        # Filtreleme sonrası kayıt sayısını güncelle
                        filtered_count = len(self.bonus_data)
                        self.status_var.set(f"Toplam {filtered_count} bonus kaydı bulundu.")
                        self.save_btn.config(state=tk.NORMAL)
                        self.summary_btn.config(state=tk.NORMAL)
                        
                    else:
                        self.status_var.set("Belirtilen kriterlerde bonus kaydı bulunamadı.")
                        messagebox.showinfo("Bilgi", f"Belirtilen kriterlerde bonus kaydı bulunamadı.\nAPI Yanıtı: {str(data)[:200]}")
                        
                except json.JSONDecodeError as e:
                    error_msg = f"JSON decode hatası: {str(e)}\nYanıt: {response.text[:500]}"
                    self.status_var.set("JSON decode hatası.")
                    messagebox.showerror("JSON Hatası", error_msg)
            else:
                error_msg = f"API Hatası: {response.status_code}"
                if response.text:
                    error_msg += f"\nDetay: {response.text[:500]}"
                
                self.status_var.set("API hatası oluştu.")
                messagebox.showerror("API Hatası", error_msg)
                
        except Exception as e:
            error_msg = f"Bonus raporu çekilirken hata oluştu:\n{str(e)}"
            self.status_var.set("Hata oluştu.")
            messagebox.showerror("Hata", error_msg)
            
        finally:
            # Butonları yeniden etkinleştir
            self.fetch_btn.config(state=tk.NORMAL)
    
    def get_bonus_status(self, acceptance_type):
        """Bonus durumunu açıklayıcı metne çevir"""
        status_map = {
            0: "Beklemede",
            1: "Onaylandı",
            2: "Reddedildi",
            3: "İptal Edildi",
            4: "Kullanıldı"
        }
        return status_map.get(acceptance_type, "Bilinmiyor")
    
    def get_user_details(self, client_id):
        """Kullanıcı ID'si ile kullanıcı detaylarını getir"""
        if not client_id:
            return None
        
        try:
            user_url = f"https://backofficewebadmin.betconstruct.com/api/tr/Client/GetClientById?id={client_id}"
            response = requests.get(user_url, headers=self.api_settings["headers"])
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "Data" in data:
                    user_data = data["Data"]
                    return {
                        "username": user_data.get("UserName", ""),
                        "firstName": user_data.get("FirstName", ""),
                        "lastName": user_data.get("LastName", ""),
                        "email": user_data.get("Email", "")
                    }
        except Exception as e:
            print(f"Kullanıcı detayı çekilirken hata: {e}")
        
        return None
    
    def create_summary_report(self):
        """Seçilen bonus türü için özet rapor oluştur"""
        if not self.bonus_data:
            messagebox.showwarning("Uyarı", "Özet rapor için veri yok!")
            return
        
        try:
            # Özet rapor penceresi oluştur
            summary_window = tk.Toplevel(self.window)
            summary_window.title("Bonus Özet Raporu")
            summary_window.geometry("800x600")
            
            # Başlık
            selected_bonus = self.bonus_type_combo.get()
            ttk.Label(summary_window, text=f"Bonus Özet Raporu: {selected_bonus}", 
                     font=self.title_font).pack(pady=10)
            
            # Özet rapor tablosu
            columns = ("Üye ID", "Kullanıcı Adı", "Alım Sayısı", "Bonus Türü", "Toplam Bonus")
            
            summary_frame = ttk.Frame(summary_window)
            summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            summary_tree = ttk.Treeview(summary_frame, columns=columns, show="headings", height=20)
            
            # Sütun başlıklarını ayarla
            for col in columns:
                summary_tree.heading(col, text=col)
                summary_tree.column(col, width=150, minwidth=100)
            
            # Scrollbar ekle
            scrollbar = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=summary_tree.yview)
            summary_tree.configure(yscrollcommand=scrollbar.set)
            
            summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Veriyi grupla ve özetle
            summary_data = {}
            for bonus in self.bonus_data:
                user_id = bonus["Kullanıcı ID"]
                bonus_type = bonus["Bonus Türü"]
                amount = bonus["Miktar"]
                user_name = bonus["Kullanıcı Adı"]
                
                key = (user_id, bonus_type)
                if key not in summary_data:
                    summary_data[key] = {
                        "user_id": user_id,
                        "user_name": user_name,
                        "bonus_type": bonus_type,
                        "count": 0,
                        "total_amount": 0
                    }
                
                summary_data[key]["count"] += 1
                summary_data[key]["total_amount"] += amount
            
            # Özet tablosuna veri ekle
            for data in summary_data.values():
                summary_tree.insert("", "end", values=(
                    data["user_id"],
                    data["user_name"],
                    data["count"],
                    data["bonus_type"],
                    f"{data['total_amount']:.2f} TL"
                ))
            
            # Excel'e kaydet butonu
            button_frame = ttk.Frame(summary_window)
            button_frame.pack(fill=tk.X, pady=10, padx=10)
            
            def save_summary():
                try:
                    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = filedialog.asksaveasfilename(
                        defaultextension=".xlsx",
                        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                        title="Özet raporu kaydet",
                        initialfile=f"bonus_ozet_{date_str}.xlsx"
                    )
                    
                    if filename:
                        summary_df = pd.DataFrame([
                            {
                                "Üye ID": data["user_id"],
                                "Kullanıcı Adı": data["user_name"],
                                "Alım Sayısı": data["count"],
                                "Bonus Türü": data["bonus_type"],
                                "Toplam Bonus": data["total_amount"]
                            }
                            for data in summary_data.values()
                        ])
                        summary_df.to_excel(filename, index=False)
                        messagebox.showinfo("Başarılı", f"Özet rapor {filename} dosyasına kaydedildi!")
                        
                except Exception as e:
                    messagebox.showerror("Hata", f"Özet rapor kaydedilirken hata oluştu: {str(e)}")
            
            ttk.Button(button_frame, text="Özet Raporu Excel'e Kaydet", command=save_summary).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Kapat", command=summary_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Özet rapor oluşturulurken hata oluştu: {str(e)}")
    
    def save_bonus_to_excel(self):
        if not self.bonus_data:
            messagebox.showwarning("Uyarı", "Kaydedilecek bonus verisi yok!")
            return
        
        try:
            # Dosya adı önerisi
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Bonus raporunu kaydet",
                initialfile=f"bonus_raporu_{date_str}.xlsx"
            )
            
            if filename:
                df = pd.DataFrame(self.bonus_data)
                df.to_excel(filename, index=False)
                messagebox.showinfo("Başarılı", f"Bonus raporu {filename} dosyasına kaydedildi!")
                self.status_var.set(f"Rapor {os.path.basename(filename)} dosyasına kaydedildi.")
                
        except Exception as e:
            messagebox.showerror("Hata", f"Excel dosyası kaydedilirken hata oluştu: {str(e)}")
    
    def clear_results(self):
        # Tabloyu temizle
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Veri listesini temizle
        self.bonus_data = []
        
        # Durum çubuğunu sıfırla
        self.status_var.set("Hazır")
        
        # Kaydet ve özet butonlarını devre dışı bırak
        self.save_btn.config(state=tk.DISABLED)
        self.summary_btn.config(state=tk.DISABLED)
    
    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.lift()
    
    def update_api_settings(self, settings):
        self.api_settings["headers"]["Authentication"] = settings["auth_key"]
        self.api_settings["headers"]["Referer"] = settings["referer"]
        self.api_settings["headers"]["Origin"] = settings["origin"]
    
    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    self.update_api_settings(settings)
        except:
            pass

if __name__ == "__main__":
    app = BonusReportApp()


if __name__ == "__main__":
    main()
