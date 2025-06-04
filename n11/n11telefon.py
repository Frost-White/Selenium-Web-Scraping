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
# N11 URL ve sayaçlar
base_url = "https://www.n11.com/telefon-ve-aksesuarlari/cep-telefonu?pg="
current_page = 1
counter = 0

def urun_veritabanina_kaydet(marka, model, fiyat, urun_url, gorsel_url, satici, renk, hafiza, kampanya, stok_durumu, org_fiyat):
    site_no = 3  # N11 için site numarası
    kategori_no = 1 if marka.lower() == "apple" else 2
    guncelleme_tarihi = datetime.now()

    if fiyat == 0.0 or not all([marka, model, urun_url, gorsel_url, satici, renk, hafiza, kampanya, stok_durumu]):
        print("Veri eksik veya fiyat 0, kayıt yapılmadı.")
        return

    cursor.execute("SELECT Fiyat FROM Urun WHERE Urunurl = ?", urun_url)
    sonuc = cursor.fetchone()

    if sonuc:
        cursor.execute("SELECT Fiyat, Urun_Id, Guncellemetarihi FROM Urun WHERE Urunurl = ?", urun_url)
        id_sonuc = cursor.fetchone()
        eski_fiyat = sonuc[0]
        urun_id = id_sonuc[1]
        onceki_tarih = id_sonuc[2]

        cursor.execute("INSERT INTO Urun_Eski_Fiyat (Urun_Id, Fiyat, Tarih) VALUES (?, ?, ?)", urun_id, eski_fiyat, onceki_tarih)
        cursor.execute("UPDATE Urun SET Fiyat = ?, Kampanya = ?, Stok = ?, Guncellemetarihi = ?, Org_Fiyat = ? WHERE Urunurl = ?",
                       fiyat, kampanya, stok_durumu, guncelleme_tarihi,org_fiyat, urun_url)
    else:
        cursor.execute("""
            INSERT INTO Urun (Marka, Model, Fiyat, Urunurl, Urungorsel, Satici, Kampanya, Stok, Guncellemetarihi, Site, Kategori, Org_Fiyat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        marka, model, fiyat, urun_url, gorsel_url, satici, kampanya, stok_durumu, guncelleme_tarihi, site_no, kategori_no,org_fiyat)

        cursor.execute("SELECT Urun_Id FROM Urun WHERE Urunurl = ?", urun_url)
        id_sonuc = cursor.fetchone()
        cursor.execute("INSERT INTO Mobil_Ekstra (Urun_Id, Renk, Hafıza) VALUES (?, ?, ?)", id_sonuc[0], renk, hafiza)

    conn.commit()

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

                # Yan sekmeye geçiş
                driver.execute_script("window.open(arguments[0]);", link)
                driver.switch_to.window(driver.window_handles[1])
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "prod-opt-hasLb-text")))

                # Ekstra özellikleri yüklemek için butona tıkla (eğer varsa)
                try:
                    daha_fazla_btn = driver.find_element(By.CLASS_NAME, "unf-prop-more-button")
                    driver.execute_script("arguments[0].click();", daha_fazla_btn)
                except:
                    pass

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "unf-prop-list")))

                # Renk ve hafıza bilgisi
                try:
                    r_h_container = driver.find_element(By.CLASS_NAME, "prod-opt-hasLb-text")
                    spanler = r_h_container.find_elements(By.TAG_NAME, "span")
                    renk = spanler[0].text.strip() if len(spanler) > 0 else ""
                    hafiza = spanler[1].text.strip() if len(spanler) > 1 else ""
                except:
                    renk = ""
                    hafiza = ""

                # Marka / Model bilgisi
                try:
                    prop_list = driver.find_element(By.CLASS_NAME, "unf-prop-list")
                    li_etiketleri = prop_list.find_elements(By.TAG_NAME, "li")
                    marka = ""
                    model = ""
                    for li in reversed(li_etiketleri):
                        p_tags = li.find_elements(By.TAG_NAME, "p")
                        if len(p_tags) >= 2:
                            label = p_tags[0].text.strip().lower()
                            value = p_tags[1].text.strip()
                            if "marka" in label:
                                marka = value
                            elif "model" in label:
                                model = value
                        if marka and model:
                            break
                except:
                    marka = ""
                    model = ""

                # Fiyat bilgisi
                try:
                    fiyat_container = driver.find_element(By.CLASS_NAME, "newPrice")
                    fiyat_raw = fiyat_container.find_element(By.TAG_NAME, "ins").text.strip()
                    fiyat_temiz = fiyat_raw.replace("TL", "").replace(".", "").replace(",", ".").strip()
                    fiyat = float(fiyat_temiz)
                except:
                    fiyat = 0.0

                # Ürün görseli
                try:
                    gorsel_div = driver.find_element(By.CLASS_NAME, "imgObj")
                    gorsel = gorsel_div.find_element(By.TAG_NAME, "img").get_attribute("src")
                except:
                    gorsel = ""

                try:
                    org_fiyat = driver.find_element(By.XPATH, "//div[@class='priceContainer']//del[@class='oldPrice']").text
                    org_fiyat = org_fiyat.replace('.', '').replace(',', '.').replace('TL', '').strip()
                    org_fiyat = float(org_fiyat)
                except:
                    org_fiyat = 0.0

                # Satıcı bilgisi
                try:
                    satici_element = driver.find_element(By.CLASS_NAME, "unf-p-seller-name")
                    satici = satici_element.text.strip()
                except:
                    satici = ""

                                # Stok durumu
                try:
                    stok_element = driver.find_element(By.CLASS_NAME, "stockWarning")
                    stok_durumu = stok_element.text.strip()
                except:
                    stok_durumu = "Stokta var"

                                # Kampanya bilgisi
                try:
                    kampanya_container = driver.find_element(By.CLASS_NAME, "unf-p-campaign-item")
                    kampanya = kampanya_container.find_element(By.TAG_NAME, "span").text.strip()
                except:
                    kampanya = "Yok"

                print(f"RENK: {renk} | HAFIZA: {hafiza} | MARKA: {marka} | MODEL: {model} | FİYAT: {fiyat} | GÖRSEL: {gorsel} | SATICI: {satici} | STOK: {stok_durumu} | KAMPANYA: {kampanya}")
                # Veritabanına kayıt
                urun_veritabanina_kaydet(
                    marka,
                    model,
                    fiyat,
                    link,
                    gorsel,
                    satici,
                    renk,
                    hafiza,
                    kampanya,
                    stok_durumu,
                    org_fiyat
                )
                # Sekmeyi kapat ve geri dön
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except:
                print("Ürün linki alınamadı")           
    except Exception as e:
        print("Sayfa ürünleri alınamadı:", e)

    current_page += 1
    counter += 1
    if len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(original_tab)

driver.quit()
