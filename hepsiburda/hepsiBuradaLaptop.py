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
driver.set_window_size(1024, 768)  # Genişlik: 1024px, Yükseklik: 768px

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
        kampanya_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-test-id='price']//span[contains(text(), 'kazanç') or contains(text(), 'indirim') or contains(text(), 'kampanya')]"))
        )
        return kampanya_element.text.strip()
    except:
        try:
            # Diğer kampanya metinlerini ara
            kampanya_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'kazanç') or contains(text(), 'indirim') or contains(text(), 'kampanya')]"))
            )
            return kampanya_element.text.strip()
        except:
            return "Yok"

# Ürün bilgilerini çekme ve veritabanına kaydetme
while counter < max_urun_sayisi:
    try:
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

        # Elementleri yeniden bul
        urunler = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//h2[@class='title-module_titleRoot__dNDiZ']"))
        )
        fiyatlar = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='price-module_finalPrice__LtjvY']"))
        )
        urun_url = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[@class='productCardLink-module_productCardLink__GZ3eU']"))
        )
        urun_gorseller = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//picture//img[@class='hbImageView-module_hbImage__Ca3xO']"))
        )

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
            try:
                fiyat_text = fiyat.text.strip()
                urun_url_text = url_eleman.get_attribute("href")
                urun_gorsel_url = gorsel.get_attribute("src")

                if fiyat_text:
                    urun_text = urun.text.strip()
                    urun_text_split = urun_text.split()
                    marka = urun_text_split[0]
                    model = " ".join(urun_text_split[1:])

                    # Kapasite bilgisini başlıktan çek
                    kapasite = next((k for k in kapasite_listesi if k in urun_text.lower()), "Bilinmiyor")

                    # Eğer kapasite bilgisi bulamazsa, yeni HTML yapısından kapasiteyi al
                    if kapasite == "Bilinmiyor":
                        try:
                            kapasite_elements = WebDriverWait(driver, 5).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='jkj4C4LML4qv2Iq8GkL3']//div[text()='SSD Kapasitesi']/following-sibling::div//span"))
                            )
                            if kapasite_elements:
                                for element in kapasite_elements:
                                    kapasite_text = element.text.strip().lower()
                                    if any(k in kapasite_text for k in kapasite_listesi):
                                        kapasite = next(k for k in kapasite_listesi if k in kapasite_text)
                                        break
                        except:
                            kapasite = "Bilinmiyor"

                    if kapasite != "Bilinmiyor":
                        kapasite = kapasite_formatlari.get(kapasite.lower(), "Bilinmiyor")

                    # Ürün detayına giderek satıcı bilgilerini al
                    driver.execute_script("window.open(arguments[0], '_blank');", urun_url_text)
                    driver.switch_to.window(driver.window_handles[-1])

                    try:
                        # Model bilgisini çek
                        model_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@class='raeVnaSg0g9mMFTxKLRf']//h1[@data-test-id='title']"))
                        )
                        model_full = model_element.text.strip()
                        if marka.lower() in model_full.lower():
                            model = model_full.lower().replace(marka.lower(), "").strip().capitalize()
                        else:
                            model = model_full
                        model = model[:100]
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

                    # Fiyat bilgilerini çek
                    new_price_str, old_price_str = extract_price_from_html(driver)
                    new_price = format_price(new_price_str)
                    old_price = format_price(old_price_str)

                    # Kampanya bilgisini çek
                    kampanya = extract_kampanya(driver)

                    # Stok bilgisini kontrol et
                    try:
                        stok_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[@class='ttVQfRCD0ugwrs65whKO _pGf4dDvGK0tdoimtqWf']"))
                        )
                        stok_yazisi = stok_element.text.strip().lower()
                        stok_durumu = "yok" if "stoklarda olacaktır" in stok_yazisi else "var"
                    except:
                        stok_durumu = "var"

                    # Dikkat bilgisi kontrolü
                    try:
                        dikkat_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'AxM3TmSghcDRH1F871Vh')]//span"))
                        )
                        dikkat = "Tükenmek Üzere" if "50 adetten az" in dikkat_element.text.lower() else None
                    except:
                        dikkat = "Stokta"

                    # RAM bilgisini çek
                    try:
                        ram_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[text()='Ram (Sistem Belleği)']/following-sibling::div//a"))
                        )
                        ram = ram_element.get_attribute("title").strip()
                    except:
                        ram = "Bilinmiyor"

                    # İşlemci tipi bilgisi çek
                    try:
                        islemci_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[text()='İşlemci Tipi']/following-sibling::div//a"))
                        )
                        islemci_tipi = islemci_element.get_attribute("title").strip()
                    except:
                        islemci_tipi = "Bilinmiyor"

                    # İşlemci nesli bilgisi çek
                    try:
                        islemci_nesli_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[text()='İşlemci Nesli']/following-sibling::div//a"))
                        )
                        islemci_nesli = islemci_nesli_element.get_attribute("title").strip()
                    except:
                        islemci_nesli = "Bilinmiyor"

                    # İşlemci modeli bilgisi çek
                    try:
                        islemci_modeli_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[text()='İşlemci']/following-sibling::div//a"))
                        )
                        islemci_modeli = islemci_modeli_element.get_attribute("title").strip()
                    except:
                        islemci_modeli = "Bilinmiyor"

                    # Ekran Boyutu bilgisi çek
                    try:
                        ekran_boyutu_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[text()='Ekran Boyutu']/following-sibling::div//a"))
                        )
                        ekran_boyutu = ekran_boyutu_element.get_attribute("title").strip()
                    except:
                        ekran_boyutu = "Bilinmiyor"

                    # Ekran Kartı bilgisi çek
                    try:
                        ekran_karti_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[text()='Ekran Kartı']/following-sibling::div//a"))
                        )
                        ekran_karti = ekran_karti_element.get_attribute("title").strip()
                    except:
                        ekran_karti = "Bilinmiyor"

                    # Kullanım Amacı bilgisi çek
                    try:
                        kullanim_amaci_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//div[text()='Kullanım Amacı']/following-sibling::div//span"))
                        )
                        kullanim_amaci = kullanim_amaci_element.text.strip()
                    except:
                        try:
                            kullanim_amaci_element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[text()='Ürün Modeli']/following-sibling::div//span"))
                            )
                            kullanim_amaci = kullanim_amaci_element.text.strip()
                        except:
                            kullanim_amaci = "Bilinmiyor"

                    guncelleme_tarihi = datetime.now()

                    # Veritabanına ürün ekleme veya güncelleme işlemi
                    def urun_veritabanina_kaydet(marka, model, yeni_fiyat, eski_fiyat, urun_url_text, urun_gorsel_url, satici, kapasite, kullanim_amaci, guncelleme_tarihi,
                                                kampanya, dikkat, ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti):
                        site_no = 2
                        kategori_no = 4
                        try:
                            # Ürünün veritabanında olup olmadığını kontrol et
                            cursor.execute(
                                """
                                SELECT Fiyat FROM Urun
                                WHERE UrunUrl = ?
                                """, 
                                urun_url_text
                            )
                            sonuc = cursor.fetchone()

                            if sonuc:
                                # Ürün zaten varsa, fiyatını kontrol et ve güncelle
                                mevcut_fiyat = sonuc[0]
                                
                                # Eğer HTML'den eski fiyat gelmediyse, mevcut yeni fiyatı eski fiyat olarak kullan
                                if eski_fiyat is None:
                                    eski_fiyat = mevcut_fiyat
                                
                                cursor.execute(
                                    """
                                    UPDATE Urun 
                                    SET Org_Fiyat = ?, Fiyat = ?, Satici = ?, Stok = ?, Kampanya = ?, Guncellemetarihi = ?
                                    WHERE UrunUrl = ?
                                    """,
                                    eski_fiyat, yeni_fiyat, satici, dikkat, kampanya, guncelleme_tarihi, urun_url_text
                                )
                            else:
                                # Ürün yoksa yeni bir kayıt ekle
                                cursor.execute(
                                    """
                                    INSERT INTO Urun (Marka, Model, Fiyat, Org_Fiyat, Urunurl, Urungorsel, Satici, Kampanya, Stok, Guncellemetarihi, Site, Kategori)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    marka, model, yeni_fiyat, eski_fiyat, urun_url_text, urun_gorsel_url, satici, kampanya, dikkat, guncelleme_tarihi, site_no, kategori_no
                                )
                                cursor.execute("SELECT Urun_Id FROM Urun WHERE Urunurl = ?", urun_url_text)
                                id_sonuc = cursor.fetchone()
                                cursor.execute(
                                    """
                                    INSERT INTO Laptop_Ekstra (Urun_Id, Hafıza, Ram, islemciTipi, islemciNesli, islemciModeli, EkranEbat, EkranKarti, KullanimAmaci)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    id_sonuc[0], kapasite, ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti, kullanim_amaci
                                )
                                # Her işlemden sonra değişiklikleri veritabanına kaydet
                                conn.commit()
                        except Exception as e:
                            print(f"Veritabanı işlemi sırasında hata oluştu: {str(e)}")
                            conn.rollback()

                    # Ana döngü içinde ürünü veritabanına kaydet çağrısı
                    urun_veritabanina_kaydet(
                        marka, model, 
                        new_price,  # Yeni fiyat
                        old_price,  # Eski fiyat
                        urun_url_text, urun_gorsel_url,
                        satici, kapasite, kullanim_amaci, guncelleme_tarihi, kampanya, stok_durumu,
                        ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti
                    )

                    print(f"{counter + 1}. Marka: {marka}, Model: {model}, Yeni Fiyat: {new_price}, Eski Fiyat: {old_price}, Satıcı: {satici}, Kapasite: {kapasite}, Guncelleme: {guncelleme_tarihi}, RAM: {ram}, islemciTipi: {islemci_tipi}, islemciNesli: {islemci_nesli}, islemciModeli: {islemci_modeli}, EkranEbat: {ekran_boyutu}, EkranKarti: {ekran_karti}, KullanimAmaci: {kullanim_amaci}, Kampanya: {kampanya}, Dikkat: {dikkat}, URL: {urun_url_text}")

                    # Ürün sayfasını kapat ve ana sekmeye dön
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                    counter += 1
                    if counter >= max_urun_sayisi:
                        break

            except Exception as e:
                print(f"Ürün işlenirken hata oluştu: {str(e)}")
                continue

        # Sayfalar arasında geçiş yap
        current_page += 1

    except Exception as e:
        print(f"Sayfa işlenirken hata oluştu: {str(e)}")
        current_page += 1
        continue

# Veritabanı bağlantısını kapat
conn.commit()
cursor.close()
conn.close()

# Tarayıcıyı kapat
driver.quit()
