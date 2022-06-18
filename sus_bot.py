
import telegram
import requests 
import json
import random
import torch
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize
from googlesearch import search

TOKEN = 'seu token'
bot = telegram.Bot(TOKEN)


class TelegramBot:
    def __init__(self):
        token = TOKEN
        self.url_base = f"https://api.telegram.org/bot{token}/"
        
    # Iniciar o bot
    def Iniciar(self):
        update_id = None

        while True:
            atualizacao = self.obter_mensagens(update_id)
            mensagens = atualizacao["result"]
            if mensagens:
                for mensagem in mensagens:
                    update_id = mensagem["update_id"]
                    chat_id = mensagem["message"]["from"]["id"]
                    primeira_mensagem = mensagem["message"]["message_id"] == 1
                    resposta = self.criar_resposta(mensagem, primeira_mensagem)
                    if resposta == 'busca':
                        try:
                            termo = mensagem['message']['text'].split('-')[1]
                            buscas = 'faz a busca na api do ms'
                            resposta = buscas
                        except:
                            resposta = "Erro na solicitação"
                    self.responder(resposta,chat_id)       
    # Obter mensagens
    def obter_mensagens(self,update_id):
        link_requisicao = f'{self.url_base}getUpdates?timeout=100'
        if update_id:    
            link_requisicao = f"{link_requisicao}&offset={update_id + 1}"
        resultado = requests.get(link_requisicao)
        return json.loads(resultado.content)
    # Criar uma resposta
    def criar_resposta(self,mensagem, primeira_mensagem):
        if "text" in list(mensagem["message"].keys()):
            msg = mensagem["message"]["text"]
            resposta = self.intents(msg)
            return resposta

    def responder(self,resposta,chat_id):
        chat_id = bot.get_updates()[-1].message.chat_id
        bot.sendMessage(chat_id, resposta)

     
    def intents(self, msg):
           
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        with open('intents.json', 'r') as json_data:
            intents = json.load(json_data)
        
        FILE = "data.pth"
        data = torch.load(FILE)
        
        input_size = data["input_size"]
        hidden_size = data["hidden_size"]
        output_size = data["output_size"]
        all_words = data['all_words']
        tags = data['tags']
        model_state = data["model_state"]
        
        model = NeuralNet(input_size, hidden_size, output_size).to(device)
        model.load_state_dict(model_state)
        model.eval()
        sentence = msg
        sentence = tokenize(sentence)
        X = bag_of_words(sentence, all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(device)
    
        output = model(X)
        _, predicted = torch.max(output, dim=1)
    
        tag = tags[predicted.item()]
    
        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]
        if prob.item() > 0.5:
            for intent in intents['intents']:
                if tag == intent["tag"]:
                    intencao = (f"{random.choice(intent['responses'])}")
                    return intencao
        else:
            intencao = ("Não entendi...")
            return intencao
        

bot2 = TelegramBot() 
bot2.Iniciar()

