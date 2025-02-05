import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from tkcalendar import DateEntry
from datetime import datetime
import requests
import pyperclip
import threading
import re
import os
import sys

class RaporOlusturucu:
    def __init__(self, root):
        self.root = root
        self.root.title("Rapor Oluşturucu")
        self.root.geometry("500x600")

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(side="top", fill="x")

        self.rapor_button = tk.Button(self.button_frame, text="Rapor", command=self.show_rapor_page)
        self.rapor_button.pack(side="left")

        self.kyc_button = tk.Button(self.button_frame, text="KYC", command=self.show_kyc_page)
        self.kyc_button.pack(side="left")

        self.mcek_button = tk.Button(self.button_frame, text="M.Çek", command=self.show_mcek_page)
        self.mcek_button.pack(side="left")

        self.cevrim_button = tk.Button(self.button_frame, text="Ç.Hesapla", command=self.show_cevrim_page)
        self.cevrim_button.pack(side="left")

        self.current_page = None

        self.rapor_page = tk.Frame(self.main_frame)
        self.create_rapor_page(self.rapor_page)

        self.kyc_page = tk.Frame(self.main_frame)
        self.create_kyc_page(self.kyc_page)

        self.mcek_page = tk.Frame(self.main_frame)
        self.create_mcek_page(self.mcek_page)

        self.cevrim_page = tk.Frame(self.main_frame)
        self.create_cevrim_page(self.cevrim_page)

        self.show_rapor_page()

    def create_rapor_page(self, frame):
        self.isim_soyisim = ""
        self.kullanici_adi = ""
        self.talep_miktari = ""
        self.talep_yontemi = ""
        self.yatirim_miktari = ""
        self.toplam_yatirim = ""
        self.toplam_cekim = ""
        self.toplam_cekim_adedi = ""
        self.oyun_turu = ""
        self.arka_bakiye = ""
        self.aciklama = ""
        self.oynamaya_devam = "Etmiyor"

        self.clipboard_izleme = False

        self.title_label = tk.Label(frame, text="Rapor Oluşturucu", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)

        self.button_frame = tk.Frame(frame)
        self.button_frame.pack(pady=10)

        self.calistir_buton = tk.Button(self.button_frame, text="Çalıştır", width=15, command=self.calistir)
        self.calistir_buton.grid(row=0, column=0, padx=5)

        self.guncelle_buton = tk.Button(self.button_frame, text="Raporu Güncelle", width=15, command=self.raporu_guncelle)
        self.guncelle_buton.grid(row=0, column=1, padx=5)

        self.kopyala_buton = tk.Button(self.button_frame, text="Raporu Kopyala", width=15, command=self.raporu_kopyala)
        self.kopyala_buton.grid(row=0, column=2, padx=5)

        self.temizle_buton = tk.Button(self.button_frame, text="Raporu Temizle", width=15, command=self.raporu_temizle)
        self.temizle_buton.grid(row=0, column=3, padx=5)

        self.report_text = scrolledtext.ScrolledText(frame, width=100, height=15)
        self.report_text.pack(pady=10)

        self.bottom_frame = tk.Frame(frame)
        self.bottom_frame.pack(pady=10)

        tk.Label(self.bottom_frame, text="Oyun Türü:").grid(row=0, column=0, padx=5, sticky="w")
        self.game_type_var = tk.StringVar()
        game_types = ["Casino", "Canlı Casino", "Rulet", "Spor", "Tek Maç", "Çapraz Bahis", "Kurmaca"]

        for idx, game in enumerate(game_types):
            tk.Radiobutton(self.bottom_frame, text=game, variable=self.game_type_var, value=game).grid(row=0 + (idx // 4), column=1 + (idx % 4), padx=5, sticky="w")

        tk.Label(self.bottom_frame, text="Arka Bakiye:").grid(row=2, column=0, padx=5, sticky="w")
        self.arka_bakiye_entry = tk.Entry(self.bottom_frame, width=50)
        self.arka_bakiye_entry.grid(row=2, column=1, columnspan=3, padx=5, sticky="w")

        tk.Label(self.bottom_frame, text="Açıklama:").grid(row=3, column=0, padx=5, sticky="w")
        self.description_entry = tk.Entry(self.bottom_frame, width=50)
        self.description_entry.grid(row=3, column=1, columnspan=3, padx=5, sticky="w")

        tk.Label(self.bottom_frame, text="Oynamaya Devam Ediyor mu?").grid(row=4, column=0, padx=5, sticky="w")
        self.play_status_var = tk.StringVar(value="Seçilmedi")
        tk.Radiobutton(self.bottom_frame, text="Evet", variable=self.play_status_var, value="Ediyor").grid(row=4, column=1, padx=5, sticky="w")
        tk.Radiobutton(self.bottom_frame, text="Hayır", variable=self.play_status_var, value="Etmiyor").grid(row=4, column=2, padx=5, sticky="w")

    def create_kyc_page(self, frame):
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)

        def yapistir():
            clipboard_content = pyperclip.paste()
            try:
                lines = clipboard_content.strip().split("\n")
                if len(lines) > 4:
                    ad_entry.delete(0, tk.END)
                    ad_entry.insert(0, lines[0].strip())
                    soyad_entry.delete(0, tk.END)
                    soyad_entry.insert(0, lines[1].strip())
                    dogum_tarihi_entry.delete(0, tk.END)
                    dogum_tarihi_entry.insert(0, lines[2].strip())
                    tc_entry.delete(0, tk.END)
                    tc_entry.insert(0, lines[4].strip())
                else:
                    messagebox.showwarning("Eksik Veri", "Panodaki veri eksik veya yanlış formatta.")
            except Exception as e:
                messagebox.showerror("Hata", f"Panodan veri alırken bir hata oluştu: {e}")

        def dogrula():
            tc = tc_entry.get().strip()
            ad = ad_entry.get().strip()
            soyad = soyad_entry.get().strip()
            dogum_tarihi = dogum_tarihi_entry.get().strip()

            if not (tc and ad and soyad and dogum_tarihi):
                messagebox.showwarning("Eksik Bilgi", "Lütfen tüm alanları doldurunuz.")
                return

            if not tc.isdigit() or len(tc) != 11:
                messagebox.showwarning("Hatalı Giriş", "TC Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır.")
                return

            if len(dogum_tarihi.split("-")) != 3:
                messagebox.showwarning("Hatalı Giriş", "Doğum tarihi formatı 'YYYY-MM-DD' şeklinde olmalıdır.")
                return

            url = "https://tc-kimlik.vercel.app/api/dogrula"
            data = {
                "tc": tc,
                "ad": ad,
                "soyad": soyad,
                "dogumTarihi": dogum_tarihi
            }

            try:
                response = requests.post(url, json=data)
                response.raise_for_status()
                try:
                    result = response.json()
                except ValueError:
                    messagebox.showerror("Hata", "Sunucudan geçersiz yanıt alındı.")
                    return

                if result.get("result"):
                    sonuc_label.config(text="✅ Doğrulama Başarılı!", fg="green")
                else:
                    sonuc_label.config(text="❌ Doğrulama Başarısız!", fg="red")
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Hata", f"Sunucuya bağlanırken bir hata oluştu: {e}")

        def temizle():
            tc_entry.delete(0, tk.END)
            ad_entry.delete(0, tk.END)
            soyad_entry.delete(0, tk.END)
            dogum_tarihi_entry.delete(0, tk.END)
            sonuc_label.config(text="")

        tk.Label(frame, text="TC Kimlik Doğrulama", font=("Arial", 16, "bold")).pack(pady=10)

        form_frame = tk.Frame(frame)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="TC Kimlik No:").grid(row=0, column=0, padx=10, pady=5)
        tc_entry = tk.Entry(form_frame)
        tc_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Ad:").grid(row=1, column=0, padx=10, pady=5)
        ad_entry = tk.Entry(form_frame)
        ad_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Soyad:").grid(row=2, column=0, padx=10, pady=5)
        soyad_entry = tk.Entry(form_frame)
        soyad_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Doğum Tarihi (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=5)
        dogum_tarihi_entry = tk.Entry(form_frame)
        dogum_tarihi_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Button(form_frame, text="Panodan Yapıştır", command=yapistir).grid(row=4, column=0, pady=10)
        tk.Button(form_frame, text="Doğrula", command=dogrula).grid(row=4, column=1, pady=10)
        tk.Button(form_frame, text="Temizle", command=temizle).grid(row=5, column=0, columnspan=2, pady=10)

        sonuc_label = tk.Label(form_frame, text="", font=("Arial", 12))
        sonuc_label.grid(row=6, column=0, columnspan=2, pady=10)

        tk.Label(frame, text="Powered by ©Selim ☺", fg="grey").place(relx=0.5, rely=1.0, anchor="s", y=-10)

    def create_mcek_page(self, frame):
        self.mcek = ManuelCekimHazirla(frame)

    def create_cevrim_page(self, frame):
        self.cevrim = CevrimHesaplayici(frame)

    def show_rapor_page(self):
        if self.current_page:
            self.current_page.pack_forget()
        self.rapor_page.pack(fill="both", expand=True)
        self.current_page = self.rapor_page

    def show_kyc_page(self):
        if self.current_page:
            self.current_page.pack_forget()
        self.kyc_page.pack(fill="both", expand=True)
        self.current_page = self.kyc_page

    def show_mcek_page(self):
        if self.current_page:
            self.current_page.pack_forget()
        self.mcek_page.pack(fill="both", expand=True)
        self.current_page = self.mcek_page

    def show_cevrim_page(self):
        if self.current_page:
            self.current_page.pack_forget()
        self.cevrim_page.pack(fill="both", expand=True)
        self.current_page = self.cevrim_page

    def calistir(self):
        self.root.clipboard_clear()
        self.clipboard_izleme = True
        self.calistir_buton.config(text="Durdur")
        threading.Thread(target=self.clipboard_izle, daemon=True).start()

    def clipboard_izle(self):
        son_clipboard_verisi = ""
        while self.clipboard_izleme:
            try:
                clipboard_verisi = self.root.clipboard_get()
                if clipboard_verisi != son_clipboard_verisi:
                    son_clipboard_verisi = clipboard_verisi
                    self.veriyi_isle(clipboard_verisi)
            except tk.TclError:
                pass
            self.root.after(1000, self.clipboard_izle)
            break

    def veriyi_isle(self, veri):
        if self.is_first_copy(veri):
            self.birinci_kisim_isle(veri)
        else:
            self.ikinci_kopya_isle(veri)
            self.clipboard_izleme = False
            self.calistir_buton.config(text="Çalıştır")

    def is_first_copy(self, veri):
        odeme_yontemleri = [
            "Aninda_KrediKarti", "Aninda_Mefete", "Aninda_Parazula", "AnindaHavale", "AnindaKrediKarti", "AnindaQR",
            "AtikOdemeHavale", "AtikOdemeOtoPapara", "CepPay", "Fixturka", "FulgurPay", "FulgurPayBNBB", "FulgurPayBTC",
            "FulgurPayETH", "FulgurPayFTN", "FulgurPayLTC", "FulgurPayTRX", "FulgurPayUSDB", "FulgurPayUSDT",
            "FulgurPayUSDT_T", "HedefHavale", "Hemen", "HemenMefete", "HemenVipPayFix", "MiniPayHavale",
            "MiniPayPapara", "ScashMoneyBankTransfer", "ScashMoneyFast", "ScashMoneyFixturka", "ScashMoneyPapara",
            "UltraPayV1AutoPapara", "UltraPayV1Payfix", "VipPapara", "VipParola", "BankTransferBME"
        ]
        return any(yontem in veri for yontem in odeme_yontemleri)

    def birinci_kisim_isle(self, veri):
        pattern = r"(\S+)\s+\d+\s+(\S+\s+\S+)\s+(\S+)\s+₺([\d,]+\.\d{2})"
        eslesme = re.search(pattern, veri)
        if eslesme:
            if eslesme.group(1) == "BankTransferBME":
                self.talep_yontemi = "Manuel Talep"
            else:
                self.talep_yontemi = eslesme.group(1)
            self.isim_soyisim = eslesme.group(2)
            self.kullanici_adi = eslesme.group(3)
            self.talep_miktari = "₺" + eslesme.group(4)
            self.raporu_guncelle()

    def ikinci_kopya_isle(self, veri):
        try:
            self.toplam_cekim_adedi = re.search(r"(\d+)$", veri).group(1)
            self.toplam_cekim = re.findall(r"₺([\d,]+\.\d{2})", veri)[-2]
            self.toplam_yatirim = re.search(r"%.*₺([\d,]+\.\d{2})₺", veri).group(1)
            self.yatirim_miktari = re.findall(r"₺([\d,]+\.\d{2})", veri)[-3]
            self.raporu_guncelle()
        except AttributeError:
            messagebox.showerror("Dikkatli ol!", "Spor Toplam Kazançlar yazan yer ile Para Çekme Sayısı yazan yer arasını kopyalamalısın")

    def raporu_guncelle(self):
        rapor = f"""
İsim Soyisim            :   {self.isim_soyisim}
K. Adı                  :   {self.kullanici_adi}
Talep Miktarı           :   {self.talep_miktari}
Talep yöntemi           :   {self.talep_yontemi}
Yatırım Miktarı         :   ₺{self.yatirim_miktari}
Oyun Türü               :   {self.game_type_var.get()}
Arka Bakiye             :   ₺{self.arka_bakiye_entry.get()}
Oyuna  Devam            :   {self.play_status_var.get()}

T. Yatırım Miktarı      :   ₺{self.toplam_yatirim}
T. Çekim Miktarı        :   ₺{self.toplam_cekim}
T. Çekim Adedi          :   {self.toplam_cekim_adedi}

Açıklama                :   {self.description_entry.get()}
"""
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, rapor)

    def raporu_kopyala(self):
        rapor = self.report_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(rapor)

    def raporu_temizle(self):
        self.isim_soyisim = ""
        self.kullanici_adi = ""
        self.talep_miktari = ""
        self.talep_yontemi = ""
        self.yatirim_miktari = ""
        self.toplam_yatirim = ""
        self.toplam_cekim = ""
        self.toplam_cekim_adedi = ""
        self.oyun_turu = ""
        self.arka_bakiye = ""
        self.aciklama = ""
        self.oynamaya_devam = "Seçilmedi"

        self.report_text.delete(1.0, tk.END)
        self.arka_bakiye_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.game_type_var.set("")
        self.play_status_var.set("Seçilmedi")

