import os
import json
import hashlib
import hmac
import unicodedata
import re
import ssl
import smtplib
import requests as r
import datetime as dt
from email.message import EmailMessage
from dotenv import load_dotenv

def validate_signature(data, hmac_header):
    load_dotenv()
    secret = os.environ["FB_APP_SECRET"]

    if type(data) == str:
        data = data.encode()
    elif type(data) != bytes:
        raise ValueError(f'data has to a string or bytes. Got {type(data)}')
    
    digest = hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()

    
    return hmac.compare_digest(hmac_header[7:], digest)

def send_msg(logger, msg, to_phone):
    data = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": msg['type'],
        msg['type']: json.dumps(msg['body'])
    }
    if os.environ["FLAKS_ENV"] == "production":
        post = post_req_messages(data)
        logger.debug('Send message: ' + post.content.decode())
    
def post_req_messages(data):
    load_dotenv()
    headers = {
        "Authorization": "Bearer " + os.environ["ACCESS_TOKEN"],
        "Content-Type": "application/json"
    }

    return r.post(f'https://graph.facebook.com/v19.0/{os.environ["BOT_NUMBER_ID"]}/messages', data=json.dumps(data), headers=headers)

def log_request(request, response):
    if request.data: request_data = request.json if request.json else request.form
    else: request_data = ''
        
    req = {
        'url': request.url,
        'method': request.method,
        'origin': request.origin,
        'address': request.remote_addr,
        'time': dt.datetime.now().strftime('%d/%m/%Y - %H:%M:%S.%f'),
        'headers': {},
        'body': request_data,
        'response': {
            'status-code': response.status_code,
            'headers': {},
            'body': response.data.decode()
        }
    }

    for key, value in response.headers.items():
        req['response']['headers'][key] =  value
    for key, value in request.headers.items():
        req['headers'][key] = value
        
    open('log.json', 'w').write(json.dumps(req, indent=4) + '\n')

def get_option_interactive_msg(msg, options):
    msg = msg.split()
    
    if len(msg) > 5:
        return None
    
    option = 0
    for word in msg:
        try:
            option = int(word)
            break
        except ValueError:
            pass
        
    if option in options:
        return option
        
    return None

def get_message_history(logger, phone):
    if not os.path.exists(f'conversations/{phone}.txt'):
        return []
    
    history = []
    for line in open(f'conversations/{phone}.txt', 'rb').readlines():
        msg = line.decode('utf-8')
        try:
            history.append({
                'date': dt.datetime.strptime(msg.split()[0][1:-1], "%d/%m/%Y-%H:%M:%S.%f"),
                'by': msg.split()[1][:-1],
                'content': ' '.join(msg.split()[2:])
            })
        except ValueError as e:
            logger.debug(f'MSG Error date: {msg}, from {phone}')
            raise ValueError(repr(e))
            
    return history

# This function code is from https://gist.github.com/boniattirodrigo/67429ADA53B7337D2E79
def normalize_string(string):
    # Unicode normalize transforma um caracter em seu equivalente em latin.
    nfkd = unicodedata.normalize('NFKD', string)
    normalized = u"".join([c for c in nfkd if not unicodedata.combining(c)])

    # Usa expressão regular para retornar a string apenas com números, letras e espaço
    return re.sub('[^a-zA-Z0-9\s]', '', normalized)

def send_email(subject, msg, err, email_receiver):
    email = EmailMessage()
    email.set_content(msg + '\n\n' + err)

    email['Subject'] = subject
    email['From'] = os.environ['EMAIL_SENDER']
    email['To'] = email_receiver

    with smtplib.SMTP_SSL(os.environ['EMAIL_SMTP_SERVER'], int(os.environ['EMAIL_SMTP_PORT']), context=ssl.create_default_context()) as s:
        s.login(os.environ['EMAIL_SENDER'], os.environ['EMAIL_PASSWORD'])
        s.sendmail(os.environ['EMAIL_SENDER'], email_receiver, email.as_string())

def manage_tokens(token=None, client_phone=None, tokens_path='tokens.txt', token_due=10):
    tokens = []
    for line in open(tokens_path, 'r').readlines():
        line = line[:-1]
        line_client_phone, datetime_token, line_token = line.split(';')
        
        if line_client_phone == client_phone: continue
        
        if dt.datetime.now() - dt.datetime.strptime(datetime_token, "%d/%m/%Y-%H:%M:%S.%f") < dt.timedelta(days=token_due):
            tokens.append(line)
        
    if token and client_phone:
        tokens.append(f'{client_phone};{dt.datetime.strftime(dt.datetime.now(), "%d/%m/%Y-%H:%M:%S.%f")};{token}')
        
    open(tokens_path, 'w').write('\n'.join(tokens) + '\n')
