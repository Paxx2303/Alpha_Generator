import requests, json, base64

with open('wqb_config.json') as f:
    config = json.load(f)

creds = base64.b64encode(f"{config['email']}:{config['password']}".encode()).decode()
headers = {'Authorization': f'Basic {creds}', 'Content-Type': 'application/json'}

res = requests.post('https://api.worldquantbrain.com/authentication', headers=headers)
if res.status_code == 201:
    res = requests.get('https://api.worldquantbrain.com/data-fields?instrumentType=EQUITY&region=USA&delay=1&limit=5&search=sentiment', headers=headers)
    print(res.status_code)
    print(json.dumps(res.json(), indent=2)[:500])
