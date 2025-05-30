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
base_url = "https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98?sayfa="

# Kaç ürün çekmek istediğimizi belirleyelim
max_urun_sayisi = 200
current_page = 1  # Başlangıç sayfası
counter = 0  # Ürün sayaç

# Kapasite bilgilerini içeren anahtarlar
kapasite_listesi = [ "256gb", "500gb", "512gb", "1tb", "2tb", "4tb",
                     "256 gb","500 gb","512 gb", "1 tb", "2 tb", "4 tb"]
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
            marka = urun_text_split[0]  # İlk kelime marka
            model = " ".join(urun_text_split[1:])  # Geri kalanı model


            # Kapasite bilgisini başlıktan çek
            kapasite = next((k for k in kapasite_listesi if k in urun_text.lower()), "Bilinmiyor")

            # Eğer kapasite bilgisi bulamazsa, yeni HTML yapısından kapasiteyi al
            if kapasite == "Bilinmiyor":
                try:
                    # Kapasiteyi yeni HTML yapısından çek
                    kapasite_elements = driver.find_elements(By.XPATH, "//div[@class='jkj4C4LML4qv2Iq8GkL3']//div[text()='SSD Kapasitesi']/following-sibling::div//span")
                    if kapasite_elements:
                        # Elde edilen kapasiteyi kontrol et
                        for element in kapasite_elements:
                            kapasite_text = element.text.strip().lower()
                            # Kapasiteyi listede var mı diye kontrol et
                            if any(k in kapasite_text for k in kapasite_listesi):
                                kapasite = next(k for k in kapasite_listesi if k in kapasite_text)
                                break
                    else:
                        kapasite = "Bilinmiyor"
                except Exception as e:
                    print(f"Kapasite bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                    kapasite = "Bilinmiyor"
            # Eğer kapasite bulunmuşsa, standart formata çevir
            if kapasite != "Bilinmiyor":
                kapasite = kapasite_formatlari.get(kapasite.lower(), "Bilinmiyor")

            # Ürün detayına giderek satıcı bilgilerini al
            driver.execute_script("window.open(arguments[0], '_blank');", urun_url_text)  # Yeni sekmede aç
            driver.switch_to.window(driver.window_handles[-1])  # Yeni sekmeye geç

            try:
                # Model bilgisini çek
                model_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='raeVnaSg0g9mMFTxKLRf']//h1[@data-test-id='title']"))
                )
                model_full = model_element.text.strip()
                # Marka adını model bilgisinden çıkar
                if marka.lower() in model_full.lower():  # Marka adı küçük-büyük harf farkını göz ardı ederek kontrol edilir
                    model = model_full.lower().replace(marka.lower(), "").strip().capitalize()
                else:
                    model = model_full

                # Model uzunluğunu 100 karakterle sınırla
                model = model[:100]  # İlk 100 karakteri alın
                   
            except Exception as e:
                print(f"Model bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                model = "Bilinmiyor"

            try:
                # Satıcı bilgisini çek
                satici_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.lZIamyT3gZHA5DDxZZx_ > a.W5OUPzvBGtzo9IdLz4Li > span"))
                )
                satici = satici_element.text.strip()
            except Exception as e:
                print(f"Satıcı bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                satici = "Bilinmiyor"



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
                # Dikkat bilgisi kontrolü
                dikkat_element = driver.find_elements(By.XPATH, "//div[contains(@class, 'AxM3TmSghcDRH1F871Vh')]//span")
                if dikkat_element and "50 adetten az" in dikkat_element[0].text.lower():
                    dikkat = "Tükenmek Üzere"
                else:
                    dikkat = None
            except Exception as e:
                print(f"Dikkat bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                dikkat = "Stokta"

                 # RAM bilgisini çek
            try:
                ram_element = driver.find_element(By.XPATH, "//div[text()='Ram (Sistem Belleği)']/following-sibling::div//a")
                ram = ram_element.get_attribute("title").strip()
            except Exception as e:
                print(f"RAM bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                ram = "Bilinmiyor"
            try:
                # İşlemci tipi bilgisi çek
                islemci_element = driver.find_element(By.XPATH, "//div[text()='İşlemci Tipi']/following-sibling::div//a")
                islemci_tipi = islemci_element.get_attribute("title").strip()
            except Exception as e:
                print(f"İşlemci tipi bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                islemci_tipi = "Bilinmiyor"
            try:
                # İşlemci nesli bilgisi çek
                islemci_nesli_element = driver.find_element(By.XPATH, "//div[text()='İşlemci Nesli']/following-sibling::div//a")
                islemci_nesli = islemci_nesli_element.get_attribute("title").strip()
            except Exception as e:
                print(f"İşlemci nesli bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                islemci_nesli = "Bilinmiyor" 
            try:
                # İşlemci modeli bilgisi çek
                islemci_modeli_element = driver.find_element(By.XPATH, "//div[text()='İşlemci']/following-sibling::div//a")
                islemci_modeli = islemci_modeli_element.get_attribute("title").strip()
            except Exception as e:
                print(f"İşlemci modeli bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                islemci_modeli = "Bilinmiyor"  
            try:
                # Ekran Boyutu bilgisi çek
                ekran_boyutu_element = driver.find_element(By.XPATH, "//div[text()='Ekran Boyutu']/following-sibling::div//a")
                ekran_boyutu = ekran_boyutu_element.get_attribute("title").strip()
            except Exception as e:
                print(f"Ekran Boyutu bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                ekran_boyutu = "Bilinmiyor"   
            try:
                # Ekran Kartı bilgisi çek
                ekran_karti_element = driver.find_element(By.XPATH, "//div[text()='Ekran Kartı']/following-sibling::div//a")
                ekran_karti = ekran_karti_element.get_attribute("title").strip()
            except Exception as e:
                print(f"Ekran Kartı bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                ekran_karti = "Bilinmiyor" 
            try:
                # Kullanım Amacı bilgisi çek
                kullanim_amaci_element = WebDriverWait(driver, 10).until(
                kullanim_amaci_element = driver.find_element(By.XPATH, "//div[text()='Kullanım Amacı']/following-sibling::div//span")
                )
                kullanim_amaci = kullanim_amaci_element.text.strip()
            except Exception as e:
                print(f"Kullanım Amacı bilgisi alınamadı: {urun_url_text} - Hata: {str(e)}")
                try:
                    # Eğer Kullanım Amacı bulunamazsa Ürün Modeli bilgisi çek
                    urun_modeli_element = driver.find_element(By.XPATH, "//div[text()='Ürün Modeli']/following-sibling::div//span")
                    kullanim_amaci = urun_modeli_element.text.strip()
                except Exception as e2:
                    print(f"Ürün Modeli bilgisi alınamadı: {urun_url_text} - Hata: {str(e2)}")
                    kullanim_amaci = "Bilinmiyor"          

            guncelleme_tarihi = format_date(datetime.now()) 

            # Veritabanına ürün ekleme veya güncelleme işlemi
            def urun_veritabanina_kaydet(marka, model, yeni_fiyat, urun_url_text, urun_gorsel_url, satici, kapasite, kullanim_amaci, guncelleme_tarihi,
                                         kampanya, dikkat, ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti):
                # Ürünün veritabanında olup olmadığını kontrol et
                cursor.execute(
                    """
                    SELECT YeniFiyat FROM HepsiBuradaLaptop
                    WHERE Marka = ? AND Model = ? AND Depolama = ? AND UrunUrl = ?
                    """, 
                    marka, model, kapasite, urun_url_text
                )
                sonuc = cursor.fetchone()

                if sonuc:
                    # Ürün zaten varsa, fiyatını kontrol et ve güncelle
                    mevcut_fiyat = sonuc[0]
                  
                        # Eski fiyatı kaydedip yeni fiyatı güncelle
                    cursor.execute(
                        """
                       UPDATE HepsiBuradaLaptop 
                       SET EskiFiyat = YeniFiyat, YeniFiyat = ?, Satici = ?, Kampanya = ?, Dikkat = ?, Ram = ?, islemciTipi = ?, islemciNesli = ?, islemciModeli = ?, EkranEbat = ?, EkranKarti = ?, KullanimAmaci = ?, Guncellemetarihi = ?
                       WHERE Marka = ? AND Model = ? AND Depolama = ? AND UrunUrl = ? 
                       """,
                       (yeni_fiyat, satici, kampanya, dikkat, ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti, kullanim_amaci,guncelleme_tarihi, marka, model, kapasite, urun_url_text)
                    )
                
                else:
                    # Ürün yoksa yeni bir kayıt ekle
                    cursor.execute(
                        """
                        INSERT INTO HepsiBuradaLaptop (Marka, Model, YeniFiyat, EskiFiyat, Urunurl, Urungorsel, Satici, Depolama, Kampanya, Dikkat, Ram, islemciTipi, islemciNesli, islemciModeli, EkranEbat, EkranKarti, KullanimAmaci, Guncellemetarihi)
                        VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (marka, model, yeni_fiyat, urun_url_text, urun_gorsel_url, satici, kapasite, kampanya, dikkat, ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti, kullanim_amaci, guncelleme_tarihi)
                    )
                # Her işlemden sonra değişiklikleri veritabanına kaydet
                conn.commit()  # <<--- Burada veritabanı güncelleniyor

            # Ana döngü içinde ürünü veritabanına kaydet çağrısı
            urun_veritabanina_kaydet(
                marka, model, 
                float(fiyat_text.replace(" TL", "").replace(".", "").replace(",", ".")),  # Yeni fiyat
                urun_url_text, urun_gorsel_url,
                satici, kapasite, kullanim_amaci, guncelleme_tarihi, kampanya, dikkat,
                ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti
            )


            print(f"{counter + 1}. Marka: {marka}, Model: {model}, Fiyat: {fiyat_text}, Satıcı: {satici}, Kapasite: {kapasite},Guncelleme : {guncelleme_tarihi}, RAM: {ram}, islemciTipi: {islemci_tipi}, islemciNesli: {islemci_nesli}, islemciModeli: {islemci_modeli}, EkranEbat: {ekran_boyutu}, EkranKarti: {ekran_karti}, KullanimAmaci: {kullanim_amaci}, Kampanya: {kampanya}, Dikkat: {dikkat}, URL: {urun_url_text}")

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
