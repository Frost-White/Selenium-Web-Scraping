from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pyodbc

# SQL Server bağlantısı
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
chrome_options.add_argument("--headless")
chrome_options.add_argument("--enable-unsafe-swiftshader")
# ChromeDriver başlatılıyor
driver = webdriver.Chrome(service=Service("C:\\Users\\syuce\\Desktop\\bitirme_projesi_veri_cekme\\Selenium-Web-Scraping\\trendyol\\chromedriver.exe"), options=chrome_options)
driver.maximize_window()

from datetime import datetime

def urun_veritabanina_kaydet(marka, model, yeni_fiyat, urun_url_text, urun_gorsel_url, satici, kapasite, kullanim_amaci, guncelleme_tarihi,
                                         kampanya, ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti, stok, org_fiyat):
                site_no = 1
                kategori_no = 4
                # Fiyat 0 ise veya herhangi bir değer boşsa kaydetme
                if yeni_fiyat == 0.0 or not all([marka, model, urun_url_text,ram, islemci_tipi, islemci_nesli,
                                                  islemci_modeli, ekran_boyutu, ekran_karti,
                                                  kullanim_amaci, urun_gorsel_url, satici, kapasite, kampanya, stok, ram]):
                    print("Veri eksik veya fiyat 0, kayıt yapılmadı.")
                    return

                cursor.execute("SELECT Fiyat FROM Urun WHERE Urunurl = ?", urun_url_text)
                sonuc = cursor.fetchone()

                if sonuc:
                    cursor.execute("SELECT Fiyat, Urun_Id, Guncellemetarihi FROM Urun WHERE Urunurl = ?", urun_url_text)
                    id_sonuc = cursor.fetchone()
                    fiyat = sonuc[0]
                    urun_id = id_sonuc[1]
                    tarih = id_sonuc[2]
                    cursor.execute("INSERT INTO Urun_Eski_Fiyat (Urun_Id, Fiyat, Tarih) Values (?, ?, ?)", urun_id, fiyat, tarih)
                    cursor.execute("UPDATE Urun SET Fiyat = ?, Kampanya = ?, Stok = ?, Guncellemetarihi = ?, Org_Fiyat = ? WHERE Urunurl = ?",
                       yeni_fiyat, kampanya, stok, guncelleme_tarihi, org_fiyat, urun_url_text)
                               
                else:
                    # Ürün yoksa yeni bir kayıt ekle
                    cursor.execute("""
                    INSERT INTO Urun (Marka, Model, Fiyat, Urunurl, Urungorsel, Satici, Kampanya, Stok, Guncellemetarihi, Site, Kategori, Org_Fiyat)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    marka, model, yeni_fiyat, urun_url_text, urun_gorsel_url, satici, kampanya, stok, guncelleme_tarihi, site_no, kategori_no, org_fiyat)
                   
                    cursor.execute("SELECT Urun_Id FROM Urun WHERE Urunurl = ?", urun_url_text)
                    id_sonuc = cursor.fetchone()
                    cursor.execute(
                        """
                        INSERT INTO Laptop_Ekstra (Urun_Id,Hafıza, Ram, islemciTipi, islemciNesli, islemciModeli, EkranEbat, EkranKarti, KullanimAmaci)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (id_sonuc[0],kapasite, ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti, kullanim_amaci)
                    )
                # Her işlemden sonra değişiklikleri veritabanına kaydet
                conn.commit()  # <<--- Burada veritabanı güncelleniyor

# URL ve sayaçlar
base_url = "https://www.trendyol.com/laptop-x-c103108?pi="
max_urun_sayisi = 200
current_page = 1
counter = 0

