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
        
def drop_the_an(sentence):
    new_sentence = ""
    for i in range(0, len(sentence)):
        if sentence[i] != "an":
            pass
        else:
            new_sentence[i] = sentence[i]
    return new_sentence
		


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
		'ingredients':'has part',
		'members':'has part'
}

print_example_queries()

for w in sys.stdin:
    obj = []
    sub = []
    url = 'https://www.wikidata.org/w/api.php'
    params['type'] = 'item'
    wordList = re.sub("[^\w]", " ",  w).split()
    stopWords = ['an']
    for word in wordList:
			  if word in stopWords:
					  wordList.remove(word)
    # Format question using a dictionary to accomodate for the way
    # data is stored in wikiData. For now, only president is converted
    # to head of state, as the latter retrieves what the user actually wants.
    for x in range(0, len(wordList)):
        if wordList[x] in input_parser:
            wordList[x] = input_parser.get(wordList[x])
    stri = " ".join(wordList)
    w = stri
    parse = nlp(w.strip())
    word_list = w.split()
    first = word_list[0]
    last = word_list[len(word_list)-1]
    of_counter = 0
    current_counter = 0
    for i in range(0, len(word_list)):
        if word_list[i] == "of" or word_list[i] == "of?":
            of_counter +=1;
    if (last == "of?"):
        last = "of"
    for token in parse:
        if token.dep_ == "nsubj" or token.dep_ == "attr" or token.dep_ == "dobj" or token.dep_ == "appos":
            sub = []
            for d in token.subtree:
                if d.text == "of":
                    current_counter = current_counter + 1
                if d.pos_ != "ADP":
                    sub.append(d.text)
                else:
                    if (d.text == last or current_counter != of_counter):
                        sub.append(d.text)
                    else:
                        break
            if sub[0] == 'the':
                del sub[0]
        if token.dep_ == "pobj":
            obj = []
            for d in token.subtree:
                obj.append(d.text)
            if obj[0] == 'the':
                del obj[0]
    if not obj:
        for token in parse:
            if token.pos_ == "PROPN":
                obj = []
                for d in token.subtree:
                    obj.append(d.text)
    ok = 1
    search_property = " ".join(sub)
    search_object = " ".join(obj)
    print(search_property)
    print(search_object)
    params['search'] = search_object
    json = requests.get(url,params).json()
    for result in json['search']:
        if ok == 1:
            ok = 0
            query_object = result['id']
    ok = 1
    params['search'] = search_property
    params['type'] = 'property';
    json = requests.get(url,params).json()
    for result in json['search']:
        if ok == 1:
            ok = 0
            query_property = result['id']
    query='''
        SELECT ?valueLabel WHERE {
        wd:''' + query_object + ''' wdt:''' + query_property + ''' ?value
        SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .
        }
        }
        '''
    url = 'https://query.wikidata.org/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    if data['results']['bindings'] == []:
			  
        print('Unable to retrieve answer.')
    else:
      for item in data['results']['bindings']:
        for var in item:
            sys.stdout.write("The " + search_property + " of " + search_object + " is ")
            sys.stdout.write('{}'.format(item[var]['value']))
            if search_property in dictionary_units:
                sys.stdout.write(' ' + dictionary_units.get(search_property) + '.\n')
            else:
                sys.stdout.write('.\n')
    search_property = ''
    search_object = ''
    del obj[:]
    del sub[:]
