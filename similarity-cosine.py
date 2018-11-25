import re, math
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem.porter import *
from nltk.corpus import wordnet as wn
import json
from progress.bar import IncrementalBar
import itertools
from read_data import read_JSON


dishes = read_JSON('zomato_menu.json')

out_file = open('similarity_index_new.json' , 'w+' , encoding='utf-8')





stop = stopwords.words('english')

WORD = re.compile(r'\w+')
stemmer = PorterStemmer()

def get_cosine(vec1, vec2):
    # print vec1, vec2
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def text_to_vector(text):
    words = WORD.findall(text)
    a = []
    for i in words:
        for ss in wn.synsets(i):
            a.extend(ss.lemma_names())
    for i in words:
        if i not in a:
            a.append(i)
    a = set(a)
    w = [stemmer.stem(i) for i in a if i not in stop]
    return Counter(w)

def get_similarity(a, b):
    a = text_to_vector(a.strip().lower())
    b = text_to_vector(b.strip().lower())

    return get_cosine(a, b)

def get_char_wise_similarity(a, b):
    a = text_to_vector(a.strip().lower())
    b = text_to_vector(b.strip().lower())
    s = []

    for i in a:
        for j in b:
            s.append(get_similarity(str(i), str(j)))
    try:
        return sum(s)/float(len(s))
    except: # len(s) == 0
        return 0
main = dict()
query = input('Enter your query :')
print('\n Generating index in memory , please wait .....')
bar = IncrementalBar('Loading', max= 93655)
for dish in dishes :
    if  not main.get(dish,False) :
        if dish == query:
            main[dish] = list()
            bar.next()
bar.finish()
criteria = float(input("\n Enter similarity cut-off score (0< cut-off < 1) :"))
bar = IncrementalBar('Processing', max= pow(93655,2))
count = 0  
# for match  in itertools.product(dishes, dishes) :
#     if get_similarity(match[0],match[1]) > criteria : 
#             main[match[0]].append(match[1])
#     if count % 10000 == 0 : 
#         out_file.seek(0)                        
#         out_file.truncate()
#         json.dump(main,out_file)
#         out_file.write('\n')
#     count += 1
#     bar.next()
for dish  in dishes :
    if get_char_wise_similarity(query,dish) > criteria : 
            if dish not in main[query] : main[query].append(dish)
    if count % 10000 == 0 : 
        out_file = open('similarity_index_new1.json' , 'w+' , encoding='utf-8')
        out_file.seek(0)                        
        out_file.truncate()
        json.dump(main,out_file)
        out_file.write('\n')
        out_file.close()
    count += 1
    bar.next()


print('\n Writing to file for the last time .....')
json.dump(main,out_file)
out_file.close()
print('Done!')



