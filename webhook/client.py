from utils import *
from dictionaries import INFO_TRANSLATION
from agendor import Agendor
from detect_mashing import is_mashing

import os
import re
import datetime as dt
from dateutil.relativedelta import relativedelta
from typing import Tuple
from enum import Enum

import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type, NumberParseException
from pyisemail import is_email

SearchClient = Enum('SearchClient', ['NOT_FOUND', 'PHONE_FOUND', 'EMAIL_FOUND', 'NAME_FOUND', 'NICKNAME_FOUND', 'ID_FOUND', 'ERROR'])

class Client:
    def __init__(self, logger, phone='') -> None:
        self.logger = logger
        self.id = ''
        self.role = '' # parent / athlete / other
        self.name = ''
        self.phone = phone
        self.email = ''
        self.athlete_name = ''
        self.athlete_birth = ''
        self.sport = ''
        self.date_to_go = ''
        self.gender = ''
        self.n_missing_info = 0
        
        if phone:
            self.get_info(phone)
        

    def from_crm_obj(self, obj):
        self.id = obj.get("id")
        self.name = obj.get("name")
        
        self.set_phone(obj.get("contact").get("whatsapp"))
        self.set_email(obj.get("contact").get("email"))
        
        self.role = obj.get("customFields").get("role")
        self.set_athlete_name(obj.get("customFields").get("athlete_name"))
        self.set_athlete_birth(obj.get("customFields").get("athlete_birth"))
        self.set_sport(obj.get("customFields").get("sport"))
        self.set_gender(obj.get("customFields").get("gender"))
        self.date_to_go = obj.get("customFields").get("date_to_go")
        
        if obj.get("organization"): self.representant = obj.get("organization").get("id")
        return self
    
    
    def to_crm_obj(self):
        customFields = [
            "role",
            "athlete_name",
            "athlete_birth",
            "sport",
            "date_to_go",
            "gender"
        ]
        
        obj = {
            "id": self.id,
            "name": self.name,
            "contact": {
                "email": self.email,
                "whatsapp": "+" + self.phone
            },
            "description": "\n".join([f"{INFO_TRANSLATION[key]}: {val}" for key, val in self.__dict__.items() if key in customFields]),
            "customFields": {key: val for key, val in self.__dict__.items() if key in customFields}
        }
        if self.representant:
            obj['organization'] = self.representant
            
        return obj
        
        
    def search(self, local=True, ignore=[]) -> Tuple[SearchClient, dict]:
        if local:
            return self.search_in_local_data(ignore)
        else:
            return self.search_in_crm_data(ignore)
                
                
    def search_in_local_data(self, ignore=[]):
        for file in os.listdir('clients/'):
            if not file.replace('.txt', '').isnumeric(): continue
            
            client = Client(self.logger, file.replace('.txt', ''))
            
            search = self.search_by_client(client, ignore)
            if not search in [SearchClient.ERROR, SearchClient.NOT_FOUND]:
                return (search, client.to_crm_obj())
            
        return (SearchClient.NOT_FOUND, {})
    
    
    def search_in_crm_data(self, ignore=[]):
        i = 0
        while True:
            i += 1
        
            response = Agendor(self.logger, 'people', body={
                'page': i,
                'per_page': 100
            }).request()
            
            data = response.json().get('data')
            if response.status_code != 200 or not data:
                return (
                    SearchClient.ERROR,
                    {
                        'code': response.status_code,
                        'headers': response.headers,
                        'content': response.content.decode()
                    }
                )
            
            for client in data:
                search = self.search_by_client(Client(self.logger).from_crm_obj(client), ignore)
                if not search in [SearchClient.ERROR, SearchClient.NOT_FOUND]:
                    return (search, client)
            
            if len(data) < 100:
                return (SearchClient.NOT_FOUND, {})
    
    
    def search_by_client(self, client, ignore=[]) -> SearchClient:
        if self.id == client.id and self.id and (not SearchClient.ID_FOUND in ignore):
            return SearchClient.ID_FOUND
        if self.name == client.name and self.name and (not SearchClient.NICKNAME_FOUND in ignore):
            return SearchClient.NICKNAME_FOUND
        if self.athlete_name == client.athlete_name and self.athlete_name and (not SearchClient.NAME_FOUND in ignore):
            return SearchClient.NAME_FOUND
        if self.phone == client.phone and self.phone and (not SearchClient.PHONE_FOUND in ignore):
            return SearchClient.PHONE_FOUND
        if self.email == client.email and self.email and (not SearchClient.EMAIL_FOUND in ignore):
            return SearchClient.EMAIL_FOUND
            
        return SearchClient.NOT_FOUND
        
        
    def is_new(self):
        return not os.path.exists(f'clients/{self.phone}.txt')
        
    def get_info(self, waid):
        if self.is_new():
            self.n_missing_info = 5
            return
            
        with open(f'clients/{waid}.txt', 'r', encoding='utf-8') as f:
            infos = [info[:-1] for info in f.readlines()]
            self.logger.debug(f'infos {len(infos)}'.encode('utf-8'))
            for var, info in zip(list(self.__dict__.keys())[1:-2], infos):
                self.__dict__[var] = info
                if var in ['gender', 'id']: continue
                if info == '': self.n_missing_info += 1

        self.logger.debug(self.n_missing_info)

    def save_info(self):
        # Update CRM with client base infos and reminder to follow up
        if self.email:
            upsert = Agendor(self.logger, 'people/upsert', 'POST', self.to_crm_obj()).request()
            
            if upsert.status_code not in [200, 201]:
                send_email('Error on updating CRM', f'error on updating CRM of client with email: {self.email}, status code: {upsert.status_code}', str(upsert.content), os.environ['EMAIL_DEV'])
            elif not self.id:
                task_data = {
                    "text": f"Responder Whatsapp do cliente {self.athlete_name}",
                    "due_date": dt.date.strftime(dt.date.today() + dt.timedelta(days=2), "%d/%m/%Y")
                }
                self.id = json.loads(upsert.content)['data']['id']
                task = Agendor(self.logger, f'people/{self.id}/tasks', 'POST', task_data).request()
                if task.status_code not in [200, 201]:
                    send_email('Error on creating CRM task', f'error on creating CRM task for client with email: {self.email}, status code: {task.status_code}', str(task.content), os.environ['EMAIL_DEV'])

        # Save client infos on server database
        with open(f'clients/{self.phone}.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(map(lambda val: str(val) if val else '', list(self.__dict__.values())[1:-1])) + '\n')
            
    def registered(self):
        if self.n_missing_info == 0:
            return True
        
        return False
    
    def send_form_follow_up(self):
        follow_up_template_msg = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.phone,
            "type": "template",
            "template": {
                "name": "acompanhamento_formulario_sites",
                "language": {
                    "code": "pt_BR"
                },
                "components": [{
                    "type": "body",
                    "parameters": [{
                        "type": "text",
                        "parameter_name": "name",
                        "text": self.name
                    }]
                }]
            }
        }
        
        response = post_req_messages(follow_up_template_msg)
        self.logger.debug(f'{response.status_code} {response.content}')
        
        if response.status_code != 200:
            return False
        
        file = open(f'conversations/{self.phone}.txt', 'a', encoding='utf-8')
        msg_record = f'[{dt.datetime.now().strftime("%d/%m/%Y-%H:%M:%S.%f")}] bot: base site_follow_up\n'
        file.write(msg_record)

        return True
    
    
    def set_phone(self, phone:str) -> bool:
        if not phone:
            return False
            
        if phone[0] == '+': phone = phone.replace('+', '')
        phone = phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
        
        if not phone.isnumeric(): return False
        
        try:
            phone_var = phonenumbers.parse('+' + phone, None)
        except NumberParseException:
            try:
                phone_var = phonenumbers.parse(phone, 'BR')
            except NumberParseException:
                return False
            
        if phonenumbers.is_valid_number(phone_var) and carrier._is_mobile(number_type(phone_var)):
            self.phone = phonenumbers.format_number(phone_var, phonenumbers.PhoneNumberFormat.E164)[1:]
            return True
        
        return False
    
    
    def set_athlete_name(self, athlete_name:str) -> bool:
        if not athlete_name:
            return False
        
        if is_mashing(athlete_name) or len(athlete_name.split()) < 2 or len(athlete_name.split()) >= 20:
            self.logger.debug('Keyboard mashing detected')
            return False
        
        self.athlete_name = athlete_name
        return True
    
    
    def set_gender(self, gender:str) -> bool:
        if not gender in ['Male', 'Female']:
            return False
        
        self.gender = gender
        return True
    
    
    def set_athlete_birth(self, athlete_birth:str, max_age:int=21) -> bool:
        athlete_birth = re.sub('[^0-9]','', athlete_birth)
        athlete_birth = athlete_birth[:2] + '/' + athlete_birth[2:4] + '/' + athlete_birth[4:]
        
        try:
            birth_dt = dt.datetime.strptime(athlete_birth, "%d/%m/%Y")
        except ValueError:
            return False
        
        if not relativedelta(dt.datetime.now(), birth_dt).years in range(5, max_age):
            return False
        
        self.athlete_birth = athlete_birth
        return True
    
    
    def set_sport(self, sport:str) -> bool:
        avaible_sports = [
            'Soccer',
            'Tennis',
            'Basketball',
            'Volleyball',
            'Football',
            'Track & Field',
            'Golf',
            'Baseball',
            'Cross Country',
            'Lacrosse',
            'Performance'
        ]
        
        if not sport in avaible_sports:
            return False
        
        self.sport = sport
        return True
    
    
    def set_email(self, email:str) -> bool:
        for word in email.split():
            if is_email(word, check_dns=True):
                self.email = word
                return True
            
        return False