# Veri çekme döngüsü
while counter < max_urun_sayisi:
    print(f"Sayfa: {current_page} - Toplam Ürün: {counter}")
    url = f"{base_url}{current_page}"
    driver.get(url)
    time.sleep(3)

    try:
        urunler = driver.find_elements(By.CLASS_NAME, "p-card-wrppr")

        for urun in urunler:
            if counter >= max_urun_sayisi:
                break

            try:
                link = urun.find_element(By.CLASS_NAME, "p-card-chldrn-cntnr.card-border").get_attribute("href")

                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[1])

                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h2[@class='title']")))

                    marka = driver.find_element(By.XPATH, "//h1[@class='pr-new-br']/a").text
                    model = driver.find_element(By.XPATH, "//h1[@class='pr-new-br']/span").text

                    try:
                        kampanya = driver.find_element(By.CLASS_NAME, "gallery-badge-left-text").text
                    except:
                        kampanya = "yok"

                    try:
                        stok = driver.find_element(By.CLASS_NAME, "stock-warning-badge-text").text
                    except:
                        stok = "Stokta var"

                    try:
                        gorsel = driver.find_element(By.XPATH, "//div[@class='product-image-container']//img").get_attribute("src")
                    except:
                        gorsel = ""

                    try:
                        fiyat = driver.find_element(By.CLASS_NAME, "prc-dsc").text
                    except:
                        fiyat = ""

                    fiyat = fiyat.replace('.', '').replace(',', '.').replace('TL', '').strip()
                    try:
                        fiyat = float(fiyat)
                    except:
                        fiyat = 0.0

                    try:
                        org_fiyat = driver.find_element(By.XPATH, "//div[@class='pr-in-cn']//span[@class='prc-org']").text
                        org_fiyat = org_fiyat.replace('.', '').replace(',', '.').replace('TL', '').strip()
                        org_fiyat = float(org_fiyat)
                    except:
                        org_fiyat = 0.0

                    try:
                        magaza = driver.find_element(By.CLASS_NAME, "seller-name-text").text
                    except:
                        magaza = ""

                except Exception as e:
                    print("Detay sayfası verileri alınamadı:", e)
                    marka = model = fiyat = magaza = gorsel = kampanya = ram = hafiza = ""
                
                try:
                    detay_ozellikler = driver.find_elements(By.XPATH, "//ul[@class='detail-attr-container']/li")
                    islemci_tipi = islemci_nesli = islemci_modeli = ekran_karti = ekran_boyutu = kullanim_amaci = ""

                    for li in detay_ozellikler:
                        spans = li.find_elements(By.TAG_NAME, "span")
                        if len(spans) >= 2:
                            ozellik_adi = spans[0].text.strip()
                            ozellik_degeri = spans[1].get_attribute("title").strip()

                            if "İşlemci Tipi" in ozellik_adi:
                                islemci_tipi = ozellik_degeri
                            elif "İşlemci Nesli" in ozellik_adi:
                                islemci_nesli = ozellik_degeri
                            elif "İşlemci Modeli" in ozellik_adi:
                                islemci_modeli = ozellik_degeri
                            elif "Ekran Kartı" == ozellik_adi:
                                ekran_karti = ozellik_degeri
                            elif "Ekran Boyutu" in ozellik_adi:
                                ekran_boyutu = ozellik_degeri
                            elif "Kullanım Amacı" in ozellik_adi:
                                kullanim_amaci = ozellik_degeri
                            elif "SSD Kapasitesi" in ozellik_adi:
                                hafiza = ozellik_degeri
                            elif "Ram (Sistem Belleği)" == ozellik_adi:
                                ram = ozellik_degeri 

                    if not ekran_karti:
                        ekran_karti = "Dahili"
                except Exception as e:
                    print("Donanım bilgileri alınamadı:", e)
                    ekran_karti = "Dahili"



                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                guncelleme_tarihi = datetime.now()
                urun_veritabanina_kaydet(
                    marka, model, 
                    fiyat,  # Yeni fiyat
                    link, gorsel,
                    magaza, hafiza, kullanim_amaci, guncelleme_tarihi, kampanya,
                    ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti, stok, org_fiyat
                )
                print(f"{counter+1}: {marka} | {model} | {fiyat} | {magaza} | {link} | {gorsel} | {guncelleme_tarihi} | {stok} | {kampanya} | {kullanim_amaci} | {hafiza} | {ekran_boyutu} | {ekran_karti} | {islemci_modeli} | {islemci_nesli} | {islemci_tipi}")

                counter += 1

            except Exception as e:
                print("Ürün işlenirken hata:", e)

    except Exception as e:
        print("Sayfa ürünleri alınamadı:", e)

    current_page += 1