class ManuelCekimHazirla:
    def __init__(self, frame):
        self.frame = frame
        self.frame.pack(fill="both", expand=True)

        self.isim_soyisim = ""
        self.iban = ""
        self.banka = ""
        self.miktar = ""

        self.clipboard_izleme = False

        self.title_label = tk.Label(frame, text="Manuel Çekim Hazırla", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)

        self.button_frame = tk.Frame(frame)
        self.button_frame.pack(pady=10)

        self.calistir_buton = tk.Button(self.button_frame, text="Çalıştır", width=15, command=self.calistir)
        self.calistir_buton.grid(row=0, column=0, padx=5)

        self.kopyala_buton = tk.Button(self.button_frame, text="Raporu Kopyala", width=15, command=self.raporu_kopyala)
        self.kopyala_buton.grid(row=0, column=1, padx=5)

        self.temizle_buton = tk.Button(self.button_frame, text="Temizle", width=15, command=self.raporu_temizle)
        self.temizle_buton.grid(row=0, column=2, padx=5)

        self.report_text = scrolledtext.ScrolledText(frame, width=70, height=15)
        self.report_text.pack(pady=10)

    def calistir(self):
        self.frame.clipboard_clear()
        self.clipboard_izleme = True
        self.calistir_buton.config(text="Durdur")
        threading.Thread(target=self.clipboard_izle, daemon=True).start()

    def clipboard_izle(self):
        son_clipboard_verisi = ""
        while self.clipboard_izleme:
            try:
                clipboard_verisi = self.frame.clipboard_get()
                if clipboard_verisi != son_clipboard_verisi:
                    son_clipboard_verisi = clipboard_verisi
                    self.veriyi_isle(clipboard_verisi)
            except tk.TclError:
                pass
            self.frame.after(1000, self.clipboard_izle)
            break

    def veriyi_isle(self, veri):
        self.hesap_adi_isle(veri)
        self.iban_isle(veri)
        self.banka_isle(veri)
        self.miktar_isle(veri)
        self.raporu_guncelle()
        self.clipboard_izleme = False
        self.calistir_buton.config(text="Çalıştır")

    def hesap_adi_isle(self, veri):
        baslangic = re.search(r"Hesap Adi ve Soyadi:|Isim Soyisim:", veri)
        if baslangic:
            baslangic = baslangic.end()
            bitis = re.search(r",", veri[baslangic:])
            if bitis:
                self.isim_soyisim = veri[baslangic:baslangic + bitis.start()].strip()
            else:
                self.isim_soyisim = "Bulunamadı"
        else:
            self.isim_soyisim = "Bulunamadı"

    def iban_isle(self, veri):
        baslangic = re.search(r"Iban Numarasi:|IBAN Numarasi:|HESAP NO:|Payfix No:", veri)
        if baslangic:
            baslangic = baslangic.end()
            bitis = re.search(r",", veri[baslangic:])
            if bitis:
                self.iban = veri[baslangic:baslangic + bitis.start()].strip()
                if not self.iban.startswith("TR"):
                    self.iban = "TR" + self.iban
            else:
                self.iban = "Bulunamadı"
        else:
            self.iban = "Bulunamadı"

    def banka_isle(self, veri):
        baslangic = re.search(r"Banka Adi:", veri)
        if baslangic:
            baslangic = baslangic.end()
            bitis = re.search(r",", veri[baslangic:])
            if bitis:
                self.banka = veri[baslangic:baslangic + bitis.start()].strip()
            else:
                self.banka = "Bulunamadı"
        else:
            if re.search(r"PAPARA NO:", veri):
                self.banka = "Papara"
            elif re.search(r"PAYFIX", veri):
                self.banka = "PAYFIX"
            else:
                self.banka = "Bulunamadı"

    def miktar_isle(self, veri):
        baslangic = re.search(r"₺", veri)
        if baslangic:
            baslangic = baslangic.end()
            bitis = re.search(r".00", veri[baslangic:])
            if bitis:
                self.miktar = veri[baslangic:baslangic + bitis.start() + 3].strip()
                self.miktar = self.miktar.replace(",", "").replace(".", ",") + "₺"
            else:
                self.miktar = "Bulunamadı"
        else:
            self.miktar = "Bulunamadı"

    def raporu_guncelle(self):
        rapor = f"""
İsimSoyisim    :    {self.isim_soyisim}
İban           :    {self.iban}
Banka          :    {self.banka}
Miktar         :    {self.miktar}
"""
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, rapor)

    def raporu_kopyala(self):
        rapor = self.report_text.get(1.0, tk.END)
        self.frame.clipboard_clear()
        self.frame.clipboard_append(rapor)
        messagebox.showinfo("Bilgi", "Rapor panoya kopyalandı.")

    def raporu_temizle(self):
        self.isim_soyisim = ""
        self.iban = ""
        self.banka = ""
        self.miktar = ""

        self.report_text.delete(1.0, tk.END)

