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

# Site ve kategori numaraları
site_no = 1  # HepsiBurada
kategori_no = 1  # Mobil (iPhone)

# Chrome driver ayarları
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome()

# WebDriver'ı başlat
driver.set_window_size(1024, 768)  # Genişlik: 1024px, Yükseklik: 768px

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

def extract_price_from_html(driver):
    try:
        # Önce indirimli fiyat yapısını dene
        try:
            price_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-test-id='price']//div[@data-test-id='default-price']//div[contains(@class, 'z7kokklsVwh0K5zFWjIO')]//span"))
            )
            new_price = price_element.text.strip()
            
            # Eski fiyatı kontrol et
            try:
                old_price_element = driver.find_element(By.XPATH, "//div[@data-test-id='prev-price']//span")
                old_price = old_price_element.text.strip()
            except:
                old_price = None
                
            return new_price, old_price
        except:
            # İndirimli yapı bulunamazsa, genel fiyat yapısını dene
            try:
                # Daha genel bir XPath kullanarak fiyatı bul
                price_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-test-id='price']//span[contains(text(), 'TL')]"))
                )
                new_price = price_element.text.strip()
                return new_price, None
            except:
                # Son çare olarak, herhangi bir fiyat içeren span'i ara
                try:
                    price_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'TL')]"))
                    )
                    new_price = price_element.text.strip()
                    return new_price, None
                except:
                    print("Fiyat bulunamadı")
                    return None, None
    except Exception as e:
        print(f"Fiyat çekilirken hata oluştu: {str(e)}")
        return None, None

def format_price(price_str):
    if not price_str:
        return None
    try:
        # Fiyat string'ini temizle
        cleaned_price = price_str.replace(" TL", "").replace(".", "").replace(",", ".")
        
        # Sadece sayı ve nokta içeriyor mu kontrol et
        if not all(c.isdigit() or c == '.' for c in cleaned_price):
            print(f"Geçersiz fiyat formatı: {price_str}")
            return None
            
        return float(cleaned_price)
    except Exception as e:
        print(f"Fiyat formatlanırken hata oluştu: {str(e)}")
        return None

def extract_kampanya(driver):
    try:
        # Önce kampanya metnini bulmaya çalış
        kampanya_element = driver.find_element(By.XPATH, "//div[@data-test-id='price']//span[contains(text(), 'kazanç') or contains(text(), 'indirim') or contains(text(), 'kampanya')]")
        return kampanya_element.text.strip()
    except:
        try:
            # Diğer kampanya metinlerini ara
            kampanya_element = driver.find_element(By.XPATH, "//span[contains(text(), 'kazanç') or contains(text(), 'indirim') or contains(text(), 'kampanya')]")
            return kampanya_element.text.strip()
        except:
            return "Yok"

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

            # Fiyat bilgilerini çek
            new_price_str, old_price_str = extract_price_from_html(driver)
            new_price = format_price(new_price_str)
            old_price = format_price(old_price_str)

            # Kampanya bilgisini çek
            kampanya = extract_kampanya(driver)

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
                # Dikkat bilgisi kontrolü
                dikkat_element = driver.find_elements(By.XPATH, "//div[contains(@class, 'AxM3TmSghcDRH1F871Vh')]//span")
                if dikkat_element and "50 adetten az" in dikkat_element[0].text.lower():
                    dikkat = "Tükenmek Üzere"
                else:
                    dikkat = None
            except Exception as e:
                print(f"Dikkat bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                dikkat = "Stokta"

            guncelleme_tarihi = datetime.now()
            # Veritabanına ürün ekleme veya güncelleme işlemi
            def urun_veritabanina_kaydet(marka, model, yeni_fiyat, org_fiyat, urun_url_text, urun_gorsel_url, satici, renk, kapasite, kampanya, stok_durumu, guncelleme_tarihi):
                site_no = 2
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
                new_price,  # Yeni fiyat
                old_price,  # Eski fiyat
                urun_url_text, urun_gorsel_url, satici, renk, kapasite, kampanya, stok_durumu, guncelleme_tarihi
            )

            print(f"{counter + 1}. Marka: {marka}, Model: {model}, Yeni Fiyat: {new_price}, Eski Fiyat: {old_price}, Satıcı: {satici}, Renk: {renk}, Kapasite: {kapasite}, Kampanya: {kampanya}, Stok: {stok_durumu}, Dikkat: {dikkat}, Guncelleme: {guncelleme_tarihi}, URL: {urun_url_text}")

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
