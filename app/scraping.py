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

def scraping_sinfronterasdeportes():
    url = 'https://diariosinfronteras.com.pe/category/deportes/'
    response = requests.get(url)
    noticiassf = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
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
                upload_to_firebase('deportes', noticia)
            print("Scraping completado y datos subidos a Firebase")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al acceder a la página')




def scraping_andes_deportes():
    url = 'https://losandes.com.pe/category/deportes/'
    response = requests.get(url)
    noticias_andes = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
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

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ''

                    # Concatenar el texto de todos los párrafos
                    for paragraph in paragraphs:
                        description += paragraph.text.strip() + ' '

                    data = {
                        'fecha': date.text.strip(),
                        'titulo': title,
                        'fuente': 'Los Andes',
                        'descripcion': description.strip(),
                        'image': image_url
                    }
                    noticias_andes.append(data)

        if noticias_andes:
            for noticia in noticias_andes:
                upload_to_firebase('deportes', noticia)
            print("Scraping completado y datos subidos a Firebase")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al acceder a la página')

def scraping_andes_politica():
    url = 'https://losandes.com.pe/category/politica/'
    response = requests.get(url)
    noticias_politica = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
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

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ''

                    # Concatenar el texto de todos los párrafos
                    for paragraph in paragraphs:
                        description += paragraph.text.strip() + ' '

                    data = {
                        'fecha': date.text.strip(),
                        'titulo': title,
                        'fuente': 'Los Andes',
                        'descripcion': description.strip(),
                        'image': image_url
                    }
                    noticias_politica.append(data)

        if noticias_politica:
            for noticia in noticias_politica:
                upload_to_firebase('politica', noticia)
            print("Scraping completado y datos subidos a Firebase")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al acceder a la página')

def scraping_sinfronteras_politica():
    url = 'https://diariosinfronteras.com.pe/category/politica/'
    response = requests.get(url)
    noticias_politica = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
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
                        'fecha': 'septiembre 4, 2024',  # Puedes ajustar esto según necesites
                        'titulo': title,
                        'fuente': 'Sin Fronteras',
                        'descripcion': description.strip(),
                        'image': image_url
                    }
                    noticias_politica.append(data)

        if noticias_politica:
            for noticia in noticias_politica:
                upload_to_firebase('politica', noticia)
            print("Scraping completado y datos subidos a Firebase")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al acceder a la página')
        
def scraping_tvsur_politica():
    url = 'https://www.tvsur.com.pe/category/noticias/nacional/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        title_elements = soup.find_all('h3', class_='entry-title')
        date_elements = soup.find_all('time', class_='entry-date updated td-module-date')
        img_elements = soup.find_all('img', class_='entry-thumb')

        noticias = []

        for title_element, img, date in zip(title_elements, img_elements, date_elements):
            article_url = title_element.find('a')['href']
            article_response = requests.get(article_url)

            if article_response.status_code == 200:
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                title_tag = article_soup.find('h1', class_='entry-title')
                content_div = article_soup.find('div', class_='td-post-content')
                title = title_tag.text.strip()

                if content_div:
                    paragraphs = content_div.find_all('p')
                    description = ''

                    # Concatenar el texto de todos los párrafos
                    for paragraph in paragraphs:
                        description += paragraph.text.strip() + ' '

                    # Verificar y limpiar la descripción
                    description = description.encode('utf-8', 'ignore').decode('utf-8')
                    data_img_url = img.get('data-img-url', 'No Image')

                    print(f"Title: {title}")
                    print(f"Image: {data_img_url}")
                    print(f"Description: {description.strip()}")
                    print("Fecha: " + date.text.strip())

                    data = {
                        'fecha': date.text.strip(),
                        'titulo': title,
                        'fuente': 'TV SUR',
                        'descripcion': description.strip(),
                        'image': data_img_url
                    }

                    noticias.append(data)

                else:
                    print("Error al encontrar el contenido de la noticia.")
            else:
                print("Error al acceder al artículo.")

        if noticias:
            for noticia in noticias:
                upload_to_firebase('politica', noticia)  # Cambiar a la colección que necesites
            print("Scraping completado y datos subidos a Firebase.")
        else:
            print("No se encontraron noticias.")
    else:
        print('Error al acceder a la página.')

def scraping_marca_futbol_internacional():
    url = 'https://www.marca.com/futbol/futbol-internacional.html'
    response = requests.get(url)
    response.raise_for_status()  # Verifica que la solicitud fue exitosa

    soup = BeautifulSoup(response.text, 'html.parser')

    # Encuentra todos los artículos de noticias
    articles = soup.find_all('div', class_='ue-c-cover-content__body')

    noticias = []

    for article in articles:
        # Extrae el título y el enlace
        headline_group = article.find('header', class_='ue-c-cover-content__headline-group')
        if headline_group:
            link_tag = headline_group.find('a', class_='ue-c-cover-content__link')
            if link_tag:
                titulo = link_tag.get_text(strip=True)
                enlace = link_tag['href']
                if not enlace.startswith('http'):
                    enlace = 'https://www.marca.com' + enlace

                # Realiza una solicitud al enlace del artículo para obtener la descripción
                article_response = requests.get(enlace)
                article_response.raise_for_status()
                article_soup = BeautifulSoup(article_response.text, 'html.parser')

                # Extrae la descripción del artículo
                content_div = article_soup.find('div', class_='ue-c-article__body')
                descripcion = ''
                if content_div:
                    paragraphs = content_div.find_all('p')
                    descripcion = ' '.join(paragraph.get_text(strip=True) for paragraph in paragraphs)

                # Extrae la imagen
                media = article.find('div', class_='ue-c-cover-content__media')
                imagen = None
                if media:
                    img_tag = media.find('img', class_='ue-c-cover-content__image')
                    if img_tag and 'src' in img_tag.attrs:
                        imagen = img_tag['src']

                # Almacena la información en la lista de noticias
                noticia = {
                    'fecha': datetime.now().strftime('%B %d, %Y'),
                    'titulo': titulo,
                    'fuente': 'Marca',
                    'descripcion': descripcion,
                    'image': imagen
                }
                noticias.append(noticia)

                # Sube la noticia a Firebase si no existe
                upload_to_firebase('deportes', noticia)

    return noticias

#  Ejemplo de uso

def scrape_all():
    scrape_tvsur()
    scraping_sinfronteras()
    scraping_andes()
    scraping_sinfronterasdeportes()
    scraping_andes_deportes()
    scraping_andes_politica()
    scraping_sinfronteras_politica()
    scraping_marca_futbol_internacional()
    schedule.every(0.0001).minutes.do(scrape_all)

while True:
    scrape_all() 
    schedule.run_pending()
    time.sleep(1)
