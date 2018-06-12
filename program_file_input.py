import spacy
import sys
import requests
import re

nlp = spacy.load('en')

url = 'https://www.wikidata.org/w/api.php'

params = {'action':'wbsearchentities',
          'language':'en',
          'format':'json'
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

stopWords = ['an', 'a']
current_counter = 0

def removeUnwantedWords(wList):
    for word in wList:
        if word in stopWords:
            wList.remove(word)
    return wList

def inputParse(wordList):
    for x in range(0, len(wordList)):
        if wordList[x] in input_parser:
            wordList[x] = input_parser.get(wordList[x])
    return wordList

def extractSubject(t, p, sub, last, of_counter, current_counter):
    if (t.dep_ == "nsubj" or t.dep_ == "attr" or t.dep_ == "appos" or t.dep_ == "ROOT") and (t.pos_ != "ADV" and t.pos_ != "ADJ" or t.tag_ != "WP"):
        sub = []
        for d in t.subtree:
            if d.text == "of":
                current_counter = current_counter + 1
            if (d.tag_ != "WP" and d.dep_ != "ROOT" and d.pos_ != "ADV"):
                if (d.pos_ == 'VERB' or d.pos_ == 'NOUN') and (d.tag_ != "WP" and d.dep_ != "ROOT" and d.pos_ != "ADV"):
                    sub.append(d.lemma_)
                elif d.pos_ != "ADP" and d.pos_ != "ADJ" and d.tag_ != "WP" and d.dep_ != "ROOT" and d.pos_ != "ADV":
                    sub.append(d.text)
                else:
                    if (d.text == last or current_counter != of_counter):
                        sub.append(d.text)
                    else:
                        break
        if not sub:
            sub.append(t.lemma_)
        if sub[0] == 'the':
            del sub[0]
    return sub

def extractSubjectCount(t, p, sub, last, of_counter, current_counter):
    if (t.dep_ == "nsubj" or t.dep_ == "attr" or t.dep_ == "appos" or t.dep_ == "ROOT") and (t.pos_ != "ADV" and t.pos_ != "ADJ" or t.tag_ != "WP"):
        sub = []
        for d in t.subtree:
            if d.text == "of":
                current_counter = current_counter + 1
            if (d.tag_ != "WP" and d.dep_ != "ROOT" and d.pos_ != "ADV"):
                if (d.pos_ == 'VERB' or d.pos_ == 'NOUN') and (d.tag_ != "WP" and d.dep_ != "ROOT" and d.pos_ != "ADV"):
                    sub.append(d.lemma_)
                elif d.pos_ != "ADP" and d.pos_ != "ADJ" and d.tag_ != "WP" and d.dep_ != "ROOT" and d.pos_ != "ADV":
                    sub.append(d.text)
                else:
                    if (d.text == last or current_counter != of_counter):
                        sub.append(d.text)
                    else:
                        break
        if not sub:
            sub.append(t.lemma_)
        if sub[0] == 'the':
            del sub[0]
    return sub

def extractObject(t, p, obj):
    if t.dep_ == "pobj" or t.dep_ == "dobj":
        obj = []
        for d in t.subtree:
            obj.append(d.text)
        if obj[0] == 'the':
            del obj[0]
    return obj

def extractPropertyYesNo(t, p, prop):
    if (t.dep_ == "attr" or t.pos_ == "NOUN") and (t.dep_ != "dobj" and t.dep_ != "pobj"):
        for d in t.subtree:
            if (d.dep_ == "attr" or d.pos_ == "NOUN") and (d.dep_ != "dobj" and d.dep_ != "pobj"):
                prop.append(d.text)
    if not prop:
        if t.dep_ == "prep":
            prop.append(t.text)
    return prop

def extractObjectYesNo(t, p, obj):
    if t.dep_ == "pobj" or t.dep_ == "dobj":
        obj = []
        for d in t.subtree:
            obj.append(d.text)
        if obj[0] == "the":
            del obj[0]
    return obj

def extractSubjectYesNo(t, p, sub, obj):
    if (t.pos_ == "PROPN" or t.dep_ == "nsubj") and t.dep_ != "attr" and t.dep_ != "pobj" and t.dep_ != "dobj" and t.text not in obj:
        sub.append(t.text)
    return sub

def checkForProperNouns(t, p, obj):
    if not obj:
        for t in p:
            if t.pos_ == "PROPN":
                obj = []
                for d in t.subtree:
                    obj.append(d.text)
    return obj

def extractSubjectVersionTwo(token, p, current_counter, sub, last, of_counter):
    if token.dep_ == "nsubj" or token.dep_ == "attr" or token.dep_ == "dobj" or token.dep_ == "appos":
        sub = []
        for d in token.subtree:
            if d.text == "of":
                current_counter = current_counter + 1
            if d.pos_ == 'VERB' or d.pos_ == 'NOUN':
                sub.append(d.lemma_) 
            elif d.pos_ != "ADP":
                sub.append(d.text)
            else:
                if (d.text == last or current_counter != of_counter):
                    sub.append(d.text)
                else:
                    break
        if sub[0] == 'the':
            del sub[0]
    return sub

def extractSubjectCountHmh(w):
    m = re.search("How many (.*) does (.*) have", w)
    lem = nlp(m.group(1))
    ret = []
    for token in lem:
        ret.append(token.lemma_)
    return ret

def extractObjectCountHmh(w):
    m = re.search("How many (.*) does (.*) have", w)
    return m.group(2)

def getSearchPropertyIterate(sub, reg):
    if not reg:  
        search_property = " ".join(sub)
    else:
        search_property = sub
    params['search'] = search_property
    params['type'] = 'property';
    json = requests.get(url,params).json()
    query_property = []
    if 'search' in json:
        for result in json['search']:
            query_property.append(result['id'])
    return query_property

def getSearchObject(obj, reg):
    # Ok is a boolean initialized to 1 to extract only one answer. Ok becomes 0
    # after an answer has been extracted
    ok = 1
    if not reg:
        search_object = " ".join(obj)
    else:
        search_object = obj
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

def getSearchSubject(sub, reg):
    # Ok is a boolean initialized to 1 to extract only one answer. Ok becomes 0
    # after an answer has been extracted
    ok = 1
    if not reg:
        search_subject = " ".join(sub)
    else:
        search_subject = sub
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

def checkProperty(qs, qp):
    if qp == []:
        return False
    query='''
    ASK {
    wd:''' + qs + ''' wdt:''' + qp + ''' ?value  .
    }
    '''
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    return data.get('boolean')

def fireQuery(qo, qp):
    query='''
    SELECT ?valueLabel WHERE {
    wd:''' + qo + ''' wdt:''' + qp + ''' ?value
    SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
    }
    }
    '''
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    return data

def fireQueryYesNo(qs, qp, qo):
    query='''
    ASK {
    wd:''' + qs + ''' wdt:''' + qp + ''' wd:''' + qo +''' .
    }
    '''
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    return data

def countOf(wList):
    of_counter = 0
    for i in range(0, len(wList)):
        if wList[i] == "of" or wList[i] == "of?":
            of_counter +=1;
    return of_counter


def fireQueryYesNoNoProperty(qs, qo):
    query='''
    ASK {
    wd:''' + qs + ''' ?value wd:''' + qo +''' .
    }
    '''
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    return data

def printAnswer(data):
    for item in data['results']['bindings']:
        for var in item:
            wf.write('\t{}'.format(item[var]['value']))
            
def checkIfCount(temp):
    how_check = 0
    many_check = 0
    for word in temp:
        if word.text == 'how' or word.text == 'How':
            how_check = 1
        if word.text == 'many' or word.text == 'Many':
            many_check = 1
    if (how_check and many_check):
        return True
    return False

def checkHowManyHave(temp):
    how_check = 0
    many_check = 0
    have_check = 0
    for word in temp:
        if word.text == 'how' or word.text == 'How':
            how_check = 1
        if word.text == 'many' or word.text == 'Many':
            many_check = 1
        if word.text == 'have':
            have_check = 1
    if (how_check and many_check and have_check):
        return True
    return False

def cleanHowMany(obj):
    if obj[0] == 'How' or obj[0] == 'how':
        del obj[0]
    if obj[0] == 'many':
        del obj[0]
    return obj

def answerQuestionPossesive(parse, question_number, reg, current_counter):
    url1 = 'https://query.wikidata.org/sparql'
    url2 = 'https://www.wikidata.org/w/api.php'

    paramsY = {'action':'wbsearchentities','language':'en','format':'json'}
    paramsX = {'action':'wbsearchentities','language':'en','format':'json','type':'property'}


    sub = " "
    obj = " "
    dob = " "
    own = " "
    pre = " "
    att = " "
    
    result = nlp(parse)

    for w in result:

        if w.dep_ == "nsubj":
            subject=[]
            for d in w.subtree:
                subject.append(d.text)
            sub = " ".join(subject)

        if w.dep_ == "pobj":
            object=[]
            for d in w.subtree:
                object.append(d.text)
            obj = " ".join(object)

        if w.dep_ == "dobj":
            dobje=[]
            for d in w.subtree:
                dobje.append(d.text)
            dob = " ".join(dobje)

        if w.dep_ == "poss":
            owner=[]
            for d in w.subtree:
                owner.append(d.text)
            own = own.join(owner)
	
        if w.dep_ == "prep":
            prepo=[]
            for d in w.subtree:
                prepo.append(d.text)
            
            pre = pre.join(prepo)
	
        if w.dep_ == "attr":
            attri=[]
            for d in w.subtree:
                attri.append(d.text)
            att = " ".join(attri)

    mown = re.search('(.*)\'s', own)
    msub = re.search(own + ' (.*)', sub)
    if msub: X = msub.group(1)
    else:
        X = re.search(own + ' (.*)', att)
        if X is None:
            return
        else:
            X = re.search(own + ' (.*)', att).group(1)
    if mown is None:
        return
    else:
        Y = mown.group(1)

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

    paramsX['search'] = X
    json1 = requests.get(url2,paramsX).json()

    paramsY['search'] = Y
    json2 = requests.get(url2,paramsY).json()
    
    k = 0
    wf.write('{}'.format(question_number))
    for result1 in json1['search']:
        for result2 in json2['search']: #iterate over all pairs X,Y
            query = 'SELECT ?responseLabel ?response WHERE {wd:'+("{}".format(result2['id']))+' wdt:'+("{}".format(result1['id']))+' ?response . SERVICE wikibase:label {bd:serviceParam wikibase:language "en" .}}'
            data = requests.get(url1, params={'query': query, 'format': 'json'}).json()
            for item in data['results']['bindings']:
                for var in item:
                    wf.write('\t{}'.format(item[var]['value']))
    wf.write('\n');
    if(k<1):
        pass

def checkIfPossesive(parse):
    for token in parse:
        if token.text == "'s":
            return True
    return False

def typeOfQuestion(parse, question_number, reg, current_counter):
    temp = nlp(parse)
    if (temp[0].tag_ == "VBZ"):
        answerQuesetionYesNo(parse)
    elif (checkIfCount(temp)):
        if checkHowManyHave(temp):
            answerQuestionCount(parse, 'hmh')
        else:
            answerQuestionCount(parse, 'count')
    elif(checkIfPossesive(temp)):
        answerQuestionPossesive(parse, question_number, reg, current_counter)
    else:
        answerQuestionRegular(parse)

def alternate_parsing(w, answer):
    obj = []
    sub = []
    data = []
    params['type'] = 'item'

    # Parse the input as a list of words.
    wordList = re.sub("[^\w]", " ",  w).split()
    wordList = removeUnwantedWords(wordList)
    
    # Convert the input from a word of list to nlp strip
    stri = " ".join(wordList)
    w = stri
    parse = nlp(w.strip())
    
    # Take the first and last word of the input for research purposes.
    word_list = w.split()
    first = word_list[0]
    last = word_list[len(word_list)-1]

    # Take the last word without the question mark.
    if (last == "of?"):
        last = "of"

    # Checks whether an answer has been given.
    answer_given = 0

    # Count the number of "of" in the input.
    of_counter = countOf(word_list)
    current_counter = 0

    # Go through each token and extract the subject and object.
    for token in parse:
        sub = extractSubjectVersionTwo(token, parse, current_counter, sub, last, of_counter)
        obj = extractObject(token, parse, obj)
    
    # In case no object was found, check for proper nouns.
    obj = checkForProperNouns(token, parse, obj)
    sub = inputParse(sub)
    if answer == 'count':
        obj = cleanHowMany(obj)
    # Extract the search property and object to feed into the query.
    query_object = getSearchObject(obj, reg)
    query_property = getSearchPropertyIterate(sub, reg)
    if query_object != '@' and query_property:
        for item in range(0, len(query_property)):  
            data = fireQuery(query_object, query_property[item])
            if data['results']['bindings']:
                if answer == 'count':
                    wf.write('\t{}'.format(len(data['results']['bindings'])))
                else:
                    printAnswer(data)
                answer_given = 1
                break
        # Reverse the object and the subject.
        if not data['results']['bindings']:
            query_object = getSearchObject(sub, reg)
            query_property = getSearchPropertyIterate(obj, reg)
            if query_object != '@' and query_property:
                for item in range(0, len(query_property)):  
                    data = fireQuery(query_object, query_property[item])
                    if data['results']['bindings']:
                        if answer == 'count':
                            wf.write('\t{}'.format(len(data['results']['bindings'])))
                        else:
                            printAnswer(data)
                        answer_given = 1
                        break

def answerQuestionCount(w, form):
# Initialize lists.
    obj = []
    sub = []
    data = []
    # Set up initial parameters.
    params['type'] = 'item'
    reg = 0
    # Parse the input as a list of words.
    wordList = re.sub("[^\w]", " ",  w).split()
    wordList = removeUnwantedWords(wordList)
    
    # Convert the input from a word of list to nlp strip
    stri = " ".join(wordList)
    w = stri
    parse = nlp(w.strip())
    
    # Take the first and last word of the input for research purposes.
    word_list = w.split()
    first = word_list[0]
    last = word_list[len(word_list)-1]

    # Take the last word without the question mark.
    if (last == "of?"):
        last = "of"

    # Checks whether an answer has been given.
    answer_given = 0

    # Count the number of "of" in the input.
    of_counter = countOf(word_list)
    current_counter = 0
    
    data_counter = 0
    if form == 'count':
        for token in parse:
            sub = extractSubjectCount(token, parse, sub, last, of_counter, current_counter)
            obj = extractObject(token, parse, obj)
        # In case no object was found, check for proper nouns.
        obj = checkForProperNouns(token, parse, obj)
        sub = inputParse(sub)
        obj = cleanHowMany(obj)
    else:
        for token in parse:
            sub = extractSubjectCountHmh(w)
            obj = extractObjectCountHmh(w)
        reg = 1
    # Extract the search property and object to feed into the query.
    query_object = getSearchObject(obj, reg)
    query_property = getSearchPropertyIterate(sub, reg)
    wf.write('{}'.format(question_number))
    if query_object != '@' and query_property:
        for item in range(0, len(query_property)):  
            data = fireQuery(query_object, query_property[item])
            if data['results']['bindings']:
                wf.write('\t{}'.format(len(data['results']['bindings'])))
                answer_given = 1
                break
        if not data['results']['bindings']:
            query_object = getSearchObject(sub, reg)
            query_property = getSearchPropertyIterate(obj, reg)
            if query_object != '@' and query_property:
                for item in range(0, len(query_property)):  
                    data = fireQuery(query_object, query_property[item])
                    if data['results']['bindings']:
                        wf.write('\t{}'.format(len(data['results']['bindings'])))
                        answer_given = 1
                        break
    if answer_given == 0:
        alternate_parsing(w, 'count')
    wf.write('\n')

def answerQuestionRegular(w):
    # Initialize lists.
    obj = []
    sub = []
    data = []

    # Set up initial parameters.
    params['type'] = 'item'

    # Parse the input as a list of words.
    wordList = re.sub("[^\w]", " ",  w).split()
    wordList = removeUnwantedWords(wordList)
    
    # Convert the input from a word of list to nlp strip
    stri = " ".join(wordList)
    w = stri
    parse = nlp(w.strip())
    
    # Take the first and last word of the input for research purposes.
    word_list = w.split()
    first = word_list[0]
    last = word_list[len(word_list)-1]

    # Take the last word without the question mark.
    if (last == "of?"):
        last = "of"

    # Checks whether an answer has been given.
    answer_given = 0
    wf.write('{}'.format(question_number))
    # Count the number of "of" in the input.
    of_counter = countOf(word_list)
    current_counter = 0
    for token in parse:
        sub = extractSubject(token, parse, sub, last, of_counter, current_counter)
        obj = extractObject(token, parse, obj)
    # In case no object was found, check for proper nouns.
    obj = checkForProperNouns(token, parse, obj)

    # In case no subject was found, check with other subject parsing method.
    if not sub:
        for token in parse:
            sub = extractSubjectVersionTwo(token, parse, current_counter, sub, last, of_counter)
    sub = inputParse(sub)

    # Extract the search property and object to feed into the query.
    query_object = getSearchObject(obj, reg)
    query_property = getSearchPropertyIterate(sub, reg)
    if query_object != '@' and query_property:
        for item in range(0, len(query_property)):  
            data = fireQuery(query_object, query_property[item])
            if data['results']['bindings']:
                printAnswer(data)
                answer_given = 1
                break
        if not data['results']['bindings']:
            query_object = getSearchObject(sub, reg)
            query_property = getSearchPropertyIterate(obj, reg)
            if query_object != '@' and query_property:
                for item in range(0, len(query_property)):  
                    data = fireQuery(query_object, query_property[item])
                    if data['results']['bindings']:
                        printAnswer(data)
                        answer_given = 1
                        break
    if answer_given == 0:
        alternate_parsing(w, 'regular')
    wf.write('\n')
        

def answerQuesetionYesNo(w):
    # Initialize lists.
    obj = []
    sub = []
    data = []
    prop = []
    params['type'] = 'item'
    
    parse = nlp(w.strip())
    
    wf.write('{}'.format(question_number))

    # Checks whether an answer has been given.
    answer_given = 0
    for token in parse:
        obj = extractObjectYesNo(token, parse, obj)
    for token in parse:
        sub = extractSubjectYesNo(token, parse, sub, obj)
    for token in parse:
        prop = extractPropertyYesNo(token ,parse, prop)
    inputParse(prop)
    query_subject = getSearchSubject(sub, reg)
    query_object = getSearchObject(obj, reg)
    if query_object in code_dictionary:
        query_object = code_dictionary.get(query_object)
    query_property = getSearchPropertyIterate(prop, reg)
    if (query_subject != '@' and query_object != '@'):
        if (len(query_property) == 0):
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
                        break
                else:
                    if checkProperty(query_object, query_property[item]):
                        data = fireQueryYesNo(query_object, query_property[item], query_subject)
                        if data.get('boolean') == True:
                            answer_given = 1
                            break
                    else:
                        pass
                        data = fireQueryYesNoNoProperty(query_object, query_subject)
                        if data.get('boolean') == False:
                            data = fireQueryYesNoNoProperty(query_subject, query_object)
                        if data.get('boolean') == True:
                            answer_given = 1
    else:
        if (query_subject != '@'):
            query_object = getSearchObject(prop, reg)
            if query_object in code_dictionary:
                query_object = code_dictionary.get(query_object)
            data = fireQueryYesNoNoProperty(query_object, query_subject)
            if data.get('boolean') == False:
                data = fireQueryYesNoNoProperty(query_subject, query_object)
            if data.get('boolean') == True:
                answer_given = 1
    if answer_given == 0:
        wf.write('\tNo')
    else:
        wf.write('\tYes')
    wf.write('\n')

with open('test_questions.txt', 'r') as rf:
    with open('answer_questions.txt', 'w') as wf:
        reg = 0
        question_number = 0
        current_counter = 0
        for line in rf:
            question_number = question_number + 1
            question = ''
            for i in range(0, len(line)):
                if line[i].isalpha() or (line[i] == ' ' and line[i-1].isalpha() and line[i+1].isalpha()) or line[i] == "'":
                    question = question + line[i]
            typeOfQuestion(question, question_number, reg, current_counter)