import re, math
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from nltk.corpus import wordnet as wn
import json
from progress.bar import IncrementalBar
import itertools
from read_data import read_JSON
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import multiprocessing
from multiprocessing import Process 
from multiprocessing import Queue
import psutil
from math import sqrt 
import decimal 
from decimal import Decimal
import os 
import platform
import time 
import glob


stop = stopwords.words('english')
WORD = re.compile(r'\w+')
stemmer = PorterStemmer()

class Similarity():


    def euclidean_distance(self,x,y):

        score = math.sqrt(sum((x.get(k, 0) - y.get(k, 0))**2 for k in set(x.keys()).union(set(y.keys()))))
        if score!= 0 : return 1/score
        else : return 1 

    def manhattan_distance(self,x,y):

        score = sum(abs(x.get(k, 0)-y.get(k, 0)) for k in set(x.keys()).union(set(y.keys())))
        if score!= 0 : return 1/score
        else : return 1 

    def minkowski_distance(self,x,y):

        score = self.nth_root(sum(pow(abs(x.get(k, 0)-y.get(k, 0)),3)for k in set(x.keys()).union(set(y.keys()))),2)
        if score!= 0 : return 1/score
        else : return 1 

    def nth_root(self,value, n_root):

        root_value = 1/float(n_root)
        return round (Decimal(value) ** Decimal(root_value),3)

    def square_rooted(self,x):

        return round(sqrt(sum([a*a for a in x])),3)

    def jaccard_similarity(self,x,y):
        
        s1 = set(x.keys())
        s2 = set(y.keys())
        return len(s1.intersection(s2)) / len(s1.union(s2))
    
    def text_to_vector(self,text):
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
    def get_mix_similarity(self,x,y):
        x = self.text_to_vector(x.strip().lower())
        y = self.text_to_vector(y.strip().lower())
        return float((decimal.Decimal(self.euclidean_distance(x,y)) + decimal.Decimal(self.manhattan_distance(x,y)) + decimal.Decimal(self.minkowski_distance(x,y)) + decimal.Decimal(self.jaccard_similarity(x,y)))/4)
    def get_cosine(self,vec1, vec2):

        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator


    def get_similarity(self,a, b):
        a = self.text_to_vector(a.strip().lower())
        b = self.text_to_vector(b.strip().lower())

        return self.get_cosine(a, b)


    def levenshtein(self,dish_A, dish_B):        
            
            a = 0.5 * fuzz.ratio(dish_A, dish_B)
            b = 1.5 * fuzz.partial_ratio(dish_A, dish_B)
            c = 1.5 * fuzz.token_sort_ratio(dish_A, dish_B)
            d = 0.5 * fuzz.token_set_ratio(dish_A, dish_B)
            score = (a + b + c + d)/400
            return score 


    def get_crit_list(self,dish_name , freq_dist):
        freq = int(freq_dist[dish_name])
        if freq >= 100 : crit_list = [0.9]
        elif freq < 100 and freq >= 50 : crit_list = [0.8]
        else : crit_list = [0.7]
        return crit_list

    def create_test_cases(self,test_cases, file_name , dishes , freq_dist):
        out_file = open(file_name , 'a+', encoding='utf-8')
        
        crit_data = dict()
        
        for dish in test_cases :
            
                crit_data[dish] = self.get_crit_list(dish,freq_dist)
            
        cases = list()
        
        for key,value in  crit_data.items():
            cases.append(list(itertools.product([key],value)))
        left_cases = []
        main = dict()
        
        for i in range(0,len(cases)) :
            
            for case in cases[i] :
                
                case_tag = str(case[0])+'-'+str(case[1])
                
                main[case_tag] = list()
                
                for dish  in dishes :
                    
                    score = (0.25 * self.get_similarity(case[0],dish)) + (0.25 * self.levenshtein(case[0],dish)) + (0.5 * self.get_mix_similarity(case[0],dish))
                    if  score > case[1] : 
                            if dish not in main[case_tag] and dish != case[0] : main[case_tag].append(dish) 
                
                if len(main[case_tag]) < 5 : 
                    main.pop(case_tag)
                    temp = case_tag.split('-')
                    new_case = list()
                    new_case.append(temp[0])
                    new_case.append(float(temp[1]) - 0.1)
                    left_cases.append(new_case)
        for case in left_cases :
            
            case_tag = str(case[0]) + '-' + str(case[1])
            
            main[case_tag] = list()
            
            for dish  in dishes :
                
                score = (0.25 * self.get_similarity(case[0],dish)) + (0.25 * self.levenshtein(case[0],dish)) + (0.5 * self.get_mix_similarity(case[0],dish))
                if  score > case[1] : 
                        if dish not in main[case_tag] and dish != case[0] : main[case_tag].append(dish) 
        print('Processed:',test_cases)
        json.dump(main,out_file)
        return
    def chunkIt(self ,seq, num):
        avg = len(seq) / float(num)
        out = []
        last = 0.0
        while last < len(seq):
            out.append(seq[int(last):int(last + avg)])
            last += avg
        return out
    
    def split_task(self , cpu_cores, dishes , freq_dist ,dishes_to_pass , slot_number) :
        chunks = self.chunkIt(dishes, cpu_cores)
        jobs = [] 
        file_names = []
        for i in range(0,len(chunks)): 
            file_name = 'data_temp' + str(i) + str(slot_number) +'.json'
            p = multiprocessing.Process(target= self.create_test_cases , args=(chunks[i],file_name,dishes_to_pass,freq_dist))
            jobs.append(p)
            file_names.append(file_name)
            p.start()
        for p in jobs: 
            p.join()
        return file_names 








if __name__=='__main__':
    start = time.time()
    try :
        cpu_count = int(multiprocessing.cpu_count()/2)
        print('{} CPU Cores detected'.format(cpu_count))
    except :
        cpu_count = 2
    
    dishes = read_JSON('./Resources/dish_freq_cleaned.json')
    
    
    similarity = Similarity()

    freq_dist = json.loads(open('./Resources/dish_freq_cleaned.json').read())

    start = int(input("Enter starting index (max= 33302 , min = 0) :"))
    end = int(input("Enter End (max= 33302 , min = 0) :"))
    dishes_to_process = dishes[start:end]

    out_file = open('Search_tags.json','a+',encoding='utf-8')
    slots = [dishes_to_process[i:i + 60 ] for i in range(0, len(dishes_to_process), 60 )]
    files = []
    for slot in slots :
        files += similarity.split_task( cpu_count , slot , freq_dist , dishes , slots.index(slot))
    print('\n Done!')
    print('Combining Files......')
    result = []
    for file_name in files :
        with open(file_name , "r") as infile:
            result.append(json.load(infile))
    with open("merged_file.json", "w+") as outfile:
        json.dump(result, outfile)
    print('Removing temp files ....')
    for file_name in files :
        os.remove(file_name)
    end = time.time()
    print('Task completed in:', end-start)
