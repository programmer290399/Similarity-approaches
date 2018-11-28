import re, math
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem.porter import *
from nltk.corpus import wordnet as wn
import json
from progress.bar import IncrementalBar
import itertools
from read_data import read_JSON
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import multiprocessing
import threading 

stop = stopwords.words('english')
WORD = re.compile(r'\w+')
stemmer = PorterStemmer()


def create_chunks(bulk_data, cpu_count , num_of_dishes ) :
    total_data_length = len(bulk_data)
    len_of_chunks = int(total_data_length/(cpu_count))
    
    chunks = list()
    for i in range(0, total_data_length , len_of_chunks):
        chunks.append(bulk_data[i:i + len_of_chunks])
    return chunks

def get_file_names(n) :
    names = list()
    for i in range(0,n) :
        names.append('similarity_index_temp_file-' + str(i) + '.json')
    return names


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
def levenshtein(dish_A, dish_B):        
        a = 0.5 * fuzz.ratio(dish_A, dish_B)
        b = 1.5 * fuzz.partial_ratio(dish_A, dish_B)
        c = 1.5 * fuzz.token_sort_ratio(dish_A, dish_B)
        d = 0.5 * fuzz.token_set_ratio(dish_A, dish_B)
        score = (a + b + c + d)/400
        return score 


def get_crit_list(dish_name , freq_dist):
    freq = int(freq_dist[dish_name])
    if freq >= 100 : crit_list = [0.8,0.9]
    elif freq < 100 and freq >= 50 : crit_list = [0.7,0.8]
    else : crit_list = [0.6,0.7]
    return crit_list

def create_test_cases(test_cases, f_name , dishes ):
    crit_data = dict()
    freq_dist = json.loads(open('dish_freq.json').read())
    for dish in test_cases :
        crit_data[dish] = get_crit_list(dish,freq_dist)
    cases = list()

    
    for key,value in  crit_data.items():
        cases.append(list(itertools.product([key],value)))
    
    
    
    for i in range(0,len(cases)) :
        for case in cases[i] :
            out_file = open(f_name , 'a+' , encoding='utf-8')
            out_file.write('\n')
            out_file.write('------------'+str(case[0])+':'+str(case[1])+'------------')
            out_file.write('\n')
            out_file.close()
            main = dict()
            print('\n working on =>', str(case[0])+':'+str(case[1]))
            for dish in dishes :
                if  not main.get(dish,False) :
                    if dish == case[0]:
                        main[dish] = list()
            

            for dish  in dishes :
                score = (0.5 * get_similarity(case[0],dish)) + (0.5 * levenshtein(case[0],dish))
                if  score > case[1] : 
                        if dish not in main[case[0]] : main[case[0]].append(dish) 
                

            out_file = open(f_name , 'a+' , encoding='utf-8')
            out_file.write('\n')
            json.dump(main,out_file)
            out_file.write('\n')
            out_file.close()    
        
        

if __name__=='__main__':
    try :
        cpu_count = multiprocessing.cpu_count()
    except :
        cpu_count = 4 
    dishes = read_JSON('dish_freq.json')

    freq_dist = json.loads(open('dish_freq.json').read())

    num_of_dishes = int(input("Enter number of dishes to process :"))

    dishes_to_process = dishes[:num_of_dishes]
    
    chunks = create_chunks(dishes_to_process,cpu_count,num_of_dishes)

    filenames = get_file_names(len(chunks))
    processes = list()
    for i in range(0,len(chunks)):
        processes.append(multiprocessing.Process(target=create_test_cases , args=(chunks[i] , filenames[i] , dishes )))
    for i in range(0,(len(processes)- cpu_count + 1) , cpu_count):
        rng = list(range(0,cpu_count))
        for j in rng :
            processes[j].start()
        for j in rng :
            processes[j].join()
    main_file = open('main.json', 'a+' , encoding='utf-8')
    for file_name in filenames :
        main_file.write('\n')
        data = json.loads(open(file_name).read())
        json.dump(data , main_file)
    main_file.close()





    print('\n Done!')

