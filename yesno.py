import spacy
import sys
import requests
import re

nlp = spacy.load('en')
# An example of different formulations of the same question
    # Who is the president of Japan?
    # Name the president of Japan
    # State the president of Japan
    # What person is the president of Japan
    # How is the president of Japan named?

params = {'action':'wbsearchentities',
          'language':'en',
          'format':'json'
          }

# Dictionary which is used to apply the appropriate unit of measure next to
# numerical values in the answer output.
dictionary_units = {
    'height':'meters',
    'area':'km squared',
    'altitude':'meters',
    'surface area':'km squared',
    'radius':'km',
    'perimeter':'km'
}

input_parser = {
    'president':'head of state',
		'ingredient':'has part',
		'member':'has part',
        'planet':'has part',
        'in':'location'
}

code_dictionary = {
    'Q83440' : 'Q6256',
    'Q8752':'Q458'
}

def inputParse(wordList):
    for x in range(0, len(wordList)):
        if wordList[x] in input_parser:
            wordList[x] = input_parser.get(wordList[x])
    return wordList

def removeUnwantedWords(wList):
    stopWords = ['an', 'a']
    for word in wordList:
        if word in stopWords:
            wordList.remove(word)
    return wList

def extractObject(t, p, obj):
    if t.dep_ == "pobj" or t.dep_ == "dobj":
        obj = []
        for d in t.subtree:
            obj.append(d.text)
        if obj[0] == "the":
            del obj[0]
    return obj

def extractSubject(t, p, sub, obj):
    print(t, p, sub, obj)
    if (t.pos_ == "PROPN" or t.dep_ == "nsubj") and t.dep_ != "attr" and t.dep_ != "pobj" and t.dep_ != "dobj" and t.text not in obj:
        print("The SUBJECT that is about to be appended:", t.text)
        sub.append(t.text) 
        # for d in t.subtree:
        #     print("SUBTREE TOKEN: " + d.text)
        #     if d.pos_ == "PROPN" and d.dep_ != "pobj" and d.dep_ != "dobj" and d.text not in obj:
        #         print(d.text)
        #         sub.append(d.text)
    print(sub)
    return sub


def getSearchPropertyIterate(prop):
    # Ok is a boolean initialized to 1 to extract only one answer. Ok becomes 0
    # after an answer has been extracted
    search_property = " ".join(prop)
    print(search_property)
    params['search'] = search_property
    params['type'] = 'property';
    json = requests.get(url,params).json()
    query_property = []
    if 'search' in json:
        for result in json['search']:
            query_property.append(result['id'])
    return query_property


def getSearchObject(obj):
    # Ok is a boolean initialized to 1 to extract only one answer. Ok becomes 0
    # after an answer has been extracted
    ok = 1
    search_object = " ".join(obj)
    print(search_object)
    params['search'] = search_object
    params['type'] = 'item'
    json = requests.get(url,params).json()
    query_object = '@'
    if 'search' in json:
        for result in json['search']:
            if ok == 1:
                ok = 0
                query_object = result['id']
    return query_object

def getSearchSubject(sub):
    # Ok is a boolean initialized to 1 to extract only one answer. Ok becomes 0
    # after an answer has been extracted
    ok = 1
    search_subject = " ".join(sub)
    print(search_subject)
    params['search'] = search_subject
    params['type'] = 'item'
    json = requests.get(url,params).json()
    query_subject = '@'
    if 'search' in json:
        for result in json['search']:
            if ok == 1:
                ok = 0
                query_subject = result['id']
    return query_subject

def extractProperty(t, p, prop):
    print("DEPENDENCY OF PROPERTY", t.text, " = ", t.dep_)
    if (t.dep_ == "attr" or t.pos_ == "NOUN") and (t.dep_ != "dobj" and t.dep_ != "pobj"):
        for d in t.subtree:
            if (d.dep_ == "attr" or d.pos_ == "NOUN") and (d.dep_ != "dobj" and d.dep_ != "pobj"):
                prop.append(d.text)
                print("APPENDED PROPERTY LIST = ", d.text)
    if not prop:
        if t.dep_ == "prep":
            prop.append(t.text)
    return prop

def checkProperty(qs, qp):
    if qp == []:
        return False
    print(qs, qp, "<- In check property")
    query='''
    ASK {
    wd:''' + qs + ''' wdt:''' + qp + ''' ?value  .
    }
    '''
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    print("data.get(boolean) = ", data.get('boolean'))
    return data.get('boolean')



