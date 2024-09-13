import os
import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Použijeme neinteraktivní backend
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import time
from flask import Flask, render_template
import threading

# Inicializace Flask aplikace
app = Flask(__name__)

# Konfigurace
OUTPUT_DIR = 'static/radar_images'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Funkce pro stažení souboru
def download_file(url, filename):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    else:
        print(f'Nepodařilo se stáhnout {url}')

# Funkce pro získání posledních 8 časových razítek v 5minutových intervalech
def get_last_timestamps():
    timestamps = []
    now = datetime.utcnow()
    # Zaokrouhlení na předchozí 5minutový interval
    minutes = (now.minute // 5) * 5
    now = now.replace(minute=minutes, second=0, microsecond=0)
    for i in range(8):
        timestamps.append(now - timedelta(minutes=5 * i))
    return timestamps[::-1]  # Otočíme pořadí, aby byly od nejstaršího po nejnovější

# Funkce pro zpracování HDF5 souboru a uložení jako JPG
def process_hdf5_file(hdf5_file, output_image):
    with h5py.File(hdf5_file, 'r') as f:
        # Zde upravte cestu k datasetu podle skutečné struktury HDF5 souboru
        data = f['dataset1/data1/data'][:]
        # Náhrada chybějících dat hodnotou NaN pro lepší vizualizaci
        data = np.where(data == -9999, np.nan, data)
        # Vykreslení dat
        plt.figure(figsize=(6, 6))
        plt.imshow(data, cmap='jet')
        plt.colorbar(label='Intenzita')
        plt.title('Radarový snímek')
        plt.axis('off')
        plt.savefig(output_image, bbox_inches='tight', pad_inches=0)
        plt.close()

# Funkce pro stažení a zpracování obrázků
def update_images():
    timestamps = get_last_timestamps()
    image_timestamps = [ts.strftime('%Y%m%d%H%M%S') for ts in timestamps]
    for ts in timestamps:
        time_str = ts.strftime('%Y%m%d%H%M%S')
        filename = f'T_PABV23_C_OKPR_{time_str}.hdf'
        url = f'https://opendata.chmi.cz/meteorology/weather/radar/composite/maxz/hdf5/{filename}'
        local_hdf5 = os.path.join(OUTPUT_DIR, filename)
        local_jpg = os.path.join(OUTPUT_DIR, f'{time_str}.jpg')

        # Stáhneme soubor, pokud neexistuje
        if not os.path.exists(local_hdf5):
            print(f'Stahuji {filename}...')
            download_file(url, local_hdf5)

        # Převedeme HDF5 na JPG
        if not os.path.exists(local_jpg):
            print(f'Zpracovávám {filename}...')
            process_hdf5_file(local_hdf5, local_jpg)

# Vlákno pro periodickou aktualizaci obrázků
def periodic_update(interval=300):
    while True:
        print('Aktualizuji obrázky...')
        update_images()
        time.sleep(interval)

# Flask route pro zobrazení animace
@app.route('/')
def index():
    # Získáme aktuální časová razítka obrázků
    timestamps = get_last_timestamps()
    image_timestamps = [ts.strftime('%Y%m%d%H%M%S') for ts in timestamps]
    # Vytvoříme cesty k obrázkům
    image_paths = [f'radar_images/{ts}.jpg' for ts in image_timestamps]
    return render_template('index.html', image_paths=image_paths)

if __name__ == '__main__':
    # Spustíme vlákno pro periodickou aktualizaci obrázků
    threading.Thread(target=periodic_update, daemon=True).start()
    # Spustíme Flask aplikaci s Gunicorn, pokud je dostupný
    try:
        from gunicorn.app.wsgiapp import run
        import sys
        sys.argv = ['gunicorn', '-w', '4', '-b', '0.0.0.0:5000', 'download_and_convert:app']
        run()
    except ImportError:
        # Pokud není Gunicorn nainstalován, spustíme vývojový server Flask
        app.run(host='0.0.0.0', port=5000)
