from tbselenium.tbdriver import TorBrowserDriver
from bs4 import BeautifulSoup
from pymongo import MongoClient
import seaborn as sns
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import os
import matplotlib.pyplot as plt

# URL cible
url = 'http://kill432ltnkqvaqntbalnsgojqqs2wz4lhnamrqjg66tq6fuvcztilyd.onion/'

# Chemin vers le répertoire Tor Browser
TOR_BROWSER_PATH = '/home/amine/Downloads/tor-browser-linux-x86_64-13.5.2/tor-browser'

# Configuration de la base de données MongoDB
MONGO_URI = 'mongodb://localhost:27017/'
DATABASE_NAME = 'PW'
COLLECTION_NAME = 'NEW'

def insert_data(data_list):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Récupérer les titres des documents existants
    existing_data = {item['title']: item for item in collection.find({}, {'title': 1})}
    
    new_data = []
    for data in data_list:
        title = data.get('title')
        if title not in existing_data:
            # Si le titre n'existe pas, ajouter les nouvelles données
            new_data.append(data)
        else:
            # Comparer les données existantes avec les nouvelles données
            existing_item = existing_data[title]
            update_fields = {}
            
            if existing_item.get('status') != data.get('status'):
                update_fields['status'] = data.get('status')
            if existing_item.get('description') != data.get('description'):
                update_fields['description'] = data.get('description')
            
            if update_fields:
                # Mettre à jour seulement les champs modifiés
                collection.update_one({'title': title}, {'$set': update_fields})
    
    # Insérer les nouvelles données
    if new_data:
        collection.insert_many(new_data)
    
    client.close()

def generate_charts():

    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Récupérer les données depuis MongoDB
    data = list(collection.find())
    
    titles = []
    statuses = []
    descriptions = []
    
    for item in data:
        titles.append(item.get('title', 'N/A'))
        
        # Obtenir le statut en fonction des classes
        status = item.get('status', 'NOT PUBLISHED')
        if status == 'PUBLISHED':
            status = 'PUBLISHED'
        else:
            status = 'NOT PUBLISHED'
        statuses.append(status)
        
        descriptions.append(item.get('description', 'No description'))
    
    # Créer des tuples (title, description) pour trier les forums par statut
    sorted_by_status = sorted(zip(titles, statuses, descriptions), key=lambda x: x[1])
    
    # Séparer les données en deux groupes
    published = [item for item in sorted_by_status if item[1] == 'PUBLISHED']
    not_published = [item for item in sorted_by_status if item[1] == 'NOT PUBLISHED']
    
    # Extraire les données pour les graphiques
    published_titles, published_statuses, published_descriptions = zip(*published) if published else ([], [], [])
    not_published_titles, not_published_statuses, not_published_descriptions = zip(*not_published) if not_published else ([], [], [])
    
    # Style Seaborn pour des graphiques plus élégants
    sns.set(style="whitegrid")
    with PdfPages('/home/amine/pwn6/charts.pdf') as pdf_pages:

     
        
        # Créer la troisième figure pour le pie chart des statuts
        status_counts = {status: statuses.count(status) for status in set(statuses)}
        
        fig3, ax3 = plt.subplots(figsize=(10, 10))
        wedges, texts, autotexts = ax3.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%', colors=sns.color_palette("Set2", len(status_counts)))
        ax3.set_title('Forum Status Distribution', fontsize=14)
        
        # Personnaliser l'apparence des textes
        for text in texts:
            text.set_fontsize(12)
        for autotext in autotexts:
            autotext.set_fontsize(12)
        pdf_pages.savefig(fig3)  # Sauvegarder la figure dans le PDF
        # Ajuster les marges pour éviter le découpage du texte
        plt.tight_layout()

def main():
    with TorBrowserDriver(TOR_BROWSER_PATH) as driver:
        driver.get(url)
        page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')
        
        elements = soup.find_all('a', class_='post-block unleaked') + soup.find_all('a', class_='post-block leaked')

        data_list = []

        for element in elements:
            # Extraire le titre
            title_div = element.find('div', class_='post-title')
            title = title_div.get_text(strip=True) if title_div else 'N/A'

            # Déterminer le statut en fonction de la classe
            class_name = element.get('class', [])
            if 'leaked' in class_name:
                status = 'PUBLISHED'
            else:
                status = 'NOT PUBLISHED'

            # Extraire la description
            description_p = element.find('div', class_='post-block-body').find('p', class_='post-block-text')
            description = description_p.get_text(strip=True) if description_p else 'No description'

            # Préparer les données pour MongoDB
            data = {
                'title': title,
                'status': status,
                'description': description
            }

            data_list.append(data)

        # Insérer les données dans MongoDB
        insert_data(data_list)
        print("Données insérées dans MongoDB.")
    
    # Définir le répertoire de travail pour les graphiques
    os.chdir('/home/amine/pwn6/braincipher')
    generate_charts()

if __name__ == "__main__":
    main()
