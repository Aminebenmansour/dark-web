from tbselenium.tbdriver import TorBrowserDriver
from bs4 import BeautifulSoup
from pymongo import MongoClient
import time 
import seaborn as sns
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import os
import matplotlib.pyplot as plt

# Chemin vers le répertoire Tor Browser
TOR_BROWSER_PATH = '/home/amine/Downloads/tor-browser-linux-x86_64-13.5.2/tor-browser'

# URL cible
url = 'http://ransomxifxwc5eteopdobynonjctkxxvap77yqifu2emfbecgbqdw6qd.onion/'

# Configuration de la base de données MongoDB
MONGO_URI = 'mongodb://localhost:27017/'
DATABASE_NAME = 'PWN'
COLLECTION_NAME = 'Forums'

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
            if existing_item.get('visits') != data.get('visits'):
                update_fields['visits'] = data.get('visits')
            if existing_item.get('pub') != data.get('pub'):
                update_fields['pub'] = data.get('pub')
            
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
    visits = []
    pub_dates = []
    statuses = []
    
    for item in data:
        titles.append(item.get('title', 'N/A'))
        visit_str = item.get('visits', '0')
        try:
            visits.append(int(visit_str))
        except ValueError:
            visits.append(0)
        
        pub_str = item.get('pub', '1970-01-01 00:00:00')
        try:
            pub_dates.append(datetime.strptime(pub_str, '%Y-%m-%d %H:%M:%S'))
        except ValueError:
            pub_dates.append(datetime(1970, 1, 1))
        
        statuses.append(item.get('status', 'NOT PUBLISHED'))
    
    # Créer des tuples (visits, title) et (pub_date, title) pour trier les forums
    sorted_by_visits = sorted(zip(visits, titles), reverse=True)
    sorted_by_pub = sorted(zip(pub_dates, titles), reverse=True)
    
    # Séparer les données en deux groupes
    top_10_visits = sorted_by_visits[:10]
    last_5_pub = sorted_by_pub[:5]
    
    # Extraire les données pour les graphiques
    top_visits, top_titles_visits = zip(*top_10_visits)
   
    last_dates, last_titles_pub = zip(*last_5_pub)
    print(last_dates)
    print(last_titles_pub)
    
    # Formatage des dates pour l'affichage
    last_dates_str = [date.strftime('%Y-%m-%d') for date in last_dates]
    print(last_dates_str)
    
    # Style Seaborn pour des graphiques plus élégants
    sns.set(style="whitegrid")
    with PdfPages('charts.pdf') as pdf_pages:

        # Créer la première figure pour les 10 forums les plus visités
        fig1, ax1 = plt.subplots(figsize=(14, 8))
        bars_top_visits = ax1.bar(top_titles_visits, top_visits, color=sns.color_palette("Blues", 8))
        ax1.set_xlabel('Visits', fontsize=12)
        ax1.set_ylabel('Number of Visits', fontsize=12)
        ax1.set_title('Top 10 Forums with Most Visits', fontsize=14)
        ax1.set_xticks(top_titles_visits)
        ax1.set_xticklabels(top_titles_visits, rotation=10, ha='right', fontsize=10)
        pdf_pages.savefig(fig1)  # Sauvegarder la figure dans le PDF
        
        # Créer la deuxième figure avec des barres verticales pour les 5 forums les plus récemment publiés
        fig2, ax2 = plt.subplots(figsize=(14, 8))
        bars_last_pub = ax2.barh(last_titles_pub, range(len(last_dates)), color=sns.color_palette("Greens", 5))
        ax2.set_xlabel('Publication Date', fontsize=12)
        ax2.set_ylabel('Victim Title', fontsize=12)
        ax2.set_title('5 Most Recently Published Victims', fontsize=14)
        ax2.set_xticks(range(len(last_dates)))
        ax2.set_xticklabels(last_dates_str, rotation=45, ha='right', fontsize=10)
        pdf_pages.savefig(fig2)  # Sauvegarder la figure dans le PDF
        
        # Créer la troisième figure pour le pie chart des statuts
        status_counts = {status: statuses.count(status) for status in set(statuses)}
        
        fig3, ax3 = plt.subplots(figsize=(10, 10))
        wedges, texts, autotexts = ax3.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%', colors=sns.color_palette("Set2", 2))
        ax3.set_title('Forum Status Distribution', fontsize=14)
        
        # Personnaliser l'apparence des textes
        for text in texts:
            text.set_fontsize(12)
        for autotext in autotexts:
            autotext.set_fontsize(12)
        pdf_pages.savefig(fig3)  # Sauvegarder la figure dans le PDF
        # Ajuster les marges pour éviter le découpage du texte
        plt.tight_layout()
        
        # Afficher les graphiques dans des fenêtres séparées
       
def main():
    with TorBrowserDriver(TOR_BROWSER_PATH) as driver:
        driver.get(url)
        page_source = driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')

        elements = soup.find_all('div', class_='col-12 col-md-6 col-lg-4')

        data_list = []

        for element in elements:
            # Extraire le titre
            title_div = element.find('div', class_='card-title text-center')
            title = title_div.get_text(strip=True) if title_div else 'N/A'

            # Extraire le statut
            status_p = element.find('p', class_='text-center')
            if status_p and status_p.find('strong'):
                status_text = status_p.find('strong').get_text(strip=True)
                status = 'PUBLISHED' if 'PUBLISHED' in status_text else 'NOT PUBLISHED'
            else:
                status = 'NOT PUBLISHED'

            # Extraire les détails
            details_p = element.find_all('p')
            if len(details_p) >= 2:
                visits = details_p[1].get_text(strip=True).split(': ')[1][:-9] if 'Visits' in details_p[1].get_text() else 'N/A'
                data_size = details_p[1].get_text(strip=True).split(': ')[2][:-8] if 'Data Size' in details_p[1].get_text() else 'N/A'
                last_view = details_p[1].get_text(strip=True).split(': ')[3] if 'Last View' in details_p[1].get_text() else 'N/A'
            else:
                visits = data_size = last_view = 'N/A'

            # Extraire le contenu de card-footer
            footer_div = element.find('div', class_='card-footer')
            pub = footer_div.get_text(strip=True) if footer_div else 'N/A'
            index_anchor = element.find('a', class_='index-anchor')
            if index_anchor and 'href' in index_anchor.attrs:
                href = index_anchor['href']
                full_url = f"http://ransomxifxwc5eteopdobynonjctkxxvap77yqifu2emfbecgbqdw6qd.onion/{href.lstrip('/')}"
                
            # Préparer les données pour MongoDB
            data = {
                'title': title,
                'status': status,
                'visits': visits,
                'data_size': data_size,
                'last_view': last_view,
                'pub': pub,
                'full_url': full_url
            }

            data_list.append(data)

        # Insérer les données dans MongoDB
        insert_data(data_list)
        print("Données insérées dans MongoDB.")
    os.chdir('/home/amine/pwn6')
    generate_charts()

if __name__ == "__main__":
    main()
