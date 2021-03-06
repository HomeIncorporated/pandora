#!/usr/bin/env python3

import os
import requests
import api
import resetdb as resetdb_impl
import audiosource
import unsplash
import utils

from langdetect import detect
from functools import wraps
from flask import Flask, request, jsonify, Response
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.debug = True
done = 'done!'

api.flask_app = app

PROXY_HEADERS = [
    'X-Forwarded-For',
    'X-Forwarded-Port',
    'X-Forwarded-Proto',
    'X-Real-Ip',
]


def get_proxy_headers():
    result = {}
    for k in PROXY_HEADERS:
        if k in request.headers:
            result[k] = request.headers.get(k)
    return result


def get_api_token():
    auth = request.headers.get('Authorization', '').split(' ')
    if len(auth) == 2 and auth[0].lower() == 'bearer':
        return auth[1]
    return None


def auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_ok = False
        token = get_api_token()
        if token is not None:
            api.proxy_headers = get_proxy_headers()
            resp = api.check_token(token)
            auth_ok = resp.ok
        if not auth_ok:
            secret = request.args.get('secret')
            if secret != os.getenv('ADMIN_SECRET'):
                return 'bad auth', 401
        api.access_token = token
        return f(*args, **kwargs)

    return decorated_function


@app.route('/api/pyadmin/dropall')
@auth
def dropall():
    api.drop_all()
    api.init_schema()
    return done


@app.route('/api/pyadmin/initschema')
@auth
def initschema():
    api.drop_all()
    api.init_schema()
    return done


@app.route('/api/pyadmin/resetdb')
@auth
def resetdb():
    resetdb_impl.run()
    return done


def get_lang(text):
    lang = request.args.get('lang')
    if lang is None or lang == '':
        lang = detect(text)
        if lang != 'ru':
            lang = 'en'
    return lang


@app.route('/api/lingvo/search/audio/<text>')
@auth
def find_audio(text):
    lang = get_lang(text)
    result = audiosource.find_audio(text, lang)
    return jsonify(result)


def unsplash_images(text, lang):
    return [v for k, v in unsplash.get_data(text, lang) if k == 'visual']


@app.route('/api/lingvo/search/unsplash/<text>')
@auth
def search_unsplash(text):
    lang = get_lang(text)
    result = unsplash_images(text, lang)
    return jsonify([t.url for t in result])


# TODO support different resolutions
@app.route('/api/lingvo/unsplash/<text>')
@auth
def get_unsplash_image(text):
    lang = get_lang(text)
    result = unsplash_images(text, lang)
    if len(result) == 0:
        return 'not found', 404
    url = result[0].url
    headers = {
        'User-Agent': utils.CHROME_USER_AGENT,
    }
    resp = requests.get(url, headers=headers)
    excluded_headers = [
        'content-encoding', 'content-length', 'transfer-encoding', 'connection'
    ]
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response


@app.route('/api/lingvo/term', methods=['POST'])
@auth
def create_term():
    data = request.get_json()
    id = api.add_term(data['text'], data['lang'], data.get('region', None))
    return jsonify({'uid': id})


app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
