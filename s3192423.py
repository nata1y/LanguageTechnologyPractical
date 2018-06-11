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
        'planet':'has part'
}

def print_example_queries():
    print("1. What is the altitude of Mont Blanc?") # -Gabriel
    print("2. What city is the capital of Poland?") #  -Natasha
    print("3. Who is the CEO of Samsung?") # -Gabriel output twice
    print("4. What country is Berlin the capital of?") #  -Natasha -Gabriel
    print("5. What person is the head of state of North Korea?") #   -Natasha -Gabriel
    print("6. State the surface area of Tokyo") # -Gabriel
    print("7. Name the president of Zimbabwe") # -Gabriel
    print("8. Name the capital of the Andaman and Nicobar Islands") #  -Natasha -Gabriel
    print("9. How is the capital city of Iceland named?") 
    print("10. What person is the president of Romania?")  # -Natasha -Gabriel
        
def removeUnwantedWords(wList):
    stopWords = ['an', 'a']
    for word in wordList:
        if word in stopWords:
            wordList.remove(word)
    return wList

def inputParse(wordList):
    for x in range(0, len(wordList)):
        if wordList[x] in input_parser:
            wordList[x] = input_parser.get(wordList[x])
    return wordList

print_example_queries()

def countOf(wList):
    of_counter = 0
    for i in range(0, len(word_list)):
        if word_list[i] == "of" or word_list[i] == "of?":
            of_counter +=1;
    return of_counter

def extractSubject(t, p, current_counter, sub):
    if token.dep_ == "nsubj" or token.dep_ == "attr" or token.dep_ == "dobj" or token.dep_ == "appos":
        sub = []
        print(token.text, "!!!")
        for d in token.subtree:
            print(d.text, "SUBTREEEEEEE")
            if d.text == "of":
                current_counter = current_counter + 1
            if d.pos_ == 'VERB' or d.pos_ == 'NOUN':
                print(d.lemma_, "lemmatized appended!")
                sub.append(d.lemma_) 
            elif d.pos_ != "ADP":
                sub.append(d.text)
                print(d.text, " appended!")
            else:
                if (d.text == last or current_counter != of_counter):
                    sub.append(d.text)
                    print(d.text, " of appended!")
                else:
                    break
        if sub[0] == 'the':
            del sub[0]
    return sub

def extractObject(t, p, obj):
    if t.dep_ == "pobj":
        obj = []
        for d in t.subtree:
            obj.append(d.text)
        if obj[0] == 'the':
            del obj[0]
    return obj
    
def checkForProperNouns(t, p, obj):
    if not obj:
        for token in parse:
            if token.pos_ == "PROPN":
                obj = []
                for d in token.subtree:
                    obj.append(d.text)
    return obj

def getSearchProperty(sub):
    # Ok is a boolean initialized to 1 to extract only one answer. Ok becomes 0
    # after an answer has been extracted
    ok = 1
    search_property = " ".join(sub)
    print(search_property)
    params['search'] = search_property
    params['type'] = 'property';
    json = requests.get(url,params).json()
    query_property = '@'
    if 'search' in json:
        for result in json['search']:
            if ok == 1:
                ok = 0
                query_property = result['id']
    return query_property

def getSearchPropertyIterate(sub):
    # Ok is a boolean initialized to 1 to extract only one answer. Ok becomes 0
    # after an answer has been extracted
    search_property = " ".join(sub)
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

def fireQuery(qo, qp):
    query='''
    SELECT ?valueLabel WHERE {
    wd:''' + qo + ''' wdt:''' + qp + ''' ?value
    SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
    }
    }
    '''
    # print(query)
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    return data

def printAnswer(data):
    if not data['results']['bindings']:
        print('Unable to retrieve answer.')
    else:
        for item in data['results']['bindings']:
            for var in item:
                sys.stdout.write('{}'.format(item[var]['value']))
                sys.stdout.write('\n')

for w in sys.stdin:
    # Initialize lists.
    obj = []
    sub = []
    data = []

    # Set up initial parameters.
    url = 'https://www.wikidata.org/w/api.php'
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

    # Before continuing, here we would determine whether the question is a YES/NO question,
    # a count question or a regular question.

    # Function goes here..#

    # Go through each token and extract the subject and object. FOR QUESTIONS
    # OTHER THAN YES/NO. This should be a function.
    for token in parse:
        print("\t".join((token.text, token.lemma_, token.pos_,token.tag_, token.dep_, token.head.lemma_)))
        sub = extractSubject(token, parse, current_counter, sub)
        obj = extractObject(token, parse, obj)
    
    # In case no object was found, check for proper nouns.
    obj = checkForProperNouns(token, parse, obj)
    sub = inputParse(sub)

    # Extract the search property and object to feed into the query.
    query_object = getSearchObject(obj)
    query_property = getSearchPropertyIterate(sub)
    if query_object != '@' and query_property:
        for item in range(0, len(query_property)):  
            data = fireQuery(query_object, query_property[item])
            if data['results']['bindings']:
                printAnswer(data)
                answer_given = 1
                break
        if not data['results']['bindings']:
            query_object = getSearchObject(sub)
            query_property = getSearchPropertyIterate(obj)
            if query_object != '@' and query_property:
                for item in range(0, len(query_property)):  
                    data = fireQuery(query_object, query_property[item])
                    if data['results']['bindings']:
                        printAnswer(data)
                        answer_given = 1
                        break
    if answer_given == 0:
        print('Unable to retrieve answer.')
        
    # else:
    #     query_object = getSearchObject(sub)
    #     query_property = getSearchProperty(obj)
    #     if query_object != '@' and query_property:
    #         data = fireQuery(query_object, query_property)
    # Reinitialize lists to empty lists.
    del obj[:]
    del sub[:]