"""
BetConstruct Bonus Raporu - Tek Dosya Versiyonu
Streamlit web uygulaması - API entegrasyonu, tarih filtreleme ve Excel export özellikleri ile
"""

import streamlit as st
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import os
from datetime import datetime, timedelta
from io import BytesIO
import time
import random

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="BetConstruct Bonus Raporu",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Sağ üst köşeye kırmızı nokta butonu ekle
st.markdown("""
<style>
.red-dot-container {
    position: fixed;
    top: 60px;
    right: 20px;
    z-index: 999;
}

.red-dot {
    width: 12px;
    height: 12px;
    background-color: #ff4444;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
    animation: pulse 2s infinite;
}

.red-dot:hover {
    background-color: #ff0000;
    transform: scale(1.2);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(255, 68, 68, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(255, 68, 68, 0);
    }
}

.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltiptext {
    visibility: hidden;
    width: 120px;
    background-color: #333;
    color: white;
    text-align: center;
    border-radius: 6px;
    padding: 5px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -60px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}
</style>

<div class="red-dot-container">
    <div class="tooltip">
        <a href="https://cekimraporu.streamlit.app/" target="_blank" style="text-decoration: none;">
            <div class="red-dot"></div>
        </a>
        <span class="tooltiptext">Çekim Raporu</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Alternatif çözüm: Streamlit sidebar'da link butonu
with st.sidebar:
    st.markdown("---")
    if st.button("🔴 Çekim Raporu", help="Çekim Raporu uygulamasına git"):
        st.markdown("""
        <script>
        window.open('https://cekimraporu.streamlit.app/', '_blank');
        </script>
        """, unsafe_allow_html=True)
        st.info("🔗 Yeni sekmede açılıyor: https://cekimraporu.streamlit.app/")

# ========================= UTILITY FUNCTIONS =========================

def format_currency(amount):
    """Para birimi formatla (Türk Lirası)"""
    try:
        if pd.isna(amount) or amount == "" or amount is None:
            return "0,00 TL"
        
        # Sayıya çevir
        if isinstance(amount, str):
            amount = float(amount.replace(',', '.'))
        
        # Formatla
        return f"{amount:,.2f} TL".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    except:
        return '-'


def format_date_for_api(date_obj):
    """Tarihi BetConstruct API için formatla (dd-mm-yy - HH:MM:SS)"""
    try:
        if isinstance(date_obj, str):
            # String ise parse et
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        
        # datetime.date objesini datetime'a çevir (saat 00:00:00 ile)
        if hasattr(date_obj, 'year'):
            dt = datetime.combine(date_obj, datetime.min.time())
        else:
            dt = date_obj
        
        # BetConstruct formatına çevir: dd-mm-yy - HH:MM:SS
        return dt.strftime("%d-%m-%y - %H:%M:%S")
    except:
        return '-'


def create_summary_report(df):
    """Kullanıcı bazlı bonus özet raporu oluştur - Orijinal koda uygun"""
    try:
        if df.empty:
            return pd.DataFrame()
        
        if 'Kullanıcı ID' not in df.columns or 'Bonus Türü' not in df.columns or 'Miktar' not in df.columns:
            return pd.DataFrame()
        
        # Kullanıcı ve bonus türü bazlı gruplama
        user_bonus_summary = df.groupby(['Kullanıcı ID', 'Kullanıcı Adı', 'Bonus Türü']).agg({
            'Miktar': ['count', 'sum']
        }).reset_index()
        
        # MultiIndex sütunları düzelt
        user_bonus_summary.columns = ['Kullanıcı ID', 'Kullanıcı Adı', 'Bonus Türü', 'Kaç Defa Aldı', 'Toplam Miktar']
        
        # Miktarları formatla
        user_bonus_summary['Toplam Miktar Formatted'] = user_bonus_summary['Toplam Miktar'].apply(lambda x: format_currency(x))
        
        # Sıralama (önce toplam miktara göre, sonra kullanıcı ID'ye göre)
        user_bonus_summary = user_bonus_summary.sort_values(['Toplam Miktar', 'Kullanıcı ID'], ascending=[False, True])
        
        # Görüntüleme için sütun sırası
        display_columns = ['Kullanıcı ID', 'Kullanıcı Adı', 'Bonus Türü', 'Kaç Defa Aldı', 'Toplam Miktar Formatted']
        user_bonus_summary_display = user_bonus_summary[display_columns].copy()
        user_bonus_summary_display.columns = ['Kullanıcı ID', 'Kullanıcı Adı', 'Bonus Türü', 'Kaç Defa Aldı', 'Toplam Miktar']
        
        return user_bonus_summary_display
    
    except Exception as e:
        print(f"Özet rapor oluşturma hatası: {str(e)}")
        return pd.DataFrame()


def export_summary_to_excel(df, filename=None):
    """Özet raporları Excel'e aktarma fonksiyonu - Streamlit Cloud uyumlu"""
    try:
        if df.empty:
            st.error("Veri bulunamadı. Excel export yapılamaz.")
            return None, None
        
        # Dosya adı oluştur
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bonus_ozet_raporu_{timestamp}.xlsx"
        
        # Bellek buffer oluştur
        buffer = BytesIO()
        
        # Streamlit Cloud için xlsxwriter kullan
        try:
            with pd.ExcelWriter(buffer, engine='xlsxwriter', options={'remove_timezone': True}) as writer:
                # Ana veri sayfası
                df.to_excel(writer, sheet_name='Ana Veri', index=False)
                
                # Kullanıcı bazlı özet rapor
                summary_report = create_summary_report(df)
                if not summary_report.empty:
                    summary_report.to_excel(writer, sheet_name='Kullanici Ozeti', index=False)
                
                # Bonus türü bazlı özet rapor
                bonus_type_summary = create_bonus_type_summary(df)
                if not bonus_type_summary.empty:
                    bonus_type_summary.to_excel(writer, sheet_name='Bonus Turu Ozeti', index=False)
                
                # Günlük özet rapor
                daily_summary = create_daily_summary(df)
                if not daily_summary.empty:
                    daily_summary.to_excel(writer, sheet_name='Gunluk Ozet', index=False)
                
                # Workbook ve formatlar
                workbook = writer.book
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Her sayfa için stil uygula
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    
                    # Header formatı uygula ve sütun genişliklerini ayarla
                    if sheet_name == 'Ana Veri':
                        data_for_width = df
                    elif sheet_name == 'Kullanici Ozeti':
                        data_for_width = summary_report
                    elif sheet_name == 'Bonus Turu Ozeti':
                        data_for_width = bonus_type_summary
                    elif sheet_name == 'Gunluk Ozet':
                        data_for_width = daily_summary
                    else:
                        continue
                    
                    # Sütun genişlikleri ayarla
                    for col_num, value in enumerate(data_for_width.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                        try:
                            max_len = max(
                                data_for_width[value].astype(str).map(len).max(),
                                len(str(value))
                            )
                            worksheet.set_column(col_num, col_num, min(max_len + 2, 50))
                        except:
                            worksheet.set_column(col_num, col_num, 15)
            
            buffer.seek(0)
            return buffer.getvalue(), filename
            
        except Exception as xlsxwriter_error:
            st.error(f"xlsxwriter hatası: {str(xlsxwriter_error)}")
            # Fallback: basit Excel export
            try:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Ana Veri', index=False)
                buffer.seek(0)
                return buffer.getvalue(), filename
            except Exception as openpyxl_error:
                st.error(f"openpyxl fallback hatası: {str(openpyxl_error)}")
                return None, None
        
    except Exception as e:
        st.error(f"Excel export genel hatası: {str(e)}")
        return None, None


def create_daily_summary(df):
    """Günlük bonus özet raporu oluştur"""
    try:
        if df.empty or 'Tarih' not in df.columns or 'Miktar' not in df.columns:
            return pd.DataFrame()
        
        # Tarih sütununu datetime'a çevir
        df_copy = df.copy()
        df_copy['Tarih'] = pd.to_datetime(df_copy['Tarih'], errors='coerce')
        df_copy['Gün'] = df_copy['Tarih'].dt.date
        
        # Günlük gruplama
        daily_summary = df_copy.groupby('Gün').agg({
            'Miktar': ['count', 'sum'],
            'Kullanıcı ID': 'nunique'
        }).reset_index()
        
        # Sütun adlarını düzelt
        daily_summary.columns = ['Tarih', 'Toplam İşlem', 'Toplam Miktar', 'Benzersiz Kullanıcı']
        
        # Miktarları formatla
        daily_summary['Toplam Miktar Formatted'] = daily_summary['Toplam Miktar'].apply(lambda x: format_currency(x))
        
        # Görüntüleme sütunları
        display_columns = ['Tarih', 'Toplam İşlem', 'Toplam Miktar Formatted', 'Benzersiz Kullanıcı']
        daily_summary_display = daily_summary[display_columns].copy()
        daily_summary_display.columns = ['Tarih', 'Toplam İşlem', 'Toplam Miktar', 'Benzersiz Kullanıcı']
        
        return daily_summary_display.sort_values('Tarih', ascending=False)
        
    except Exception as e:
        print(f"Günlük özet rapor hatası: {str(e)}")
        return pd.DataFrame()


def create_bonus_type_summary(df):
    """Bonus türü bazlı özet rapor oluştur"""
    try:
        if df.empty:
            return pd.DataFrame()
        
        # Bonus türlerine göre gruplama
        if 'Bonus Türü' not in df.columns:
            return pd.DataFrame()
        
        summary = df.groupby('Bonus Türü').agg({
            'Kullanıcı ID': 'count',
            'Miktar': ['sum', 'mean'],
            'Para Birimi': 'first'
        }).reset_index()
        
        # MultiIndex sütunları düzelt
        summary.columns = ['Bonus Türü', 'Adet', 'Toplam Miktar', 'Ortalama Miktar', 'Para Birimi']
        
        # Formatla
        summary['Toplam Miktar'] = summary['Toplam Miktar'].apply(lambda x: format_currency(x))
        summary['Ortalama Miktar'] = summary['Ortalama Miktar'].apply(lambda x: format_currency(x))
        
        # Toplam satırı ekle
        total_row = pd.DataFrame({
            'Bonus Türü': ['TOPLAM'],
            'Adet': [df['Kullanıcı ID'].count()],
            'Toplam Miktar': [format_currency(df['Miktar'].sum())],
            'Ortalama Miktar': [format_currency(df['Miktar'].mean())],
            'Para Birimi': ['TL']
        })
        
        summary = pd.concat([summary, total_row], ignore_index=True)
        
        return summary
    
    except Exception as e:
        print(f"Bonus türü özet rapor oluşturma hatası: {str(e)}")
        return pd.DataFrame()


# ========================= API HANDLER CLASS =========================

class BonusAPIHandler:
    def __init__(self, auth_key=None):
        self.base_url = "https://backofficewebadmin.betconstruct.com/api/tr/Report/GetClientBonusReport"
        self.auth_key = auth_key or os.getenv("BETCONSTRUCT_AUTH_KEY", "affe433a578d139ed6aa4e3c02bbdd7e341719493c31e3c39a8ee60711aaeb75")
        self.referer = "https://backoffice.betconstruct.com/"
        self.origin = "https://backoffice.betconstruct.com"
    
    def update_settings(self, settings):
        """API ayarlarını güncelle"""
        self.auth_key = settings.get("auth_key", self.auth_key)
        self.referer = settings.get("referer", self.referer)
        self.origin = settings.get("origin", self.origin)
    
    def get_headers(self):
        """API istekleri için header oluştur - Daha basit ve etkili versiyon"""
        return {
            "Authentication": self.auth_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": self.referer,
            "Origin": self.origin,
            "X-Requested-With": "XMLHttpRequest"
        }
    
    def build_request_payload(self, filters):
        """API isteği için payload oluştur - Tkinter versiyonuna uygun"""
        try:
            # Tarihleri string'e çevir
            start_date = format_date_for_api(filters["start_date"])
            end_date = format_date_for_api(filters["end_date"])
            
            # Debug log
            print(f"Start date: {start_date}")
            print(f"End date: {end_date}")
            
            # Tkinter versiyonuna uygun payload yapısı
            payload = {
                "ClientBonusId": "",
                "ClientId": str(filters.get("client_id", "")),
                "PartnerBonusId": "",
                "AcceptanceType": None,
                "BonusType": "1" if filters.get("bonus_type") == "Casino Kayıp Bonusu" else None,
                "BonusSource": None,
                "ByPassTotals": False,
                "EndDateLocal": None,
                "IsTest": None,
                "MaxRows": filters.get("max_rows", 100),
                "PartnerBonusEndDateLocal": end_date,
                "PartnerBonusStartDateLocal": start_date,
                "ResultFromDateLocal": None,
                "ResultToDateLocal": None,
                "ResultType": None,
                "SkeepRows": 0,
                "SportsbookProfileId": None,
                "StartDateLocal": None,
                "ToCurrencyId": "TRY"
            }
            
            # Debug log
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            return payload
            
        except Exception as e:
            print(f"Payload oluşturma hatası: {str(e)}")
            return {
                "error": f"Payload oluşturma hatası: {str(e)}",
                "details": {
                    "start_date": str(filters.get("start_date")),
                    "end_date": str(filters.get("end_date"))
                }
            }
    
    def get_bonus_status(self, acceptance_type):
        """Bonus durumunu çevir"""
        status_map = {
            0: "Beklemede",
            1: "Onaylandı", 
            2: "Reddedildi",
            3: "İptal Edildi"
        }
        return status_map.get(acceptance_type, "Bilinmeyen")
    
    def fetch_bonus_report(self, filters):
        """BetConstruct API'den bonus raporu getir - CloudFlare bypass ile"""
        try:
            payload = self.build_request_payload(filters)
            
            if not payload:
                return {
                    "success": False,
                    "error": "Payload oluşturulamadı",
                    "data": pd.DataFrame()
                }
            
            # Her denemede farklı IP adresi ve User-Agent varyasyonu
            for attempt in range(5):  # Deneme sayısını artırma
                try:
                    # Her denemede farklı session
                    session = requests.Session()
                    
                    # Retry stratejisi
                    retry_strategy = Retry(
                        total=3,
                        backoff_factor=1.0,  # Daha uzun bekleme
                        status_forcelist=[429, 500, 502, 503, 504],
                        allowed_methods=["POST"]
                    )
                    
                    adapter = HTTPAdapter(max_retries=retry_strategy)
                    session.mount("http://", adapter)
                    session.mount("https://", adapter)
                    
                    # Headers ayarla
                    headers = self.get_headers()
                    
                    # Daha fazla User-Agent varyasyonu
                    user_agents = [
                        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120, 135)}.0.0.0 Safari/537.36",
                        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/{random.randint(120, 135)}.0 Safari/537.36",
                        f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120, 135)}.0.0.0 Safari/537.36",
                        f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120, 135)}.0.0.0 Safari/537.36",
                        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(120, 135)}.0) Gecko/20100101 Firefox/{random.randint(120, 135)}.0"
                    ]
                    headers["User-Agent"] = random.choice(user_agents)
                    
                    # Daha fazla HTTP başlığı varyasyonu
                    headers["Accept-Language"] = random.choice([
                        "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                        "en-US,en;q=0.9",
                        "tr-TR,tr;q=0.8,en-US;q=0.7,en;q=0.6"
                    ])
                    
                    # Daha fazla HTTP başlığı varyasyonu
                    headers["Sec-Ch-Ua"] = random.choice([
                        '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                        '"Firefox";v="131", "Gecko";v="131", "Not_A Brand";v="24"',
                        '"Safari";v="131", "WebKit";v="131", "Not_A Brand";v="24"'
                    ])
                    
                    session.headers.update(headers)
                    
                    # Daha uzun ve rastgele bekleme süresi
                    if attempt > 0:
                        wait_time = random.uniform(2, 5)
                        print(f"Waiting {wait_time:.1f} seconds before retry {attempt + 1}...")
                        time.sleep(wait_time)
                    
                    # İsteği gönder
                    response = session.post(
                        self.base_url,
                        json=payload,
                        timeout=(30, 120),  # Timeout'u artırma
                        verify=True,
                        allow_redirects=False
                    )
                    
                    # Response detaylarını logla
                    print(f"Attempt {attempt + 1}: Status Code: {response.status_code}")
                    print(f"Response Headers: {dict(response.headers)}")
                    
                    # 530 değilse başarılı, döngüden çık
                    if response.status_code != 530:
                        break
                        
                except requests.exceptions.RequestException as e:
                    print(f"Request failed on attempt {attempt + 1}: {str(e)}")
                    if attempt == 4:  # Son deneme
                        raise e
                    continue
            
            # Detaylı hata kontrolü
            if response.status_code == 530:
                return {
                    "success": False,
                    "error": "CloudFlare engeli - Lütfen Auth Key'inizi kontrol edin veya VPN kullanmayı deneyin",
                    "data": pd.DataFrame(),
                    "response_text": f"Status: {response.status_code}, Headers: {dict(response.headers)}"
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Yetkisiz erişim - Auth Key hatalı veya süresi dolmuş",
                    "data": pd.DataFrame(),
                    "response_text": response.text
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "Erişim yasak - IP adresi veya Auth Key kısıtlaması",
                    "data": pd.DataFrame(),
                    "response_text": response.text
                }
            
            response.raise_for_status()
            
            data = response.json()
            
            # API yanıtını DataFrame'e çevir - bonus türleri filtresini geç
            df = self.process_api_response(data, filters.get("bonus_types"))
            
            # Eğer sonuç yoksa ve bugünün tarihiyse, 23:59:59'a kadar olan verileri deneyelim
            if df.empty and filters.get("end_date") == datetime.now().date():
                # End date'i 23:59:59'a ayarla
                payload["PartnerBonusEndDateLocal"] = datetime.combine(
                    filters["end_date"], 
                    datetime.max.time()
                ).strftime("%d-%m-%y - %H:%M:%S")
                
                # Tekrar deneyelim
                response = session.post(
                    self.base_url,
                    json=payload,
                    timeout=(30, 120),
                    verify=True,
                    allow_redirects=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    df = self.process_api_response(data, filters.get("bonus_types"))
                    
            return {
                "success": True,
                "data": df,
                "total_records": len(df)
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API isteği hatası: {str(e)}"
            if "530" in str(e):
                error_msg += " - CloudFlare koruması aktif olabilir"
            elif "timeout" in str(e).lower():
                error_msg += " - Bağlantı zaman aşımı"
            elif "connection" in str(e).lower():
                error_msg += " - Bağlantı problemi"
            
            return {
                "success": False,
                "error": error_msg,
                "data": pd.DataFrame(),
                "response_text": response.text if 'response' in locals() and response else 'Bağlantı kurulamadı'
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Genel hata: {str(e)}",
                "data": pd.DataFrame(),
                "response_text": response.text if 'response' in locals() and response else 'Genel hata'
            }
    
    def process_api_response(self, api_data, bonus_types_filter=None):
        """API yanıtını DataFrame formatına çevir - Çoklu bonus türü desteği ile"""
        try:
            # API hata kontrolü
            if isinstance(api_data, dict) and api_data.get('HasError', False):
                print(f"API Hatası: {api_data.get('AlertMessage', 'Bilinmeyen hata')}")
                return pd.DataFrame()
            
            # BetConstruct API yanıt yapısına göre bonus listesini al
            bonus_list = None
            
            if isinstance(api_data, dict) and "Data" in api_data:
                data_obj = api_data["Data"]
                if isinstance(data_obj, dict) and "ClientBonusReportData" in data_obj:
                    bonus_report_data = data_obj["ClientBonusReportData"] 
                    if isinstance(bonus_report_data, dict) and "Objects" in bonus_report_data:
                        bonus_list = bonus_report_data["Objects"]
            
            if not bonus_list or len(bonus_list) == 0:
                print(f"API Yanıtı: {str(api_data)[:200]}")
                return pd.DataFrame()
            
            # DataFrame için veri listesi
            processed_data = []
            
            for bonus in bonus_list:
                if isinstance(bonus, dict):
                    bonus_name = str(bonus.get("Name", ""))
                    
                    # Çoklu bonus türü filtrelemesi
                    if bonus_types_filter and len(bonus_types_filter) > 0:
                        # Seçilen bonus türlerinden herhangi biri ile eşleşiyor mu kontrol et
                        bonus_match = False
                        for selected_type in bonus_types_filter:
                            if bonus_name.strip().upper() == selected_type.upper():
                                bonus_match = True
                                break
                        
                        # Eşleşme yoksa bu bonusu atla
                        if not bonus_match:
                            continue
                    
                    # API yanıtından doğru alan isimlerini kullan
                    processed_data.append({
                        'Kullanıcı ID': str(bonus.get("ClientId", "")),
                        'Kullanıcı Adı': str(bonus.get("ClientName", "")),
                        'Tarafından Oluşturuldu': str(bonus.get("CreatedByUserName", "")),
                        'Bonus Türü': bonus_name,
                        'Miktar': float(bonus.get("Amount", 0)),
                        'Para Birimi': str(bonus.get("ClientCurrency", "TRY")),
                        'Durum': self.get_bonus_status(bonus.get("AcceptanceType", 0)),
                        'Tarih': str(bonus.get("AcceptanceDateLocal", ""))
                    })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"API yanıt işleme hatası: {str(e)}")
            return pd.DataFrame()
    
    def create_excel_export(self, df):
        """DataFrame'i Excel formatında export et - Streamlit Cloud basit çözüm"""
        try:
            if df.empty:
                st.error("DataFrame boş - Excel oluşturulamaz")
                return None
            
            st.info(f"Excel oluşturuluyor... Satır sayısı: {len(df)}")
            
            # En basit yöntem: sadece openpyxl
            buffer = BytesIO()
            
            try:
                # Basit Excel export - hiçbir özel format yok
                df.to_excel(buffer, index=False, engine='openpyxl')
                buffer.seek(0)
                
                excel_data = buffer.getvalue()
                if len(excel_data) > 0:
                    st.success(f"Excel dosyası başarıyla oluşturuldu! Boyut: {len(excel_data)} byte")
                    return excel_data
                else:
                    st.error("Excel dosyası boş oluştu")
                    return None
                    
            except ImportError as import_error:
                st.error(f"Kütüphane eksik: {str(import_error)}")
                st.info("Streamlit Cloud'da openpyxl kütüphanesi eksik olabilir")
                return None
                
            except Exception as excel_error:
                st.error(f"Excel oluşturma hatası: {str(excel_error)}")
                st.info("Hata detayı: Excel dosyası oluşturulamadı")
                
                # Son çare: CSV olarak export
                try:
                    st.warning("Excel başarısız, CSV deneniyor...")
                    csv_buffer = BytesIO()
                    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                    csv_buffer.seek(0)
                    return csv_buffer.getvalue()
                except Exception as csv_error:
                    st.error(f"CSV export da başarısız: {str(csv_error)}")
                    return None
            
        except Exception as e:
            st.error(f"Genel hata: {str(e)}")
            st.info("Debug: Excel export fonksiyonu tamamen başarısız")
            return None


# ========================= SETTINGS FUNCTIONS =========================

def load_settings():
    """Ayarları JSON dosyasından yükle"""
    settings_file = "settings.json"
    default_settings = {
        "auth_key": os.getenv("BETCONSTRUCT_AUTH_KEY", "2582007cbe97f891cf5fe69f4f2d44b002c021e6fca4c8276dc0accf4098d5fe"),
        "referer": "https://backoffice.betconstruct.com/",
        "origin": "https://backoffice.betconstruct.com"
    }

    try:
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                return json.load(f)
    except:
        pass

    return default_settings


def save_settings(settings):
    """Ayarları JSON dosyasına kaydet"""
    try:
        with open("settings.json", "w") as f:
            json.dump(settings, f)
        return True
    except:
        return False


# ========================= MAIN APPLICATION =========================

def main():
    # Session state başlatma
    if 'bonus_data' not in st.session_state:
        st.session_state.bonus_data = pd.DataFrame()
    
    if 'api_handler' not in st.session_state:
        settings = load_settings()
        st.session_state.api_handler = BonusAPIHandler(settings.get("auth_key"))
    
    if 'settings' not in st.session_state:
        st.session_state.settings = load_settings()

    # Header - Kilit ikonu ile API ayarları
    header_col1, header_col2 = st.columns([10, 1])
    with header_col1:
        st.title("🏆 BetConstruct Bonus Raporu")
        st.markdown("Tarih aralığını seçin ve o dönemde alınan tüm bonusları görüntüleyin.")
    
    with header_col2:
        if st.button("🔐", help="API Ayarları", key="api_settings_button"):
            st.session_state.show_api_settings = not st.session_state.get("show_api_settings", False)

    # API Ayarları Modal
    if st.session_state.get("show_api_settings", False):
        with st.container():
            st.markdown("###⚙️ API Ayarları")
            
            settings = load_settings()
            
            # Auth Key ayarı
            auth_key = st.text_input(
                "Authentication Key:",
                value=settings.get("auth_key", ""),
                type="password",
                help="BetConstruct API Auth Key"
            )
            
            referer = st.text_input(
                "Referer:",
                value=settings.get("referer", ""),
                help="API Referer header"
            )
            
            origin = st.text_input(
                "Origin:",
                value=settings.get("origin", ""),
                help="API Origin header"
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("💾 Kaydet"):
                    new_settings = {
                        "auth_key": auth_key,
                        "referer": referer,
                        "origin": origin
                    }
                    if save_settings(new_settings):
                        st.session_state.api_handler.update_settings(new_settings)
                        st.success("✅ API ayarları güncellendi!")
                    else:
                        st.error("❌ Ayarlar kaydedilemedi!")
                    st.session_state.show_api_settings = False
                    st.rerun()
            
            with col2:
                if st.button("🔍 Test Et"):
                    if auth_key:
                        st.info("API bağlantısı test ediliyor...")
                        
                        # Test API handler oluştur
                        test_handler = BonusAPIHandler(auth_key)
                        test_handler.referer = referer or "https://backoffice.betconstruct.com/"
                        test_handler.origin = origin or "https://backoffice.betconstruct.com"
                        
                        # Basit test isteği
                        test_filters = {
                            "start_date": datetime.now().date() - timedelta(days=1),
                            "end_date": datetime.now().date(),
                            "max_rows": 1
                        }
                        
                        test_result = test_handler.fetch_bonus_report(test_filters)
                        
                        if test_result["success"]:
                            st.success("✅ API bağlantısı başarılı!")
                        else:
                            st.error(f"❌ API testi başarısız: {test_result['error']}")
                            
                            with st.expander("Test Hata Detayları"):
                                st.text(f"Auth Key: {auth_key[:20]}..." if len(auth_key) > 20 else auth_key)
                                st.text(f"API URL: {test_handler.base_url}")
                                if 'response_text' in test_result:
                                    st.text(f"Yanıt: {test_result['response_text'][:200]}...")
                    else:
                        st.warning("⚠️ Auth Key giriniz!")
            
            with col3:
                if st.button("❌ Kapat"):
                    st.session_state.show_api_settings = False
                    st.rerun()
            
            # Troubleshooting rehberi
            with st.expander("🔧 VPN ile 530 Error Çözümü"):
                st.markdown("""
                **VPN kullanırken 530 hatası alıyorsanız:**
                1. **En Etkili:** VPN'i geçici olarak kapatın ve tekrar deneyin
                2. VPN sunucu lokasyonunu değiştirin (Türkiye/Avrupa tercih edin)
                3. VPN protokolünü değiştirin (OpenVPN → WireGuard veya tersi)
                4. "Test Et" butonuna birkaç kez tıklayın (otomatik retry var)
                
                **Auth Key güncellemesi:**
                1. BetConstruct back office'e tarayıcıdan giriş yapın
                2. F12 → Network sekmesi → herhangi bir işlem yapın
                3. İsteklerde Authorization: Bearer ... kısmını kopyalayın
                4. Buraya yapıştırın
                
                **Diğer çözümler:**
                - İnternet bağlantınızı yenileyin
                - Farklı bir cihazdan deneyin
                - Auth Key'in başında/sonunda boşluk olmadığından emin olun
                - Token'ın tam olarak kopyalandığından emin olun
                
                **Teknik detay:** Bu uygulama 3 farklı User-Agent ile otomatik deneme yapıyor ve CloudFlare bypass teknikleri kullanıyor.
                """)
            
            st.divider()

    # Ana içerik alanı
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Filtreler")

        # Tarih aralığı
        col_start, col_end = st.columns(2)

        with col_start:
            # Varsayılan başlangıç tarihi (7 gün önce)
            default_start = datetime.now() - timedelta(days=7)
            start_date = st.date_input("Başlangıç Tarihi:",
                                       value=default_start)

        with col_end:
            end_date = st.date_input("Bitiş Tarihi:",
                                     value=datetime.now())

        # Diğer filtreler
        col_user, col_bonus = st.columns(2)

        with col_user:
            client_id = st.text_input("Kullanıcı ID (isteğe bağlı):")

        with col_bonus:
            bonus_types = [
                "CASİNO KAYIP BONUSU", "%100  SLOT BONUSU",
                "%100 CASİNO HOŞGELDİN BONUSU",
                "%100 PRAGMATİC SALI - PERŞEMBE", "%100 SPOR HOŞGELDİN BONUSU",
                "%25 SPOR YATIRIM BONUSU", "%5 CASİNO HAFTALIK",
                "%5 SPOR HAFTALIK", "250 TL CASİNO DENEME BONUSU",
                "250 TL DOĞUM GÜNÜ CASİNO BONUSU", "250 TL SPOR DENEME BONUSU",
                "CASİNO BAĞLILIK BONUSU", "CASİNO CALL DAVET",
                "CASİNO ÇEVRİMSİZ BONUS", "CASİNO DOĞUM GÜNÜ BONUSU",
                "%10 ÇEVRİMSİZ SPOR BONUSU",
                "P.TESİ & ÇARŞAMBA %100 GÜNÜN İLK KAYIBINA",
                "SPOR BAĞLILIK BONUSU", "SPOR CALL DAVET",
                "SPOR ÇEVRİMSİZ BONUS", "SPOR DOĞUM GÜNÜ BONUSU",
                "SPOR KAYIP BONUSU", "YENİ CASİNO ŞANS BONUSU"
            ]

            selected_bonus_types = st.multiselect(
                "Bonus Türleri (Birden fazla seçebilirsiniz):",
                bonus_types,
                help="Boş bırakırsanız tüm bonus türleri getirilir"
            )

        max_rows = st.number_input("Maksimum Kayıt:",
                                   min_value=1,
                                   max_value=10000,
                                   value=2000)

    with col2:
        st.subheader("⚡ İşlemler")

        # Butonlar
        if st.button("🔍 Bonus Raporunu Getir",
                     type="primary",
                     use_container_width=True):
            if start_date > end_date:
                st.error("Başlangıç tarihi bitiş tarihinden sonra olamaz!")
            else:
                with st.spinner("Bonus raporu getiriliyor..."):
                    try:
                        filters = {
                            "start_date": start_date,
                            "end_date": end_date,
                            "client_id": client_id.strip() if client_id else None,
                            "bonus_types": selected_bonus_types if selected_bonus_types else None,
                            "max_rows": max_rows
                        }

                        result = st.session_state.api_handler.fetch_bonus_report(filters)

                        if result["success"]:
                            st.session_state.bonus_data = result["data"]
                            st.success(f"✅ {result['total_records']} kayıt getirildi!")
                        else:
                            st.error(f"❌ {result['error']}")
                            st.session_state.bonus_data = pd.DataFrame()
                            
                            with st.expander("Hata Detayları"):
                                st.text(f"API URL: {st.session_state.api_handler.base_url}")
                                st.text(f"Filtreler: {filters}")
                                if 'response_text' in result:
                                    st.text(f"API Yanıtı: {result['response_text'][:500]}...")

                    except Exception as e:
                        st.error(f"❌ Beklenmeyen hata: {str(e)}")

        # Excel Export
        if not st.session_state.bonus_data.empty:
            if st.button("📊 Excel'e Kaydet", use_container_width=True):
                try:
                    # Excel dosyası oluştur
                    excel_buffer = st.session_state.api_handler.create_excel_export(
                        st.session_state.bonus_data)

                    if excel_buffer:
                        filename = f"bonus_raporu_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"

                        st.download_button(
                            label="📥 Excel Dosyasını İndir",
                            data=excel_buffer,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)
                except Exception as e:
                    st.error(f"Excel export hatası: {str(e)}")

            # Özet Rapor - Bonus - Kopya.py'deki çalışan versiyona uygun
            if st.button("📈 Özet Rapor Oluştur", use_container_width=True):
                try:
                    # Kullanıcı bazlı özet rapor (hangi kullanıcı kaç defa aldı)
                    user_summary = create_summary_report(st.session_state.bonus_data)
                    
                    if not user_summary.empty:
                        st.subheader("👥 Kullanıcı Bazlı Özet (Hangi kullanıcı kaç defa aldı)")
                        st.dataframe(user_summary, use_container_width=True)
                        
                        # Kullanıcı özet raporu Excel export - Streamlit Cloud için geliştirilmiş
                        try:
                            excel_buffer = st.session_state.api_handler.create_excel_export(user_summary)
                            if excel_buffer:
                                # Session state'e kaydet
                                st.session_state.user_summary_excel = excel_buffer
                                st.session_state.user_summary_filename = f"kullanici_ozet_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
                                
                                # Download button'u hemen göster
                                st.download_button(
                                    label="📥 Kullanıcı Özet Raporunu İndir",
                                    data=excel_buffer,
                                    file_name=f"kullanici_ozet_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True,
                                    key="user_summary_download"  # Unique key for Streamlit Cloud
                                )
                            else:
                                st.error("Excel dosyası oluşturulamadı")
                        except Exception as excel_error:
                            st.error(f"Excel oluşturma hatası: {str(excel_error)}")
                            st.write("Debug: Excel buffer oluşturma başarısız")
                        
                        st.divider()
                        
                    # Bonus türü bazlı özet rapor
                    type_summary = create_bonus_type_summary(st.session_state.bonus_data)
                    
                    if not type_summary.empty:
                        st.subheader("🎁 Bonus Türlerine Göre Özet")
                        st.dataframe(type_summary, use_container_width=True)
                        
                        # Genel istatistikler
                        total_bonuses = len(st.session_state.bonus_data)
                        total_amount = st.session_state.bonus_data['Miktar'].sum()
                        unique_users = st.session_state.bonus_data['Kullanıcı ID'].nunique()
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Toplam Bonus Sayısı", total_bonuses)
                        with col2:
                            st.metric("Toplam Miktar", format_currency(total_amount))
                        with col3:
                            st.metric("Benzersiz Kullanıcı", unique_users)

                except Exception as e:
                    st.error(f"Özet rapor hatası: {str(e)}")

            # Streamlit Cloud için ayrı download bölümü
            if hasattr(st.session_state, 'user_summary_excel') and st.session_state.user_summary_excel:
                st.subheader("📥 İndirme Seçenekleri")
                
                # Kullanıcı özet raporu download
                st.download_button(
                    label="📥 Kullanıcı Özet Raporunu İndir (Yedek)",
                    data=st.session_state.user_summary_excel,
                    file_name=st.session_state.user_summary_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="backup_user_summary_download"
                )
                
                st.info("ℹ️ Eğer yukarıdaki indirme butonu görünmüyorsa, bu yedek butonu kullanabilirsiniz.")
                st.divider()

        # Temizle
        if st.button("🗑️ Sonuçları Temizle", use_container_width=True):
            st.session_state.bonus_data = pd.DataFrame()
            st.success("Sonuçlar temizlendi!")
            st.rerun()

    # Sonuçlar tablosu
    if not st.session_state.bonus_data.empty:
        st.subheader("📋 Bonus Raporu")

        # Veri tablosu
        st.dataframe(st.session_state.bonus_data,
                     use_container_width=True,
                     height=400)

        # Durum bilgileri
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f"📊 Toplam kayıt: {len(st.session_state.bonus_data)}")

        with col2:
            if 'Miktar' in st.session_state.bonus_data.columns:
                total_amount = st.session_state.bonus_data['Miktar'].sum()
                st.info(f"💰 Toplam miktar: {format_currency(total_amount)}")

        with col3:
            if 'Kullanıcı ID' in st.session_state.bonus_data.columns:
                unique_users = st.session_state.bonus_data['Kullanıcı ID'].nunique()
                st.info(f"👤 Benzersiz kullanıcı: {unique_users}")


if __name__ == "__main__":
    main()
