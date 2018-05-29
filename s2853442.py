import sys
import requests
import spacy
import re

from collections import OrderedDict
from spacy import *

MAX_DIGITS = 10

def _keyify(x):
    try:
        xi = int(x[0])
    except ValueError:
        return 'S{0}'.format(x)
    else:
        return 'I{0:0{1}}'.format(xi, MAX_DIGITS)


def searchNum(params):
	# cut determinants in the beginning of the string
	params['search'] = re.sub(r'^the ', '', params['search'])
	params['search'] = re.sub(r'^an ', '', params['search'])
	params['search'] = re.sub(r'^a ', '', params['search'])
	params['search'] = re.sub(r'^Which ', '', params['search'])
	params['search'] = re.sub(r'^What ', '', params['search'])
	params['search'] = re.sub(r'^When ', '', params['search'])
	params['search'] = re.sub(r'^Where ', '', params['search'])
	params['search'] = re.sub(r'^How ', '', params['search'])
	params['search'] = re.sub(r'^Who ', '', params['search'])
	#search API
	url = 'https://www.wikidata.org/w/api.php'
	json = requests.get(url,params).json()
	if json['search']:
		return format(json['search'][0]['id'])
	else:
		return 

#gets id of all noun chunks from c based on parameters		
def get_id(c, params):
	nlp = spacy.load('en_core_web_sm')
	doc = nlp(c)
	res = []
	for token in doc.noun_chunks:
		chunk = nlp(token.text)
		lem = ''
		for t in chunk:
			# I want to lemmatize only verbs and nouns 
			# since, for example, superlative forms of adjectives have to stay the same
			if t.pos_ == 'VERB' or t.pos_ == 'NOUN':
				lem += t.lemma_
			else:
				lem += t.text	
			lem += ' '
		params['search'] = lem
		if token.root.dep_== 'dobj' or token.root.dep_ == 'pobj' or token.root.dep_ == 'nsubj':
			res.append(searchNum(params))
	return list(filter(None.__ne__, res))

		
#extract entity and property from the question and searches for the corresponding Q and P		
def extract(c):	 
	params = {'action':'wbsearchentities',
			  'language':'en',
			  'format':'json'} 
			  
	#first, extract all posible entities
	wd = get_id(c, params)
	
	#then, extract all posible properties	
	params['type'] = 'property'
	wdt = get_id(c, params)
	

	
	#if anwer could not be found because there has been no entity/property found
	if len(wd) == 0 or len(wdt) == 0:
		print("You might have made a spelling mistake... Try again!")
		return
	
	#combine all possible entities and properties and search for the answer
	for i in wd:
		for j in wdt:
			query = '''SELECT ?itemLabel
					WHERE
					{
						wd:''' + i + ''' wdt:''' + j + ''' ?item .
					  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,zh"}
					}'''
			if get_answer(query):
				return
		
	print("No answer was found :(")
			

#takes query as an argument and prints the answer(s) if any was found	
def get_answer(query):
	url = 'https://query.wikidata.org/sparql'
	dat = requests.get(url,params={'query': query, 'format': 'json'}).json()
	if dat['results']['bindings']:
		for item in dat['results']['bindings']:
			for var in item :
				print("Answer: ", item[var]['value'])
		return True
	return False


#questions has been changed to follow the assignment requirements			
data = {
	'1': "What is the capital of Papua New Guinea?",
	'2': "What is the anthem of Friesland?",
	'3': "What is the capital of Azerbaijan? ",
	'4': "What is the population of Spain?",
	'5': "What is the highest point of Russia?",
	'6': "Rome has how large of an area?",
	'7': "What is the length of the Elbe?",
	'8': "List the official languages of Belgium.",
	'9': "What is the official language of Colombia?",
	'10':"Which official languages does Colombia have?"
}

for key, value in sorted(data.items(), key =_keyify):
	print(key, value)
	print()

while 1:
	extract(sys.stdin.readline())
	
	