def printAnswer(data):
    print(data.get('boolean'))

def fireQueryYesNo(qs, qp, qo):
    query='''
    ASK {
    wd:''' + qs + ''' wdt:''' + qp + ''' wd:''' + qo +''' .
    }
    '''
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    return data

def fireQueryYesNoNoProperty(qs, qo):
    query='''
    ASK {
    wd:''' + qs + ''' ?value wd:''' + qo +''' .
    }
    '''
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    return data

for w in sys.stdin:
    # Initialize lists.
    obj = []
    sub = []
    data = []
    prop = []

    # Set up initial parameters.
    url = 'https://www.wikidata.org/w/api.php'
    params['type'] = 'item'

    # Parse the input as a list of words.
    #wordList = re.sub("[^\w]", " ",  w).split()
    #wordList = removeUnwantedWords(wordList)
    
    # Convert the input from a word of list to nlp strip
    #stri = " ".join(wordList)
    #w = stri
    parse = nlp(w.strip())
    
    # Checks whether an answer has been given.
    answer_given = 0

    print("Objects:")
    for token in parse:
        obj = extractObject(token, parse, obj)
    print("Object after extraction: ", obj)
        #print("\t".join((token.text, token.lemma_, token.pos_,token.tag_, token.dep_, token.head.lemma_)))
    print("Subjects:")
    for token in parse:
        # print("TOKEN OF SUBJECT:", token.text)
        sub = extractSubject(token, parse, sub, obj)
    print("Subject after extraction: ", sub)
    print("Properties:")
    for token in parse:
        prop = extractProperty(token ,parse, prop)
    print("Property after extraction: ", prop)
    inputParse(prop)
    query_subject = getSearchSubject(sub)
    print("SUBJECT CODE ", query_subject)
    query_object = getSearchObject(obj)
    if query_object in code_dictionary:
        query_object = code_dictionary.get(query_object)
    print("OBJECT CODE: ", query_object)
    query_property = getSearchPropertyIterate(prop)
    print("!!!!!!!!!!!!!!!!!", query_property)
    print("PROPERTY CODE ", query_property)
    if (query_subject != '@' and query_object != '@'):
        if (len(query_property) == 0):
            print("NO PROPERTY")
            data = fireQueryYesNoNoProperty(query_object, query_subject)
            if data.get('boolean') == False:
                data = fireQueryYesNoNoProperty(query_subject, query_object)
            if data.get('boolean') == True:
                answer_given = 1
        if query_object != '@' and query_property and query_subject != '@':
            for item in range(0, len(query_property)):
                if checkProperty(query_subject, query_property[item]):
                    data = fireQueryYesNo(query_subject, query_property[item], query_object)
                    if data.get('boolean') == True:
                        answer_given = 1
                        print("!!!!!!!!!!!!!!!!!!!!!!!!")
                        break
                else:
                    if checkProperty(query_object, query_property[item]):
                        data = fireQueryYesNo(query_object, query_property[item], query_subject)
                        print("DATA RETRIEVED: ", data.get('boolean'));
                        if data.get('boolean') == True:
                            answer_given = 1
                            print("Answer given:", answer_given)
                            break
                    else:
                        pass
                        print("NO PROPERTY")
                        data = fireQueryYesNoNoProperty(query_object, query_subject)
                        if data.get('boolean') == False:
                            data = fireQueryYesNoNoProperty(query_subject, query_object)
                        if data.get('boolean') == True:
                            answer_given = 1
                            print("??????????????????")
        # if not data.get('boolean'):
        #     query_object = getSearchObject(sub)
        #     query_property = getSearchPropertyIterate(obj)
        #     if query_object != '@' and query_property and query_subject != '@':
        #         for item in range(0, len(query_property)):  
        #             data = fireQueryYesNo(query_subject, query_property[item], query_object)
        #             if data['boolean']:
        #                 printAnswer(data)
        #                 answer_given = 1
        #                 break
    else:
        if (query_subject != '@'):
            query_object = getSearchObject(prop)
            
            if query_object in code_dictionary:
                query_object = code_dictionary.get(query_object)
            print("NO OBJECT",query_object)
            data = fireQueryYesNoNoProperty(query_object, query_subject)

            if data.get('boolean') == False:
                data = fireQueryYesNoNoProperty(query_subject, query_object)
            if data.get('boolean') == True:
                answer_given = 1
    if answer_given == 0:
        print('False')
    else:
        print('True')
    del sub[:]
    del prop[:]
    del obj[:]