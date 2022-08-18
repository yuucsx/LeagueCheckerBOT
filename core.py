from multiprocessing.sharedctypes import Value
import os
import cloudscraper
from datetime import *
import base64
from dateutil import parser
import json
import ssl
import re

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_REQUIRED
context.check_hostname = True
context.load_default_certs()
  
class Checker():
  def __init__(self, user, password):
    self.user = user
    self.password = password
    self.session = cloudscraper.create_scraper()
    self.idsLoja = {
        "BR1": "br",
        "EUN1": "eun",
        "EUW1": "euw",
        "JP1": "jp",
        "LA1": "la1",
        "LA2": "la2",
        "NA1": "na",
        "OC1": "oc",
        "RU": "ru",
        "TR1": "tr",
    }
    self.tiposInventario = ['CHAMPION', 'CHAMPION_SKIN']
    self.storeEndpoints = {
        "BR1": "lolriot.mia1.br1",
        "EUN1": "lolriot.euc1.eun1",
        "EUW1": "lolriot.ams1.euw1",
        "JP1": "lolriot.nrt1.jp1",
        "LA1": "lolriot.mia1.la1",
        "LA2": "lolriot.mia1.la2",
        "NA1": "lolriot.pdx2.na1",
        "OC1": "lolriot.pdx1.oc1",
        "RU": "lolriot.euc1.ru",
        "TR1": "lolriot.euc1.tr1",
    }
    self.bearer = self.getBearer()

  def getBearer(self):
  
    headers = {
      "user-agent": "RiotClient/44.0.1.4223069.4190634 rso-auth (Windows;10;;Professional, x64)",
      "Accept": "application/json"}

    scopes = {
        "client_id": "riot-client",
        "nonce": "1",
        "redirect_uri": "http://localhost/redirect",
        "response_type": "token id_token",
        'scope': "openid link ban lol_region"}
    
    self.session.post('https://auth.riotgames.com/api/v1/authorization', headers=headers, json=scopes)
    auth_payload = {
		        "type": "auth",
            "username": self.user,
            "password": self.password,
            "remember": "true"}
    
    r = self.session.put('https://auth.riotgames.com/api/v1/authorization', headers=headers, json=auth_payload).json()
    try:
      access_token = r['response']['parameters']['uri']
      bearer = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)').findall(access_token)[0][0]
      return bearer
    except Exception as e:
      return 'off'


    
  def getInfo(self):
    if self.bearer == 'off':
      return 'off'
    i = self.session.post("https://auth.riotgames.com/userinfo",
              headers = {
              "Accept-Encoding": "deflate, gzip",
              "user-agent": "RiotClient/44.0.1.4223069.4190634 lol-inventory (Windows;10;;Professional, x64)",
              "Accept": "application/json",
              "Authorization": f"Bearer {self.bearer}",
          }).json()



    ban = 'No'
    try:
      if i['ban']['exp'] == None:
          ban = "No"
      elif int(i['ban']['exp']) > int(time.time())*1000:
          ban = "No"
      else:
          ban = "No"
    except:
      pass
    infos = {
      "ban": ban,
      "nick":i["lol_account"]["summoner_name"],
      "id": i["acct"]["tag_line"],
      "level":i["lol_account"]["summoner_level"],
      "telefone": "Yes" if i["phone_number_verified"] else "No",
      "email":"Yes" if i['email_verified'] else "No",
      "region": i["region"]["id"],
      "creation": datetime.fromtimestamp(i['acct']['created_at']/1000).strftime('%d-%m-%Y %H:%M:%S'),
      "puuid": i['sub'],
      "pvp-net-account-id":i['pvpnet_account_id']
      
      }
    return infos

  def getChampionNameById(self):
      self.clientVersion = self.session.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
      r = self.session.get(f'https://ddragon.leagueoflegends.com/cdn/{self.clientVersion}/data/en_US/champion.json').json()['data']
      self.championIdList = {}
      for championName in r:
          self.championIdList[championName] = r[championName]['key']
      self.championIdList = {y: x for x, y in self.championIdList.items()}
      return self.championIdList
    
  def getStore(self):
    try:
      region = self.idsLoja[self.getInfo()['region']]
      store = self.session.get(f"https://{region}.store.leagueoflegends.com/storefront/v3/view/misc?language=en_US",
                      headers = {
                "Accept-Encoding": "deflate, gzip",
                "user-agent": "RiotClient/44.0.1.4223069.4190634                 lol-inventory (Windows;10;;Professional, x64)",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.bearer}"
                      }).json()
      history = self.session.get(f"https://{region}.store.leagueoflegends.com/storefront/v3/history/purchase",
                      headers = {
                "Accept-Encoding": "deflate, gzip",
                "user-agent": "RiotClient/44.0.1.4223069.4190634                 lol-inventory (Windows;10;;Professional, x64)",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.bearer}"
                      }).json()
      
      store = {
        "BE": store["player"]["ip"],
        "RP": store["player"]["rp"],
        'refunds': history["refundCreditsRemaining"]
      }
      return store
    except Exception as e:
      print(e)
      return None

  def getAltInventory(self):
      i = self.getInfo()
      query = {
         "puuid": i['puuid'],
         "location": self.storeEndpoints[i['region']],
         "accountId": i['pvp-net-account-id'],
      }

      types = ['CHAMPION', 'CHAMPION_SKIN']
      query_string = "&".join(
            [f"{k}={v}" for k, v in query.items()]
            + [f"inventoryTypes={t}" for t in types]
        )
      header = {
            "Accept-Encoding": "deflate, gzip",
            "user-agent": "RiotClient/44.0.1.4223069.4190634 lol-inventory (Windows;10;;Professional, x64)",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.bearer}",
        }

      url = "https://{region}.cap.riotgames.com/lolinventoryservice/v2/inventories/simple?".format(region=i['region']) + query_string
      r = self.session.get(url, headers=header).json()
      #print(r['data']['items']['CHAMPION_SKIN'])
      i = {
        'champions': len(r['data']['items']['CHAMPION']),
        'skins': len(r['data']['items']['CHAMPION_SKIN'])
      }
      return i

  def getInventory(self, i='CHAMPION'):
      header = {
          "Accept-Encoding": "deflate, gzip",
          "user-agent": "RiotClient/44.0.1.4223069.4190634 lol-inventory (Windows;10;;Professional, x64)",
          "Accept": "application/json",
          "Authorization": f"Bearer {self.bearer}",
      }
      url = 'https://{0}.cap.riotgames.com/lolinventoryservice/v2/inventoriesWithLoyalty?puuid={1}&inventoryTypes={2}&location={3}&accountId={4}&signed=true'
      infos = self.getInfo()
      url = url.format(infos['region'], infos['puuid'], i, self.storeEndpoints[infos['region']], infos['pvp-net-account-id'])
      r = self.session.get(url, headers=header).json()
      itensJwt = r["data"]["itemsJwt"].split('.')[1]
      data = itensJwt + f"{'=' * (-len(itensJwt) % 4)}"
      inventory = json.loads(base64.b64decode(data))
      return inventory

  def getChampions(self):
        championsId = self.getChampionNameById()
        userInventory = {}
        inventory = self.getInventory()['items']
        for champion in inventory['CHAMPION']:
            userInventory[champion['itemId']] = champion['purchaseDate']
        
        filteredInventory = {}
        
        for k in userInventory:
            filteredInventory[championsId[str(k)]] = userInventory[k]
        
        for k, v in filteredInventory.items():
            filteredInventory[k] = parser.parse(v)

        for k,v in filteredInventory.items():
            filteredInventory[k] = v.strftime("%d/%m/%Y")
        filteredInventory = sorted(filteredInventory.items(), key = lambda x:datetime.strptime(x[1], '%d/%m/%Y'))

        list = ''
        for i in filteredInventory:
            list += f'{i[0]}: *{i[1]}*\n'

        return list

  def getSkins(self):
      skins = self.session.get('https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/skins.json').json()
      skinsInInventory = self.getInventory('CHAMPION_SKIN')['items']['CHAMPION_SKIN']
      skinInventory = {}
      for i in skinsInInventory:
          skinInventory[i['itemId']] = i['purchaseDate']
      
      filteredSkinInventory = {}
      
      for k in skinInventory:
          try:
              filteredSkinInventory[skins[str(k)]['name']] = skinInventory[k]
          except:
              filteredSkinInventory[k] = skinInventory[k]
      for k, v in filteredSkinInventory.items():
          filteredSkinInventory[k] = parser.parse(v)
      for k,v in filteredSkinInventory.items():
          filteredSkinInventory[k] = v.strftime("%d/%m/%Y")
      
      filteredSkinInventory = sorted(filteredSkinInventory.items(), key = lambda x:datetime.strptime(x[1], '%d/%m/%Y'))
      list = ''
      for i in filteredSkinInventory:
          list += f'{i[0]}: *{i[1]}*\n'
      return list

  def filterFiveItems(self):
    skins = self.getSkins()
    champions = self.getChampions()
    firstFiveSkins = skins.splitlines()[:5]
    firstFiveChampions = champions.splitlines()[:5]
    i = {
      'firstSkins': firstFiveSkins,
      'firstChampions': firstFiveChampions,
    }
    return i

  def getRank(self):
    infos = self.getInfo()
    url = "https://riot.iesdev.com/graphql?query=query%20LeagueProfile%28%24summoner_name%3AString%2C%24summoner_id%3AString%2C%24account_id%3AString%2C%24region%3ARegion%21%2C%24puuid%3AString%29%7BleagueProfile%28summoner_name%3A%24summoner_name%2Csummoner_id%3A%24summoner_id%2Caccount_id%3A%24account_id%2Cregion%3A%24region%2Cpuuid%3A%24puuid%29%7BaccountId%20latestRanks%7Bqueue%20tier%20rank%20leaguePoints%7D%7D%7D&variables=%7B%22summoner_name%22%3A%22{summoner_name}%22%2C%22region%22%3A%22{region_id}%22%7D"
    rank = self.session.get(url.format(summoner_name=infos['nick'], region_id=infos['region'])).json()['data']['leagueProfile']['latestRanks']
    i = {
      'elo': {
        'SoloDuo': 'Unranked',
        'Flex': 'Unranked'
      }
    }
    if rank:
      for queue in rank:
        if queue["queue"] == "RANKED_SOLO_5X5":
          i['elo']['SoloDuo'] = f'{queue["tier"]} {queue["rank"]} {queue["leaguePoints"]}LP'
        if queue['queue'] == 'RANKED_FLEX_SR':
          i['elo']['Flex'] = f'{queue["tier"]} {queue["rank"]} {queue["leaguePoints"]}LP'
    else:
      return i
    return i
      
    

  def returnInfos(self):
    infos = {}
    try:
      infos.update(self.getStore())
      infos.update(self.getInfo())
      infos.update(self.getRank())
      return infos
    except Exception as e:
      print(e)
      return None



