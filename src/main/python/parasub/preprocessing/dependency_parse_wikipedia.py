'''
Created on Jul 7, 2017

This script reads Wikipedia articles in Json format, one per line (as those extracted by WikiExtractor),
from the input stream, passes them to Stanford CoreNLP for dependency parsing and co-ref resolution, and writes
CoreNLP's response to standard output. 

@author: marco
'''

import logging
import sys
import json
import re
import requests

LINK_REGEX = re.compile(r'<a href=("[^"]*")>([^<]*)</a>')

CORENLP_BASE_URL = 'http://localhost:9000/?properties='

CORENLP_PROPS = {
    "annotators": "tokenize,ssplit,pos,lemma,ner,depparse,coref",
    "coref.md.type": "dep",
    "ssplit.newlineIsSentenceBreak": "always",
    "coref.mode": "statistical",
    "parse.model": "edu/stanford/nlp/models/srparser/englishSR.ser.gz",
    "timeout": None,
    "outputFormat": "json",
}

CORENLP_URL = CORENLP_BASE_URL + json.dumps(CORENLP_PROPS)

def main():
    for line in sys.stdin:
        article = json.loads(line.decode("utf-8"))
        wid = article["id"]
        title = article["title"]
        raw_text = article["text"]

        paragraphs = raw_text.split("\n\n")
        logging.info(u"Processing {} - {} (len {}, {} paragraphs)".format(title, wid, len(raw_text), len(paragraphs)))
        for i, raw_paragraph in enumerate(paragraphs):
            links = []
            raw_text_cursor = 0
            text = u""
            for m in re.finditer(LINK_REGEX, raw_paragraph):
                link_ref, anchor = m.group(1), m.group(2)
                text += raw_paragraph[raw_text_cursor:m.start()]
                links.append((len(text), len(text) + len(anchor), link_ref))
                text += anchor
                raw_text_cursor = m.end()
            
            text += raw_paragraph[raw_text_cursor:]
            
            logging.info(u"Annotating paragraph {} (len {})".format(i, len(text)))
            corenlp_response = requests.post(CORENLP_URL, data=text.encode("utf-8")).json()
            out_data = {
                'wid': wid,
                'title': title,
                'paragraph_id': i,
                'paragraph_text': text,
                'links': [(start, end, text[start:end], ref) for start, end, ref in links],
                'corenlp_response': corenlp_response,
                } 
            out_str = json.dumps(out_data, ensure_ascii=False).encode('utf-8')
            sys.stdout.write(out_str)
            sys.stdout.write("\n")
            sys.stdout.flush()
            
        logging.info(u"Done {} ({})".format(title, wid))
        

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
