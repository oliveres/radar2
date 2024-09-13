# Použijeme oficiální Python image
FROM python:3.10-slim

# Nastavíme pracovní adresář
WORKDIR /app

# Zkopírujeme soubory aplikace
COPY app /app

# Instalujeme závislosti
RUN pip install --no-cache-dir -r requirements.txt

# Exponujeme port
EXPOSE 5000

# Spustíme Flask aplikaci
CMD ["python", "download_and_convert.py"]
