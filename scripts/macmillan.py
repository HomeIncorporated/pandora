#!/usr/bin/env python

import requests
import json
import utils

from bs4 import BeautifulSoup
from models import File, Term

NAME = 'macmillan'


def stripped_text(node):
    if node is None:
        return None
    return node.get_text().strip()


def get_data(query, lang):
    if lang != 'en':
        return None

    url = f'https://www.macmillandictionary.com/dictionary/british/{query}'
    headers = {
        'User-Agent': 'script',
        'Accept': 'text/html',
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')

    #get transcription
    transcriptions = soup.find_all(class_='PRON')
    for t in transcriptions:
        yield ('transcription',
               Term(text=stripped_text(t).replace('/', ''),
                    lang=lang,
                    region=None))

    #get tags
    crop_text = stripped_text(soup.find(class_='zwsp'))
    #remove bad substring
    part_speech = stripped_text(soup.find(class_='PART-OF-SPEECH')).replace(
        crop_text, '')
    syntax_coding = stripped_text(soup.find(class_='SYNTAX-CODING'))

    yield ('tag', Term(text=part_speech, lang=lang, region=None))
    yield ('tag', Term(text=syntax_coding, lang=lang, region=None))

    #get defenition
    defenitions = soup.find_all(class_='DEFINITION')
    for d in defenitions:
        yield ('definition', Term(text=stripped_text(d),
                                  lang=lang,
                                  region=None))

    #get examples
    examples = soup.find_all(class_='EXAMPLES')
    for e in examples:
        yield ('in', Term(text=stripped_text(e), lang=lang, region=None))
    examples = soup.find_all(class_='PHR-XREF')
    for e in examples:
        yield ('in', Term(text=stripped_text(e), lang=lang, region=None))

    #get synonyms
    synonyms = soup.find_all(class_='synonyms')
    for allsyn in synonyms:
        subsynonyms = allsyn.find_all(class_='theslink')
        for syn in subsynonyms:
            if (not '...' in syn.text):
                yield ('synonym',
                       Term(text=stripped_text(syn), lang=lang, region=None))

    #get audio
    audio = soup.find(class_='audio_play_button')
    yield ('audio', File(url=audio['data-src-mp3'], region=None))
    yield ('audio', File(url=audio['data-src-ogg'], region=None))


def main():
    (text, lang) = utils.find_audio_args()
    result = get_data(text, lang)
    print(utils.dump_json(result))


if __name__ == '__main__':
    main()
