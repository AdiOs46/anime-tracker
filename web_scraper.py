import requests
from bs4 import BeautifulSoup
import json
from dask.distributed import Client, progress
import dask.bag as db
from multiprocessing import Pool

def get_top_anime_urls(num_pages = 2):
    try:
        base_url = "https://myanimelist.net/topanime.php"
        top_anime_urls = []
        
        for page_number in range(1, num_pages + 1):
            n=(page_number-1)*50
            url = f"{base_url}?limit={n}"

            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error: Unable to fetch data from {url}. Status code: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            anime_td_list = soup.find_all('div',class_="di-ib clearfix")
            top_anime_urls.extend([tag.a['href'] for tag in anime_td_list])
            
        return top_anime_urls
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def scrape_anime(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        # response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            anime_image = soup.find('img', itemprop='image')['data-src']
            if anime_image:
                image = anime_image
            else:
                image="image not found"
            
            title_element = soup.find('h1', class_='title-name')
            if title_element:
                title = title_element.text.strip() 
            else:
                title = "Title not found"
            
            genres_elements = soup.find_all('span', itemprop='genre')
            genres = [genre.text.strip() for genre in genres_elements]
            
            synopsis_element = soup.find('p', itemprop='description')
            if synopsis_element:
                 synopsis = synopsis_element.text.strip()
            else:
                synopsis = "Synopsis not found"
            
            rating_element = soup.find('span', itemprop='ratingValue')
            if rating_element:
                rating = rating_element.text.strip()     
            else:
                rating = "Rating not found"
            
            trailer_element = soup.find('a', class_='iframe js-fancybox-video video-unit promotion')
            if trailer_element:
                trailer = trailer_element.get('href')
            else:
                trailer = "Trailer not found"
            
            anime_data = {
                'title': title,
                'image': image,
                'genres': genres,
                'synopsis': synopsis,
                'rating': rating,
                'trailer': trailer
            }
            
            return anime_data
        else:
            print(f"Error: Unable to fetch data from {url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def scrape_top_anime():
    top_anime_urls = get_top_anime_urls()
    if top_anime_urls:
        with Client() as client: #connect to dask cluster
            # Distribute scraping tasks across the Dask cluster
            b = db.from_sequence(top_anime_urls) #dask bag
            results = b.map(scrape_anime).compute()
        return results
    else:
        return None

if __name__ == "__main__":
    scraped_data = scrape_top_anime()
    
    if scraped_data:
        # Write the scraped data to a JSON file
        with open('top_anime_data.json', 'w') as f:
            json.dump(scraped_data, f, indent=2)
        
        print("Scraped data saved to top_anime_data.json")
    else:
        print("Error: Unable to scrape top anime data")
