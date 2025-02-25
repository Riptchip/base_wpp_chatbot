import os
import json
import logging
from dotenv import load_dotenv

from utils import *
from client_message import ClientMessage
from dictionaries import INFO_TRANSLATION

from flask import Flask, Response, request, send_file

logging.basicConfig(
    filename='record.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)

app = Flask(__name__)
load_dotenv()
    
@app.route("/whatsapp", methods=['GET'])
def wpp_config():
    app.logger.info(f'GET request from {request.headers.get("User-Agent")}')
    resp = Response()
    resp.status_code = 200
    resp.headers['Cache-Control'] = 'no-cache'
    params = request.args.to_dict()
    
    respBody = 'placeholder'
    if not "hub.mode" in params:
        respBody = "Invalid params"
    else:
        if params["hub.verify_token"] != os.environ["TEST_TOKEN"]:
            respBody = "Invalid token"
        elif params["hub.mode"] == 'subscribe':
            respBody = params["hub.challenge"]

    resp.data = respBody

    log_request(request, resp)
    return resp

@app.route("/whatsapp", methods=['POST'])
def wpp_event_notification_handler():
    resp = Response()
    resp.headers['Cache-Control'] = 'no-cache'
    resp.status_code = 400
    resp.data = "Invalid event"
        
    if not "X-Hub-Signature-256" in request.headers:
        app.logger.info('POST request without X-Hub-Signature-256 header')
    elif validate_signature(request.get_data(), request.headers["X-Hub-Signature-256"]):
            
            received = request.json['entry'][-1]['changes'][-1]['value']
            
            app.logger.info(f'{request.headers.get("User-Agent")} sent valid payload')

            resp.status_code = 200
            resp.data = 'Valid payload'
            
            if 'messages' in received:
                resp.data += 'with message'
                client_msg = ClientMessage(app.logger, received)
                if not client_msg.client.registered():
                    client_msg.handle_msg()
                    if not client_msg.responded: client_msg.respond()
                    client_msg.client.save_info()
                    client_msg.client.check_submit()
                elif not client_msg.history:
                    client_msg.mark_as_read()
                    client_msg.respond('base', 'registered')
            else:
                # app.logger.info(f'Request without message: {request.json}')
                resp.data += 'No message'
    else:
        app.logger.info(f'{request.headers.get("User-Agent")} sent invalid payload')

    log_request(request, resp)
    return resp

@app.route("/messages", methods=['GET'])
def view_messages():
    id = request.args.get('id')
    token = request.args.get('token')
    
    for line in open('tokens.txt', 'r').readlines():
        line_client_phone, datetime_token, line_token = line[:-1].split(';')
        
        id_check = id == line_client_phone
        datetime_check = dt.datetime.now() - dt.datetime.strptime(datetime_token, "%d/%m/%Y-%H:%M:%S.%f") < dt.timedelta(days=10)
        token_check = line_token == token
        if all([id_check, datetime_check, token_check]):
            page = open(f'conversations/{id}.txt', 'r', encoding='utf-8').read()
            page = '<h3>' + page.replace('\n', '<br>') + '</h3>'
            return send_file(page, as_attachment=False, download_name=f'messages_{id}.txt', mimetype='text/html')

    resp = Response()
    resp.status_code = 404
    resp.data = "Messages not found"
    
    log_request(request, resp)
    return resp
    
@app.route("/out", methods=['GET'])
def last_req_log():
    resp = Response()
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Type'] = 'application/json'

    resp.data = str(json.load(open('log.json', 'r'))).replace("'", '"')

    resp.headers['Content-Lenght'] = len(resp.data)
    
    return resp
