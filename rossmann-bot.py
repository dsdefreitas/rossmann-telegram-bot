import os
import requests
import pandas as pd
import json

from flask import Flask, request, Response

#constants
TOKEN = '6186634028:AAG7LygxmgPKMNUgfXFnbsc7hwdNTz8eu2s'

#info about the bot
"https://api.telegram.org/bot6186634028:AAG7LygxmgPKMNUgfXFnbsc7hwdNTz8eu2s/getMe"

#getme fornece informações sobre o bot.
# o browser faz uma requisição na api. Então quando você copia o link acima e cola no browser,
# é como se você tivesse fazendo uma requisição na api.
#ele manda o código pra api do telegram, que retorna um json como resposta.

#get updates

"https://api.telegram.org/bot6186634028:AAG7LygxmgPKMNUgfXFnbsc7hwdNTz8eu2s/getUpdates"

#Webhook
"https://api.telegram.org/bot6186634028:AAG7LygxmgPKMNUgfXFnbsc7hwdNTz8eu2s/setWebhook?url=https://rossmann-telegram-bot-8o6m.onrender.com"

#send message

"https://api.telegram.org/bot6186634028:AAG7LygxmgPKMNUgfXFnbsc7hwdNTz8eu2s/sendMessage?chat_id=1017959276&text=Hi Meigarom, I am doing good, tks!"

#ponto de interrogação depois do método: o browser entende que a partir de agora você vai passar parâmetros.
#pra concatenar os métodos que vocÊ passa, você usa o "&".

def send_message(chat_id, text):
    "Model: https://api.telegram.org/bot6186634028:AAG7LygxmgPKMNUgfXFnbsc7hwdNTz8eu2s/sendMessage?chat_id=1017959276&text=Hi Meigarom, I am doing good, tks!"
    url = "https://api.telegram.org/bot{}/".format(TOKEN)
    url = url + "sendMessage?chat_id={}".format(chat_id)

    r = requests.post(url, json = {'text': text})
    print('Status Code {}'.format(r.status_code))

    return None

def load_dataset(store_id):
    df10 = pd.read_csv("test.csv")
    df_store_raw = pd.read_csv("store.csv")

    #merge test dataset + store

    df_test = pd.merge(df10, df_store_raw, how = 'left', on = 'Store')

    # choose store for prediction
    df_test = df_test[df_test['Store'] == store_id]

    if not df_test.empty:
        #remove closed days (removendo linhas que não importam)
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop('Id', axis = 1 )

        #convert Dataframe to json
        data = json.dumps(df_test.to_dict(orient='records'))

    else:
        data = 'error'

    return data

    #API Call
def predict(data):
    url = 'https://rossmann-sales-prediction-a2rd.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, data=data, headers = header )
    print('Status Code {}'.format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns = r.json()[0].keys())

    return d1

def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']


    store_id = store_id.replace('/', '')
    #comandos do telegram possuem barra na frente
    #código para tirar essa barra.

    #condição para caso for enviado um texto e não um código de loja:

    try:
        store_id = int(store_id)

    except ValueError:
        store_id = 'error'

    return chat_id, store_id

#cria-se um endpoint com o flask, que fica esperando a msg,
# para o telegram mandar mensagem para este endpoint e aí trabalhar essa mensagem.

app = Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
#vai colocar um endpoint na raiz mesmo, e vou permitir dois métodos, método GET e método POST. 
#função index vai rodar sempre que o endpoint root for acionado passando um dado.
def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, store_id = parse_message(message)

        if store_id != 'error':
            #loading data
            data = load_dataset(store_id)

            if data != 'error':
                #prediction
                d1 = predict(data)
                
                #calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()

                #send message
                msg = 'Store Number {} will sell R${:,.2f} in the next 6 weeks'.format(
                d2['store'].values[0], d2['prediction'].values[0])
                #eu quero só a primeira parte dessas series.
                
                send_message(chat_id, msg)
                return Response('Ok', status=200)

            else:
                send_message(chat_id, 'Store not available')
                return Response('Ok', status = 200)
        #essa é uma mensagem pro api falando que você conseguiu enviar mensagem.
        #se esquecer de passar status 200, a api fica rodando infinitamente pq
        #acha que não acabou.

        else:
            send_message(chat_id, 'Store Id is Wrong')
            return Response('Ok', status = 200 )

    else:
        return '<h1> Rossmann Telegram BOT </h1>'

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)
