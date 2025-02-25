import csv
import secrets
from client import Client
from utils import *
from dictionaries import RESPONSES
from unidecode import unidecode

class ClientMessage:
    def __init__(self, logger, data):
        self.logger = logger
        self.data = data
        self.type = self.data['messages'][-1]['type']
        self.attendant_number_id = data['metadata']['phone_number_id']
        self.msg_id = data['messages'][-1]['id']
        self.client = Client(logger, data['contacts'][-1]['wa_id'])
        self.history = self.get_post_messages()
        self.responded = False

        if self.type == 'text':
            self.save_msg('client', self.data["messages"][-1]["text"]["body"])
            self.logger.debug(f'treating message {self.data["messages"][-1]["text"]["body"]}')
        else:
            self.save_msg('client', self.type)
            self.logger.debug(f'treating message {self.data["messages"][-1]["type"]}')
        
        if self.history:
            if dt.datetime.now() - self.history[-1]['date'] < dt.timedelta(minutes=20): return

        self.alert_message()
        
    def alert_message(self):
        attendant_history = get_message_history(self.logger, os.environ['ATTENDANT_NUMBER'])
        if attendant_history:
            if dt.datetime.now() - attendant_history[-1]['date'] > dt.timedelta(hours=20):
                # Add alert message to queue
                open('alert_queue.txt', 'a').write(f'{self.client.id}\n')
                return

        token = secrets.token_urlsafe(128)
        manage_tokens(token, self.client.phone)
        client_interact_alert = {
            'type': 'text',
            'body': {
                'body': f'{self.client.name} mandou mensagem para o bot\nContato: +{self.client.phone}\nAgendor: https://web.agendor.com.br/sistema/pessoas/historico.php?id={self.client.id}\nVer mensagens: {os.environ["WEBHOOK_URL"]}/messages?id={self.client.phone}&token={token}'
            }
        }
        
        send_msg(self.logger, client_interact_alert, os.environ['ATTENDANT_NUMBER'])


    def handle_msg(self):
        self.mark_as_read()
        
        if not self.history:
            self.logger.debug('Sem historico')
            return
        
        if self.type != 'text':
            self.logger.info(f'Message with type {self.type} instead of text')
        
        last_bot_msg_type, last_bot_msg_content = '', ''
        for i in range(-1, -(len(self.history) + 1), -1):
            if self.history[i]['by'] == 'bot':
                last_bot_msg_type, last_bot_msg_content = self.history[i]['content'].split()
                break
            
        if not all([last_bot_msg_type, last_bot_msg_content]):
            return
        
        self.logger.debug(f'last_bot_msg: {last_bot_msg_type}, {last_bot_msg_content}')
        
        if last_bot_msg_content == 'site_follow_up':
            self.treat_site_follow_up_msg(self.data["messages"][-1]["text"]["body"])
        elif last_bot_msg_content == 'site_follow_up_no':
            self.responded = True
        elif last_bot_msg_type in ['info', 'instruction']:
            handle_info = {
                'role': self.treat_role_msg,
                'name': self.treat_name_msg,
                'athlete_name': self.treat_athlete_name_msg,
                'athlete_birth': self.treat_athlete_birth_msg,
                'sport': self.treat_sport_msg,
                'email': self.treat_email_msg,
                'date_to_go': self.treat_date_to_go_msg
            }
            if self.type == 'text':
                msg = self.data["messages"][-1]["text"]["body"]
                handle_info[last_bot_msg_content](msg.replace('\n', ' '))
                self.client.n_missing_info -= 1
            else:
                self.respond('instruction', last_bot_msg_content)
        else:
            self.logger.debug('No info update')
        
        
    def respond(self, type=None, content=None):
        resps = []
        if type and content:
            resps += self.responses(type, content)
        elif self.data['messages'][-1]['type'] in ['text', 'interactive']:
            if not self.client.name:
                resps += self.responses('base', 'initial')
                resps += self.responses('info', 'name')
            elif not self.client.role:
                if dt.datetime.now() - self.history[-1]['date'] > dt.timedelta(days=1):
                    resps += self.responses('base', 'initial')
                resps += self.responses('info', 'role')
            elif len(self.history) == 0 and self.client.n_missing_info == 0:
                resps += self.responses('base', 'registered')
            elif self.client.n_missing_info == 0:
                self.logger.info('Finished conversation')
                if 'base final' not in map(lambda x: x['content'], self.history):
                    resps += self.responses('base', 'final')
            else:
                if dt.datetime.now() - self.history[-1]['date'] < dt.timedelta(days=1):
                    today_msgs = []
                    i = 0
                    while abs(i) < len(self.history):
                        i -= 1
                        
                        if (dt.datetime.now() - self.history[i]['date']) > dt.timedelta(days=1):
                            break
                        if self.history[i]['by'] == 'bot':
                            today_msgs.append(self.history[i]['content'])
                            
                    if 'base questions' not in today_msgs:
                        resps += self.responses('base', 'questions')
                else:
                    resps += self.responses('base', 'questions')
                    
                info_to_ask = ''
                for info, value in list(self.client.__dict__.items())[5:-3]:
                    if value == '':
                        info_to_ask = info
                        break
                    
                resps += self.responses('info', info_to_ask)
                        
        for response in resps:
            send_msg(self.logger, response, self.client.phone)
            
        self.responded = True


    def responses(self, type, content):
        self.save_msg('bot', f'{type} {content}')
        resps = []

        for resp in RESPONSES[type][content]:
            if resp['type'] in ['text', 'interactive']:
                resp_obj = {
                    'type': 'text',
                    'body': {
                        'body': self.treat_response_text(resp)
                    }
                }
            elif resp['type'] == 'contacts':
                resp_obj = {
                    'type': resp['type'],
                    'body': resp['contacts']
                }
                
            resps.append(resp_obj)

        return resps


    def treat_response_text(self, response):
        role = self.client.role if self.client.role else 'parent'
        text = response['base_content'] + response[f'{role}_content']
        
        treated_text = ''
        i = 0
        a = text.split('{')
        b = text.split('}')

        treated_text += a[i].split('}')[-1]
        while True:
            i += 1
            try:
                var = text[len('{'.join(a[:i]))+1 : -(len('}'.join(b[i:]))+1)]
                
                if var == 'name':
                    treated_text += self.client.name
                elif var == 'n_missing_info':
                    treated_text += str(self.client.n_missing_info)
                
                treated_text += b[i].split('{')[0]
            except IndexError:
                break
            
        if response['type'] == 'interactive':
            treated_text += '\nResponda com o número da opção'
            for i, opt in enumerate(response['options'], 1):
                treated_text += f'\n{i}-{opt}'
                
        return treated_text


    def get_post_messages(self):
        return get_message_history(self.logger, self.client.phone)


    def mark_as_read(self):
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": self.msg_id
        }
        
        post = post_req_messages(data)
        self.logger.debug('Mark as read: ' + post.content.decode())


    def save_msg(self, by, msg):
        msg = msg.replace("\n", "\t") # Replace new lines by tabs for reading simplicity
        
        file = open(f'conversations/{self.client.phone}.txt', 'a', encoding='utf-8')
        msg_record = f'[{dt.datetime.now().strftime("%d/%m/%Y-%H:%M:%S.%f")}] {by}: {msg}\n'
        file.write(msg_record)


    def treat_site_follow_up_msg(self, msg):
        treated_msg = unidecode(msg.lower())
        
        if 'nao' in treated_msg:
            self.respond('base', 'site_follow_up_no')
        else:
            self.respond('base', 'site_follow_up_yes')
            self.respond('info', 'role')


    def treat_role_msg(self, msg):
        options = {
            1: 'parent',
            2: 'athlete',
            3: 'other'
        }
        
        msg = get_option_interactive_msg(msg, range(1, len(options) + 1))
        if not msg:
            self.respond('instruction', 'role')
            return
        
        self.client.role = options[msg]


    def treat_name_msg(self, msg):
        treated_msg = unidecode(msg)
        salutations = [
            'oi',
            'oii',
            'oiii'
            'ola',
            'eae',
            'eai',
        ]
        checks = [
            len(msg.split(' ')) >= 6
        ]
        if any(checks):
            self.respond('instruction', 'name')
            return
        
        self.client.name = msg


    def treat_athlete_name_msg(self, msg:str):
        normalized_msg = normalize_string(msg.upper().split()[0])
        
        headers = {
            "User-Agent": "python-urllib/brasilio-client-0.1.0",
            "Authorization": f"Token {os.environ['BRASIL_IO_API_KEY']}"
        }
        name_request = r.get(f"https://api.brasil.io/v1/dataset/genero-nomes/nomes/data?search={normalized_msg}", headers=headers)

        possible_names = []
        if name_request.status_code != 200:
            content = json.dumps(json.loads(name_request.content), indent=2) if name_request.status_code != 522 else 'Connection timed out'
            send_email(
                'Brasil IO API error',
                f'Api returned code {name_request.status_code}',
                content,
                os.environ['EMAIL_DEV']
            )
            names_dataset = csv.DictReader(open('nomes.csv', 'r'))
            for name in names_dataset:
                if name['first_name'] == normalized_msg:
                    possible_names.append(name)
                    break
        else:
            possible_names = json.loads(name_request.content)['results']
        
        if not self.client.set_athlete_name(msg):
            self.respond('instruction', 'athlete_name')
            return
        
        for name in possible_names:
            if name['first_name'] == normalized_msg:
                gender = {
                    'M': 'Male',
                    'F': 'Female'
                }
                self.client.set_gender(gender[name['classification']])
                return

        send_email(
            'Cliente com nome duvidoso',
            'Favor checar informações do cliente para registro, cheque pelo link abaixo',
            f'{os.environ["WEBHOOK_URL"]}/checkinfos?id={self.client.phone}',
            os.environ['EMAIL_ATTENDANT']
        )
        open('clients/openforedit.txt', 'a').write(f'{self.client.phone}\n')


    def treat_athlete_birth_msg(self, msg):
        if not self.client.set_athlete_birth(msg):
            self.respond('instruction', 'athlete_birth')


    def treat_sport_msg(self, msg):
        options = {
            1: 'Soccer',
            2: 'Tennis',
            3: 'Basketball',
            4: 'Volleyball',
            5: 'Football',
            6: 'Track & Field',
            7: 'Golf',
            8: 'Baseball',
            9: 'Cross Country',
            10: 'Lacrosse',
            11: 'Performance'
        }

        msg = get_option_interactive_msg(msg, range(1, len(options) + 1))
        if msg:
            if not self.client.set_sport(options[msg]):
                self.respond('instruction', 'sport')


    def treat_email_msg(self, msg):
        if not self.client.set_email(msg):
            self.respond('instruction', 'email')


    def treat_date_to_go_msg(self, msg):
        date_related_words = [
            'dia',
            'semana',
            'mes',
            'ano',
            'temporada',
            'férias',
            'outono',
            'inverno',
            'verao',
            'primavera',
            'janeiro',
            'fevereiro',
            'marco',
            'abril',
            'maio',
            'junho',
            'julho',
            'agosto',
            'setembro',
            'outubro',
            'novembro',
            'dezembro',
            str(dt.date.today().year),
            str(dt.date.today().year + 1),
            str(dt.date.today().year + 2)
        ]
        if any([word in normalize_string(msg.lower()) for word in date_related_words]):
            self.client.date_to_go = msg
        else:
            self.client.date_to_go = 'Não sabe: ' + msg
