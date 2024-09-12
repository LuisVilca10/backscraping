import requests
from bs4 import BeautifulSoup
import schedule
import time
from firebase_admin import firestore
from firebase_admin import credentials
from datetime import datetime
import firebase_admin
import os
import base64
import json
from dotenv import load_dotenv

load_dotenv()
firebase_credentials_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")

if firebase_credentials_base64 is None:
    raise ValueError("No se pudo encontrar la variable de entorno FIREBASE_CREDENTIALS_BASE64.")

firebase_credentials_json = json.loads(base64.b64decode(firebase_credentials_base64))

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_json)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def noticia_existe(collection_name, titulo):
    try:
        noticias_ref = db.collection(collection_name).where('titulo', '==', titulo).stream()
        for noticia in noticias_ref:
            return True 
        return False
    except Exception as e:
        print(f"Error al verificar la existencia de la noticia: {e}")
        return False

def upload_to_firebase(collection_name, data):
    try:
        if not noticia_existe(collection_name, data['titulo']):
            db.collection(collection_name).add(data)
            print(f"Datos subidos a Firebase: {data}")
            return True
        else:
            print(f"Noticia ya existente: {data['titulo']}")
            return False
    except Exception as e:
        print(f"Error al subir a Firebase: {e}")
        return False


def scrape_tvsur():
    url = 'https://www.tvsur.com.pe/category/noticias/local/'
    response = requests.get(url)
    noticias = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title')
        date_elements = soup.find_all('time', class_='entry-date updated td-module-date')
        img_elements = soup.find_all('img', class_='entry-thumb')

        for title_element, img, date in zip(title_elements, img_elements, date_elements):
            article_url = title_element.find('a')['href']
            article_response = requests.get(article_url)

            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                title_tag = article_soup.find('h1', class_='entry-title')
                content_div = article_soup.find('div', class_='td-post-content')

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ' '.join([p.text.strip() for p in paragraphs])

                    data = {
                        'fecha': date.text.strip(),
                        'titulo': title_tag.text.strip(),
                        'fuente': 'TV SUR',
                        'descripcion': description,
                        'image': img.get('data-img-url', 'No Image')
                    }

                    noticias.append(data)

        # Subir noticias a Firebase
        if noticias:
            for noticia in noticias:
                upload_to_firebase('noticias', noticia)
            print("Scraping completado y datos subidos a Firebase")
        else:
            print("No se encontraron noticias.")
    else:
        print("Error al realizar scraping.")


def scraping_sinfronteras():
    url = 'https://diariosinfronteras.com.pe/category/puno/'
    response  = requests.get(url)
    noticiassf = []

    if response .status_code == 200:
        soup = BeautifulSoup(response .content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title')

        for title_element in title_elements:
            title = title_element.text.strip()
            article_url = title_element.find('a')['href']
            article_response = requests.get(article_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                image_element = article_soup.find('img', class_='attachment-bd-normal size-bd-normal wp-post-image')
                content_div = article_soup.find('div', class_='post-content-bd')
                image_url = image_element['src'] if image_element else 'No Image'

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ''

                    # Concatenar el texto de todos los párrafos
                    for paragraph in paragraphs:
                        description += paragraph.text.strip() + ' '
                    data = {
                            'fecha': datetime.now().strftime('%B %d, %Y'),
                            'titulo': title,
                            'fuente': 'Sin Fronteras',
                            'descripcion': description.strip(),
                            'image': image_url
                    }
                    noticiassf.append(data)
        if noticiassf:
            for noticia in noticiassf:
                upload_to_firebase('noticias', noticia)
            print("Scraping completado y datos subidos a Firebase")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error')



def scraping_andes():
    url = 'https://losandes.com.pe/category/regional/'
    response  = requests.get(url)
    noticiasandes = []

    if response .status_code == 200:
        soup = BeautifulSoup(response .content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title td-module-title')
        img_elements = soup.find_all('span', class_='entry-thumb td-thumb-css')
        date_elements = soup.find_all('time', class_='entry-date updated td-module-date')

        for title_element, img, date in zip(title_elements, img_elements, date_elements):
            title = title_element.text.strip()
            article_url = title_element.find('a')['href']
            image_url = img.get('data-img-url')
            article_response = requests.get(article_url)
            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                content_div = article_soup.find('div', class_='td_block_wrap tdb_single_content tdi_107 td-pb-border-top td_block_template_1 td-post-content tagdiv-type')
                data_img_url = img.get('data-img-url')

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ''

                    # Concatenar el texto de todos los párrafos
                    for paragraph in paragraphs:
                        description += paragraph.text.strip() + ' '

                    print(f"Title: {title}")
                    print(image_url)
                    print("fecha: " + date.text.strip())
                    print(f"Description: {description.strip()}\n")

                    data = {
                            'fecha': date.text.strip(),
                            'titulo': title,
                            'fuente': 'Los Andes',
                            'descripcion': description.strip(),
                            'image': image_url
                    }
                    noticiasandes.append(data)
        if noticiasandes:
            for noticia in noticiasandes:
                upload_to_firebase('noticias', noticia)
            print("Scraping completado y datos subidos a Firebase")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error')

# Programación del scraping cada 10 minutos (más razonable)
schedule.every(0.001).minutes.do(scrape_tvsur)
schedule.every(0.001).minutes.do(scraping_sinfronteras)
schedule.every(0.001).minutes.do(scraping_andes)

# Bucle para ejecutar las tareas programadas
while True:
    schedule.run_pending()
    time.sleep(1)
