import requests
from app.config import settings as s
from ..db.redis import get_currency_by_country_code
from ..config import settings as s
async def get_user_currency(ip:str)  :
    if ip == "localhost:8000" :
        ip = s.fake_ip
    url = f"http://{s.geoip_api_host}:{s.geoip_api_port}/{ip}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers )
    if response.status_code == 200:
        print(response.json().get("country"))
        #country_code = response.json().get("country")
        currency = await get_currency_by_country_code( response.json().get("country"))
        return currency
    else:
        return response.raise_for_status()

# TODO  recupérer le country code
# TODO  recupérer le exchange stocké  dans redis 
# TODO  recupérer recupéré  la monaie de l' utilsation basé sur son country code 
# TODO  vérifier si la monaie est supporter  si oui rretourner la monaie sinon retourner le dollar


