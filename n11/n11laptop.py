from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
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
chrome_options.add_argument("--enable-unsafe-swiftshader")

# ChromeDriver başlatılıyor
driver = webdriver.Chrome(service=Service("C:\\Users\\syuce\\Desktop\\bitirme_projesi_veri_cekme\\Selenium-Web-Scraping\\n11\\chromedriver.exe"), options=chrome_options)
driver.maximize_window()

original_tab = driver.current_window_handle

# N11 Laptop URL ve sayaçlar
base_url = "https://www.n11.com/bilgisayar/dizustu-bilgisayar?pg="
current_page = 1
counter = 0

def urun_veritabanina_kaydet(marka, model, yeni_fiyat, urun_url_text, urun_gorsel_url, satici, kapasite, kullanim_amaci, guncelleme_tarihi,
                              kampanya, ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_boyutu, ekran_karti, stok, org_fiyat):

            site_no = 2
            kategori_no = 4
            # Fiyat 0 ise veya herhangi bir değer boşsa kaydetme
            if yeni_fiyat == 0.0 or not all([marka, model, urun_url_text,ram, islemci_tipi, islemci_nesli,
                                                  islemci_modeli, ekran_boyutu, ekran_karti,
                                                  kullanim_amaci, urun_gorsel_url, satici, kapasite, kampanya, stok]):
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, marka, model, yeni_fiyat, urun_url_text, urun_gorsel_url, satici, kampanya, stok, guncelleme_tarihi, site_no, kategori_no, org_fiyat)

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

while counter < 200:
    print(f"Sayfa: {current_page}")
    url = f"{base_url}{current_page}"
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.column")))

    try:
        urun_kartlari = driver.find_elements(By.CLASS_NAME, "column")

        for urun in urun_kartlari:
            try:
                link_element = urun.find_element(By.CSS_SELECTOR, "div.pro > a")
                link = link_element.get_attribute("href")
                print("Ürün linki:", link)

                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[1])
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "unf-prop-more-button")))

                try:
                    daha_fazla_btn = driver.find_element(By.CLASS_NAME, "unf-prop-more-button")
                    driver.execute_script("arguments[0].click();", daha_fazla_btn)
                except Exception as e:
                    print("[!] Daha fazla özellik butonu bulunamadı:", e)

                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "unf-prop-list")))
                except Exception as e:
                    print("[!] Özellik listesi yüklenmedi:", e)
                
                islemci_nesli = "Bilinmiyor"

                try:
                    prop_list = driver.find_element(By.CLASS_NAME, "unf-prop-list")
                    li_etiketleri = prop_list.find_elements(By.TAG_NAME, "li")
                    marka = ""
                    model = ""
                    hafiza = ""
                    ram = ""
                    islemci_tipi = ""
                    islemci_modeli = ""
                    ekran_karti = ""
                    ekran_ebat = ""
                    for li in reversed(li_etiketleri):
                        p_tags = li.find_elements(By.TAG_NAME, "p")
                        if len(p_tags) >= 2:
                            label = p_tags[0].text.strip()
                            value = p_tags[1].text.strip()
                            if "Marka" in label:
                                marka = value
                            elif "Model" == label:
                                model = value
                            elif "Disk Kapasitesi" in label:
                                hafiza = value
                            elif "Bellek Kapasitesi" in label:
                                ram = value
                            elif "İşlemci" == label:
                                islemci_tipi = value
                            elif "İşlemci Modeli" in label:
                                islemci_modeli = value
                            elif "Ekran Kartı Modeli" in label:
                                ekran_karti = value
                            elif "Ekran Boyutu" in label:
                                ekran_ebat = value
                            elif "Oyuncu" == label:
                                kullanim_amaci = value
                        if marka and model and hafiza and ram and islemci_tipi and islemci_modeli and ekran_karti and ekran_ebat and kullanim_amaci:
                            break
                except Exception as e:
                    print("[!] Marka ve model bulunamadı:", e)
                try:
                    fiyat_container = driver.find_element(By.CLASS_NAME, "newPrice")
                    fiyat_raw = fiyat_container.find_element(By.TAG_NAME, "ins").text.strip()
                    fiyat_temiz = fiyat_raw.replace("TL", "").replace(".", "").replace(",", ".").strip()
                    fiyat = float(fiyat_temiz)
                except Exception as e:
                    print("[!] Fiyat bulunamadı:", e)
                    fiyat = 0.0

                try:
                    org_fiyat = driver.find_element(By.XPATH, "//div[@class='priceContainer']//del[@class='oldPrice']").text
                    org_fiyat = org_fiyat.replace('.', '').replace(',', '.').replace('TL', '').strip()
                    org_fiyat = float(org_fiyat)
                except:
                    org_fiyat = 0.0

                try:
                    gorsel_div = driver.find_element(By.CLASS_NAME, "imgObj")
                    gorsel = gorsel_div.find_element(By.TAG_NAME, "img").get_attribute("src")
                except Exception as e:
                    print("[!] Görsel bulunamadı:", e)
                    gorsel = ""

                try:
                    satici_element = driver.find_element(By.CLASS_NAME, "unf-p-seller-name")
                    satici = satici_element.text.strip()
                except Exception as e:
                    print("[!] Satıcı bilgisi bulunamadı:", e)
                    satici = ""

                try:
                    stok_element = driver.find_element(By.CLASS_NAME, "stockWarning")
                    stok_durumu = stok_element.text.strip()
                except Exception as e:
                    stok_durumu = "Stokta var"

                try:
                    kampanya_container = driver.find_element(By.CLASS_NAME, "unf-p-campaign-item")
                    kampanya = kampanya_container.find_element(By.TAG_NAME, "span").text.strip()
                except Exception as e:
                    kampanya = "Yok"
                
                guncelleme_tarihi = datetime.now()
                print(f"HAFIZA: {hafiza} | RAM: {ram} | MARKA: {marka} | MODEL: {model} | İŞLEMCİ TİPİ: {islemci_tipi} | İŞLEMCİ MODELİ: {islemci_modeli} | EKRAN KARTI: {ekran_karti} | EKRAN BOYUTU: {ekran_ebat} | FİYAT: {fiyat} | GÖRSEL: {gorsel} | SATICI: {satici} | STOK: {stok_durumu} | KAMPANYA: {kampanya}\nLINK: {link}\n")

            except Exception as e:
                print("[!] Ürün detay sayfasında hata:", e)
            finally:
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(original_tab)
                    urun_veritabanina_kaydet(
                    marka, model, 
                    fiyat,  # Yeni fiyat
                    link, gorsel,
                    satici, hafiza, kullanim_amaci, guncelleme_tarihi, kampanya,
                    ram, islemci_tipi, islemci_nesli, islemci_modeli, ekran_ebat, ekran_karti, stok_durumu,
                    org_fiyat
                    )   
                    counter += 1
    except Exception as e:
        print("Sayfa ürünleri alınamadı:", e)

    current_page += 1

driver.quit()
