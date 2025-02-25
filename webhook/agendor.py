from typing import Union
from utils import *

class Agendor:
    def __init__(self, logger, path, method='GET', body={}, custom_fields=True) -> None:
        self.logger = logger
        self.method = method
        self.path = path
        self.body = body
        self.custom_fields = custom_fields
        self.url = "https://api.agendor.com.br/v3/"
        self.headers = {
            "Authorization": f"Token {os.environ['AGENDOR_KEY']}",
            "Content-Type": "application/json"
        }
        
    def request(self) -> Union[bool, r.Response]:
        req_types = {
            'GET': r.get,
            'POST': r.post,
            'PUT': r.put,
            'DEL': r.delete
        }
        
        query = ''
        if self.method == 'GET':
            query_params = []
            for key, val in self.body.items():
                query_params.append(f'{key}={val}')
            
            if self.custom_fields:
                query_params.append('withCustomFields=true')
                
            query = '?' + '&'.join(query_params)
            self.body = {}
        
        if self.method in req_types:
            self.logger.debug(f'{self.method} req url: {self.url + self.path + query}')
            return req_types[self.method](self.url + self.path + query, data=json.dumps(self.body), headers=self.headers)
        else:
            return False