#!/usr/bin/env python3
import sys
import requests
import re
import spacy

#Language Technology Practical Assignment 4
#Gabriel Leuenberger S2716151

url1 = 'https://query.wikidata.org/sparql'
url2 = 'https://www.wikidata.org/w/api.php'

paramsY = {'action':'wbsearchentities','language':'en','format':'json'}
paramsX = {'action':'wbsearchentities','language':'en','format':'json','type':'property'}

print('''
Example Questions:

What is the diameter of the universe?
Who is the emperor of China
what is the height of the Eiffel tower?
which is the nationality of Einstein

Which king does Russia have?
Which ingredients does paella contain

who is the car's inventor?
Where is Switzerland's lowest point
how big is Africa's area?
Who is Hillary's husband

Now type in your Questions:
''')

    


for line in sys.stdin:
    input = (line.rstrip()+'?').lower()
    nlp = spacy.load('en')
    result = nlp(input)
	

    sub = " "
    obj = " "
    dob = " "
    own = " "
    pre = " "
    att = " "
    

    for w in result:

        if w.dep_ == "nsubj":
            subject=[]
            for d in w.subtree:
                subject.append(d.text)
            sub = " ".join(subject)
            print('subject: ' + sub)

        if w.dep_ == "pobj":
            object=[]
            for d in w.subtree:
                object.append(d.text)
            obj = " ".join(object)
            print('object: ' + obj)

        if w.dep_ == "dobj":
            dobje=[]
            for d in w.subtree:
                dobje.append(d.text)
            dob = " ".join(dobje)
            print('dobj: ' + dob)


        if w.dep_ == "poss":
            owner=[]
            for d in w.subtree:
                owner.append(d.text)
            own = own.join(owner)
            print('owner: '+ own)
	
        if w.dep_ == "prep":
            prepo=[]
            for d in w.subtree:
                prepo.append(d.text)
            
            pre = pre.join(prepo)
            print('prep: '+ pre)
	
        if w.dep_ == "attr":
            attri=[]
            for d in w.subtree:
                attri.append(d.text)
            att = " ".join(attri)
            print('attr: '+ att)


    mpre = re.search('of (.*)', pre)
    mown = re.search('(.*)\'s', own)
    mdoes= re.search('(.*) does (.*)', input)
    #"What is the X of Y?"-questions:
    if mpre:
        msub = re.search('(.*) ' + pre, sub)
        if msub: X = msub.group(1)
        else: X = re.search('(.*) ' + pre, att).group(1)
        Y = mpre.group(1)
    #"What is the Y's X?"-questions:
    elif mown:
        msub = re.search(own + ' (.*)', sub)
        if msub: X = msub.group(1)
        else: X = re.search(own + ' (.*)', att).group(1)
        Y = mown.group(1)

    #"What Y does X have?"-questions:
    elif mdoes:
        Y = sub
        X = dob

    #remove some determiners:
    mX = re.search('a (.*)', X)
    if mX: X = mX.group(1)
    mX = re.search('the (.*)', X)
    if mX: X = mX.group(1)
    mX = re.search('what (.*)', X)
    if mX: X = mX.group(1)
    mX = re.search('which (.*)', X)
    if mX: X = mX.group(1)
    mY = re.search('the (.*)', Y)
    if mY: Y = mY.group(1)

    print('X: '+ X)
    print('Y: '+ Y)

    paramsX['search'] = X
    json1 = requests.get(url2,paramsX).json()
    paramsY['search'] = Y
    json2 = requests.get(url2,paramsY).json()
    
    k = 0
    for result1 in json1['search']:
        for result2 in json2['search']: #iterate over all pairs X,Y

            #print("{}".format(result1['id']))
            #print("{}".format(result2['id']))
            query = 'SELECT ?responseLabel ?response WHERE {wd:'+("{}".format(result2['id']))+' wdt:'+("{}".format(result1['id']))+' ?response . SERVICE wikibase:label {bd:serviceParam wikibase:language "en" .}}'
            #print(query)
            data = requests.get(url1, params={'query': query, 'format': 'json'}).json()

            for item in data['results']['bindings']:
                for var in item :
                    if(k<10):
                        print(('{}\t{}'.format(var,item[var]['value'])))
                    k = k+1
    if(k<1):
        print('no response found')