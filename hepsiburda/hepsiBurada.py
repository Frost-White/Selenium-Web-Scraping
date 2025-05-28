from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import pyodbc

# SQL Server bağlantı bilgileri
conn = pyodbc.connect(
    "Driver={SQL Server};"
    "Server=DESKTOP-Q0O2PEL;"
    "Database=Proje;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

# Chrome driver ayarları
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome()

# WebDriver'ı başlat
driver.maximize_window()

# İlgili başlangıç sayfasının URL'sini tanımlayalım
base_url = "https://www.hepsiburada.com/apple/iphone-ios-telefonlar-c-60005202?sayfa="

# Kaç ürün çekmek istediğimizi belirleyelim
max_urun_sayisi = 200
current_page = 1  # Başlangıç sayfası
counter = 0  # Ürün sayaç

# Kapasite bilgilerini içeren anahtarlar
kapasite_listesi = ["64gb", "128gb", "256gb", "512gb", "1tb", "2tb",
                    "64 gb", "128 gb", "256 gb", "512 gb", "1 tb", "2 tb"]
# Standart kapasite formatları
kapasite_formatlari = {
    "64gb": "64 GB",
    "128gb": "128 GB",
    "256gb": "256 GB",
    "512gb": "512 GB",
    "1tb": "1 TB",
    "2tb": "2 TB",
    "64 gb": "64 GB",
    "128 gb": "128 GB",
    "256 gb": "256 GB",
    "512 gb": "512 GB",
    "1 tb": "1 TB",
    "2 tb": "2 TB",
}

# Ürün bilgilerini çekme ve veritabanına kaydetme
while counter < max_urun_sayisi:
    # URL'yi güncelle
    url = f"{base_url}{current_page}"
    driver.get(url)

    # Sayfa tamamen yüklenene kadar bekleyin
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h2[@class='title-module_titleRoot__dNDiZ']"))
    )

    # Sayfayı aşağı kaydırarak yeni ürünlerin yüklenmesini sağla
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Kaydırma işleminin tamamlanmasını bekle

    # Ürün bilgilerini çek
    urunler = driver.find_elements(By.XPATH, "//h2[@class='title-module_titleRoot__dNDiZ']")
    fiyatlar = driver.find_elements(By.XPATH, "//div[@class='price-module_finalPrice__LtjvY']")
    urun_url = driver.find_elements(By.XPATH, "//a[@class='productCardLink-module_productCardLink__GZ3eU']")
    urun_gorseller = driver.find_elements(By.XPATH, "//picture//img[@class='hbImageView-module_hbImage__Ca3xO']")

    print(f"\nSayfa {current_page} çekiliyor...\n")
    
    def format_date(date):
        now = datetime.now()
        delta = now - date

        if delta.days == 0:
            return f"bugün, {date.strftime('%H:%M')}"
        elif delta.days == 1:
            return f"dün, {date.strftime('%H:%M')}"
        else:
            return date.strftime('%Y-%m-%d %H:%M')
        

    for urun, fiyat, url_eleman, gorsel in zip(urunler, fiyatlar, urun_url, urun_gorseller):
        fiyat_text = fiyat.text.strip()
        urun_url_text = url_eleman.get_attribute("href")  # Href özelliğini al
        urun_gorsel_url = gorsel.get_attribute("src")  # Görsel URL'sini al

        if fiyat_text:
            urun_text = urun.text.strip()
            urun_text_split = urun_text.split()
            

            # Kapasite bilgisini başlıktan çek
            kapasite = next((k for k in kapasite_listesi if k in urun_text.lower()), "Bilinmiyor")
            # Eğer kapasite bulunmuşsa, standart formata çevir
            if kapasite != "Bilinmiyor":
                kapasite = kapasite_formatlari.get(kapasite.lower(), "Bilinmiyor")
            

            # Ürün detayına giderek satıcı ve renk bilgilerini al
            driver.execute_script("window.open(arguments[0], '_blank');", urun_url_text)  # Yeni sekmede aç
            driver.switch_to.window(driver.window_handles[-1])  # Yeni sekmeye geç

            try:
                # Model bilgisini çek
                model_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='jkj4C4LML4qv2Iq8GkL3']//div[@class='AxM3TmSghcDRH1F871Vh']//a"))
                )
                model = model_element.text.strip()
            except Exception as e:
                print(f"Model bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                model = "Bilinmiyor"
            try:
                # Marka adını çekmek için doğru XPath ile hedefle
                marka_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-test-id='title-area']//a[@data-test-id='brand']"))
                )
                marka = marka_element.text.strip()
                print(f"Marka: {marka}")
            except Exception as e:
                print(f"Marka bilgisi alınamadı. Hata: {str(e)}")
                marka = "Bilinmiyor"    

            try:
                # Satıcı bilgisini çek
                satici_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.lZIamyT3gZHA5DDxZZx_ > a.W5OUPzvBGtzo9IdLz4Li > span"))
                )
                satici = satici_element.text.strip()
            except Exception as e:
                print(f"Satıcı bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                satici = "Bilinmiyor"

            try:
                # Renk bilgisini başlıktan çek
                renk_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='raeVnaSg0g9mMFTxKLRf']//h1[@class='xeL9CQ3JILmYoQPCgDcl']"))
                )
                renk_metni = renk_element.text.strip().lower()  # Başlık metnini küçük harfe dönüştürerek renk kontrolü
                renk_listesi = ["çöl titanyum", "gri", "beyaz", "siyah", "mavi", "kırmızı", "yeşil", "pembe", "turuncu", "sarı", "gümüş",
                                 "natürel titanyum", "lacivert taş", "deniz mavisi", "mavi titanyum", "mor", "çöl beji", "bej", "metalik"
                                 "blue", "altın", "red"]
                renk = next((r for r in renk_listesi if r in renk_metni), "Bilinmiyor")
            except Exception as e:
                print(f"Renk bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                renk = "Bilinmiyor"

            # Kampanya bilgisini çek
            kampanya_element = driver.find_elements(By.XPATH, "//span[@class='Gog20OJDAXL6rr7HFmj2']")
            kampanya = kampanya_element[0].text.strip() if kampanya_element else "Yok"

            # Stok bilgisini kontrol et
            try:
                stok_element = driver.find_element(By.XPATH, "//div[@class='ttVQfRCD0ugwrs65whKO _pGf4dDvGK0tdoimtqWf']")
                stok_yazisi = stok_element.text.strip().lower()

                # Stokta yoksa 'yok', varsa 'var'
                if "stoklarda olacaktır" in stok_yazisi:
                    stok_durumu = "yok"
                else:
                    stok_durumu = "var"
            except Exception as e:
                stok_durumu = "var"  # Eğer stok durumu bilgisi alınamazsa varsayılan olarak 'var'

            # Stok adedini kontrol et ve Dikkat sütununu ekle
            try:
               # İlk olarak "Stok Adedi" yazısının varlığını kontrol et
               stok_adedi_baslik = driver.find_elements(By.XPATH, "//div[contains(@class, 'jkj4C4LML4qv2Iq8GkL3')]//div[contains(@class, 'OXP5AzPvafgN_i3y6wGp') and text()='Stok Adedi']")
    
               if stok_adedi_baslik:
                   # Eğer "Stok Adedi" başlığı bulunursa, ilgili stok bilgisini kontrol et
                   stok_bilgisi_element = driver.find_elements(By.XPATH, "//div[contains(@class, 'AxM3TmSghcDRH1F871Vh')]//span")
        
                   if stok_bilgisi_element:
                       stok_bilgisi = stok_bilgisi_element[0].text.lower()
            
                       # Stok durumuna göre değerlendirme yap
                       if "20 adetten az" in stok_bilgisi:
                           dikkat = "20 Adetten Az"
                       elif "10 adetten az" in stok_bilgisi:
                           dikkat = "10 Adetten Az"
                       elif "5 adetten az" in stok_bilgisi:
                          dikkat = "5 Adetten Az"
                       else:
                          dikkat = None
                   else:
                       dikkat = "Stok Bilgisi Bulunamadı"
               else:
                   dikkat = "Stok Adedi Bilgisi Bulunamadı"
            except Exception as e:
               print(f"Dikkat bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
               dikkat = "Stokta"


            guncelleme_tarihi = format_date(datetime.now())
            # Veritabanına ürün ekleme veya güncelleme işlemi
            def urun_veritabanina_kaydet(marka, model, yeni_fiyat, urun_url_text, urun_gorsel_url, satici, renk, kapasite, kampanya, stok_durumu, guncelleme_tarihi,org_fiyat):
                site_no = 1
                kategori_no = 1
                # Fiyat 0 ise veya herhangi bir değer boşsa kaydetme
                cursor.execute("SELECT Fiyat FROM Urun WHERE Urunurl = ?", urun_url_text)
                sonuc = cursor.fetchone()
                if yeni_fiyat == 0.0 or not all([marka, model, urun_url_text, urun_gorsel_url, satici, renk, kapasite, kampanya, stok_durumu]):
                    print("Veri eksik veya fiyat 0, kayıt yapılmadı.")
                    return
                if sonuc:
                    cursor.execute("SELECT Fiyat, Urun_Id, Guncellemetarihi FROM Urun WHERE Urunurl = ?", urun_url_text)
                    id_sonuc = cursor.fetchone()
                    fiyat = sonuc[0]
                    urun_id = id_sonuc[1]
                    tarih = id_sonuc[2]
                    cursor.execute("INSERT INTO Urun_Eski_Fiyat (Urun_Id, Fiyat, Tarih) Values (?, ?, ?)", urun_id, fiyat, tarih)
                    cursor.execute("UPDATE Urun SET Fiyat = ?, Kampanya = ?, Stok = ?, Guncellemetarihi = ?, Org_Fiyat = ? WHERE Urunurl = ?",
                                yeni_fiyat, kampanya, stok_durumu, guncelleme_tarihi, org_fiyat, urun_url_text)
                else:
                    cursor.execute("""
                        INSERT INTO Urun (Marka, Model, Fiyat, Urunurl, Urungorsel, Satici, Kampanya, Stok, Guncellemetarihi, Site, Kategori, Org_Fiyat)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        marka, model, yeni_fiyat, urun_url_text, urun_gorsel_url, satici, kampanya, stok_durumu, guncelleme_tarihi, site_no, kategori_no, org_fiyat)
                    cursor.execute("SELECT Urun_Id FROM Urun WHERE Urunurl = ?", urun_url_text)
                    id_sonuc = cursor.fetchone()
                    cursor.execute("INSERT INTO Mobil_Ekstra (Urun_Id, Renk, Hafıza) VALUES (?, ?, ?)", id_sonuc[0], renk, kapasite)

                conn.commit()

            # Ana döngü içinde ürünü veritabanına kaydet çağrısı
            urun_veritabanina_kaydet(
                marka, model, 
                float(fiyat_text.replace(" TL", "").replace(".", "").replace(",", ".")),  # Yeni fiyat
                urun_url_text, urun_gorsel_url, satici, renk, kapasite, kampanya, stok_durumu, dikkat,guncelleme_tarihi
            )


            print(f"{counter + 1}. Marka: {marka}, Model: {model}, Fiyat: {fiyat_text}, Satıcı: {satici}, Renk: {renk}, Kapasite: {kapasite}, Kampanya: {kampanya}, Stok: {stok_durumu}, Dikkat: {dikkat},Guncelleme : {guncelleme_tarihi}, URL: {urun_url_text}")

            # Ürün sayfasını kapat ve ana sekmeye dön
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            counter += 1
            if counter >= max_urun_sayisi:
                break

    # Sayfalar arasında geçiş yap
    current_page += 1

# Veritabanı bağlantısını kapat
conn.commit()
cursor.close()
conn.close()

# Tarayıcıyı kapat
driver.quit()