class CevrimHesaplayici:
    def __init__(self, frame):
        self.frame = frame
        # Remove the title setting line for frames
        # self.root.title("Çevrim Hesaplayıcı")
        self.frame.pack(fill="both", expand=True)

        self.clipboard_izleme = False
        self.bahis_verileri = {}
        self.bonus_kurallari = {
            "%100 Casino Hoşgeldin": {
                "minimum_yatirim": 50,
                "maksimum_yatirim": 1000,
                "cevrim_katsayisi": 10,
                "gecersiz_oyunlar": ["Plinko", "Aviatrix", "Zeppelin"],
                "oranli_oyunlar": {"Roulette": 0.2, "Blackjack": 0.2, "Baccarat": 0.1},
                "maksimum_cekim": 10000
            },
            "%25 FreeSpin Party Bonusu": {
                "minimum_yatirim": 100,
                "maksimum_freespin": 250,
                "cevrim_katsayisi": 5,
                "gecersiz_oyunlar": [],
                "freespin_oyunlari": ["SWEET BONANZA", "GATES OF OLYMPUS", "STARLIGHT PRINCESS"],
                "maksimum_cekim": 5000
            },
            "Turnuva Kazancı": {
                "cevrim_katsayisi": 1,
                "maksimum_cekim_katsayisi": 20,
                "cekim_suresi_gun": 7
            }
        }
        self.oranli_oyunlar = {"Roulette": 0.2, "Blackjack": 0.2, "Baccarat": 0.1}

        self.create_widgets()

    def create_widgets(self):
        self.title_label = tk.Label(self.frame, text="Çevrim Hesaplayıcı", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)

        self.input_frame = tk.Frame(self.frame)
        self.input_frame.pack(pady=10)

        tk.Label(self.input_frame, text="Yatırım Miktarı:").grid(row=0, column=0, padx=5)
        self.yatirim_entry = tk.Entry(self.input_frame)
        self.yatirim_entry.grid(row=0, column=1, padx=5)

        tk.Label(self.input_frame, text="Bonus:").grid(row=1, column=0, padx=5)
        self.bonus_var = tk.StringVar()
        self.bonus_menu = ttk.Combobox(self.input_frame, textvariable=self.bonus_var)
        self.bonus_menu['values'] = list(self.bonus_kurallari.keys())
        self.bonus_menu.grid(row=1, column=1, padx=5)
        self.bonus_menu.bind("<<ComboboxSelected>>", self.bonus_secildi)

        self.bonus_bakiye_label = tk.Label(self.input_frame, text="Bonus Bakiye:")
        self.bonus_bakiye_entry = tk.Entry(self.input_frame)

        self.freespin_label = tk.Label(self.input_frame, text="FreeSpin Kazancı:")
        self.freespin_entry = tk.Entry(self.input_frame)

        self.turnuva_kazanci_label = tk.Label(self.input_frame, text="Turnuva Kazanç Miktarı:")
        self.turnuva_kazanci_entry = tk.Entry(self.input_frame)

        self.kazanc_tarihi_label = tk.Label(self.input_frame, text="Kazanç Tarihi:")
        self.kazanc_tarihi_entry = DateEntry(self.input_frame, date_pattern='yyyy-mm-dd')

        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(pady=10)

        self.calistir_buton = tk.Button(self.button_frame, text="Çalıştır", width=15, command=self.calistir)
        self.calistir_buton.grid(row=0, column=0, padx=5)

        self.kopyala_buton = tk.Button(self.button_frame, text="Raporu Kopyala", width=15, command=self.raporu_kopyala)
        self.kopyala_buton.grid(row=0, column=1, padx=5)

        self.temizle_buton = tk.Button(self.button_frame, text="Temizle", width=15, command=self.raporu_temizle)
        self.temizle_buton.grid(row=0, column=2, padx=5)

        self.report_text = scrolledtext.ScrolledText(self.frame, width=70, height=15)
        self.report_text.pack(pady=10)

        self.bonus_bakiye_label.grid_remove()
        self.bonus_bakiye_entry.grid_remove()
        self.freespin_label.grid_remove()
        self.freespin_entry.grid_remove()
        self.turnuva_kazanci_label.grid_remove()
        self.turnuva_kazanci_entry.grid_remove()
        self.kazanc_tarihi_label.grid_remove()
        self.kazanc_tarihi_entry.grid_remove()

    def bonus_secildi(self, event):
        bonus = self.bonus_var.get()
        if bonus in self.bonus_kurallari:
            if bonus == "%25 FreeSpin Party Bonusu":
                self.freespin_label.grid(row=3, column=0, padx=5)
                self.freespin_entry.grid(row=3, column=1, padx=5)
                self.bonus_bakiye_label.grid_remove()
                self.bonus_bakiye_entry.grid_remove()
                self.turnuva_kazanci_label.grid_remove()
                self.turnuva_kazanci_entry.grid_remove()
                self.kazanc_tarihi_label.grid_remove()
                self.kazanc_tarihi_entry.grid_remove()
            elif bonus == "Turnuva Kazancı":
                self.turnuva_kazanci_label.grid(row=3, column=0, padx=5)
                self.turnuva_kazanci_entry.grid(row=3, column=1, padx=5)
                self.kazanc_tarihi_label.grid(row=4, column=0, padx=5)
                self.kazanc_tarihi_entry.grid(row=4, column=1, padx=5)
                self.bonus_bakiye_label.grid_remove()
                self.bonus_bakiye_entry.grid_remove()
                self.freespin_label.grid_remove()
                self.freespin_entry.grid_remove()
            else:
                self.freespin_label.grid_remove()
                self.freespin_entry.grid_remove()
                self.turnuva_kazanci_label.grid_remove()
                self.turnuva_kazanci_entry.grid_remove()
                self.kazanc_tarihi_label.grid_remove()
                self.kazanc_tarihi_entry.grid_remove()
                self.bonus_bakiye_label.grid(row=2, column=0, padx=5)
                self.bonus_bakiye_entry.grid(row=2, column=1, padx=5)
                self.bonus_bakiye_entry.delete(0, tk.END)
                self.bonus_bakiye_entry.insert(0, "")
        else:
            self.freespin_label.grid_remove()
            self.freespin_entry.grid_remove()
            self.turnuva_kazanci_label.grid_remove()
            self.turnuva_kazanci_entry.grid_remove()
            self.kazanc_tarihi_label.grid_remove()
            self.kazanc_tarihi_entry.grid_remove()
            self.bonus_bakiye_label.grid_remove()
            self.bonus_bakiye_entry.grid_remove()

    def calistir(self):
        if self.clipboard_izleme:
            self.stop_clipboard_izleme()
        else:
            self.start_clipboard_izleme()

    def start_clipboard_izleme(self):
        self.clipboard_izleme = True
        self.calistir_buton.config(text="Durdur")
        threading.Thread(target=self.clipboard_izle, daemon=True).start()

    def stop_clipboard_izleme(self):
        self.clipboard_izleme = False
        self.calistir_buton.config(text="Çalıştır")

    def clipboard_izle(self):
        while self.clipboard_izleme:
            try:
                clipboard_verisi = self.frame.clipboard_get()
                if clipboard_verisi:
                    self.veriyi_isle(clipboard_verisi)
                    self.stop_clipboard_izleme()
                    break
            except tk.TclError:
                pass
            self.frame.after(1000, self.clipboard_izle)
            break

    def veriyi_isle(self, veri):
        try:
            yatirim_miktari = self.yatirim_entry.get().replace(",", "")
            yatirim_miktari = float(yatirim_miktari) if yatirim_miktari else 0
            bonus_miktari_str = self.bonus_bakiye_entry.get().replace(",", "")
            bonus_miktari = float(bonus_miktari_str) if bonus_miktari_str else 0
            bonus = self.bonus_var.get()
            if bonus:
                if bonus == "%25 FreeSpin Party Bonusu":
                    freespin_kazanci_str = self.freespin_entry.get().replace(",", "")
                    freespin_kazanci = float(freespin_kazanci_str) if freespin_kazanci_str else 0
                    minimum_cevrim = yatirim_miktari * 1 + freespin_kazanci * self.bonus_kurallari[bonus]["cevrim_katsayisi"]
                elif bonus == "Turnuva Kazancı":
                    turnuva_kazanci_str = self.turnuva_kazanci_entry.get().replace(",", "")
                    turnuva_kazanci = float(turnuva_kazanci_str) if turnuva_kazanci_str else 0
                    minimum_cevrim = turnuva_kazanci
                else:
                    cevrim_katsayisi = self.bonus_kurallari[bonus]["cevrim_katsayisi"]
                    minimum_cevrim = yatirim_miktari * 1 + bonus_miktari * cevrim_katsayisi
            else:
                minimum_cevrim = yatirim_miktari

            satirlar = veri.strip().split("\n")
            toplam_cevrim = 0
            oyun_cevrimleri = {}
            for satir in satirlar:
                try:
                    parcalar = satir.split("\t")
                    oyun_adi = parcalar[4].strip()
                    bahis_miktari = float(parcalar[1].replace("₺", "").replace(",", ""))

                    if bonus and oyun_adi in self.bonus_kurallari[bonus].get("gecersiz_oyunlar", []):
                        continue

                    for oranli_oyun in self.oranli_oyunlar:
                        if oranli_oyun in oyun_adi:
                            bahis_miktari *= self.oranli_oyunlar[oranli_oyun]
                            break

                    toplam_cevrim += bahis_miktari
                    if oyun_adi in oyun_cevrimleri:
                        oyun_cevrimleri[oyun_adi] += bahis_miktari
                    else:
                        oyun_cevrimleri[oyun_adi] = bahis_miktari
                except Exception as e:
                    messagebox.showerror("Hata", f"Satır işlenirken bir hata oluştu: {e}\nSatır: {satir}")

            self.raporu_guncelle(toplam_cevrim, minimum_cevrim, oyun_cevrimleri, bonus)
        except Exception as e:
            messagebox.showerror("Hata", f"Veriyi işlerken bir hata oluştu: {e}")

    def raporu_guncelle(self, toplam_cevrim, minimum_cevrim, oyun_cevrimleri, bonus):
        rapor = "Oyun Çevrimleri:\n"
        for oyun, cevrim in oyun_cevrimleri.items():
            rapor += f"{oyun}: ₺{cevrim:.2f}\n"

        rapor += f"\nToplam Çevrim: ₺{toplam_cevrim:.2f}\nGereken Minimum Çevrim: ₺{minimum_cevrim:.2f}\n"

        if bonus == "Turnuva Kazancı":
            turnuva_kazanci_str = self.turnuva_kazanci_entry.get().replace(",", "")
            turnuva_kazanci = float(turnuva_kazanci_str) if turnuva_kazanci_str else 0
            max_cekim_tutari = turnuva_kazanci * self.bonus_kurallari[bonus]["maksimum_cekim_katsayisi"]
            kazanc_tarihi_str = self.kazanc_tarihi_entry.get()
            kazanc_tarihi = datetime.strptime(kazanc_tarihi_str, "%Y-%m-%d")
            bugun = datetime.now()
            gun_farki = (bugun - kazanc_tarihi).days
            if gun_farki > self.bonus_kurallari[bonus]["cekim_suresi_gun"]:
                rapor += "Kazanç tarihi 7 günü aştığı için çevrim geçersiz.\n"
                self.report_text.tag_configure("no", foreground="red")
                rapor_tag = "no"
            else:
                rapor += f"Maksimum Çekilebilir Tutar: ₺{max_cekim_tutari:.2f}\n\n"
                if toplam_cevrim >= minimum_cevrim:
                    rapor += "Çevrim Şartı Sağlandı!"
                    self.report_text.tag_configure("yes", foreground="green")
                    rapor_tag = "yes"
                else:
                    rapor += "Çevrim Şartı Sağlanamadı."
                    self.report_text.tag_configure("no", foreground="red")
                    rapor_tag = "no"
        elif bonus:
            max_cekim_tutari = self.bonus_kurallari[bonus]["maksimum_cekim"]
            rapor += f"Maksimum Çekilebilir Tutar: ₺{max_cekim_tutari:.2f}\n\n"

            if toplam_cevrim >= minimum_cevrim:
                rapor += "Çevrim Şartı Sağlandı!"
                self.report_text.tag_configure("yes", foreground="green")
                rapor_tag = "yes"
            else:
                rapor += "Çevrim Şartı Sağlanamadı."
                self.report_text.tag_configure("no", foreground="red")
                rapor_tag = "no"
        else:
            rapor += "Maksimum Çekilebilir Tutar: Maksimum Çekim Sınırı Yoktur\n\n"
            if toplam_cevrim >= minimum_cevrim:
                rapor += "Çevrim Şartı Sağlandı!"
                self.report_text.tag_configure("yes", foreground="green")
                rapor_tag = "yes"
            else:
                rapor += "Çevrim Şartı Sağlanamadı."
                self.report_text.tag_configure("no", foreground="red")
                rapor_tag = "no"

        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, rapor, rapor_tag)

    def raporu_kopyala(self):
        rapor = self.report_text.get(1.0, tk.END)
        self.frame.clipboard_clear()
        self.frame.clipboard_append(rapor)
        messagebox.showinfo("Bilgi", "Rapor panoya kopyalandı.")

    def raporu_temizle(self):
        self.bahis_verileri = {}
        self.report_text.delete(1.0, tk.END)
        self.yatirim_entry.delete(0, tk.END)
        self.bonus_bakiye_entry.delete(0, tk.END)
        self.freespin_entry.delete(0, tk.END)
        self.turnuva_kazanci_entry.delete(0, tk.END)
        self.kazanc_tarihi_entry.set_date(datetime.now())
        self.freespin_label.grid_remove()
        self.freespin_entry.grid_remove()
        self.turnuva_kazanci_label.grid_remove()
        self.turnuva_kazanci_entry.grid_remove()
        self.kazanc_tarihi_label.grid_remove()
        self.kazanc_tarihi_entry.grid_remove()
        self.bonus_bakiye_label.grid_remove()
        self.bonus_bakiye_entry.grid_remove()
        self.bonus_var.set("")
        self.calistir_buton.config(text="Çalıştır")

if __name__ == "__main__":
    root = tk.Tk()
    app = RaporOlusturucu(root)
    root.mainloop()