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
from multiprocessing import pool 
import psutil
from math import*
import decimal 
from decimal import Decimal
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
        if freq >= 100 : crit_list = [0.8,0.9]
        elif freq < 100 and freq >= 50 : crit_list = [0.7,0.8]
        else : crit_list = [0.6,0.7]
        return crit_list

    def create_test_cases(self,*argv):
        test_cases = list()
        for arg in argv : test_cases.append(arg)
        dishes = read_JSON('dish_freq.json')
        crit_data = dict()
        freq_dist = json.loads(open('dish_freq.json').read())
        for dish in test_cases :
            crit_data[dish] = self.get_crit_list(dish,freq_dist)
        cases = list()

        
        for key,value in  crit_data.items():
            cases.append(list(itertools.product([key],value)))
        
        
        main = dict()
        for i in range(0,len(cases)) :
            for case in cases[i] :
                
                case_tag = str(case[0])+'-'+str(case[1])
                print('\n working on =>', case_tag)
                main[case_tag] = list()
                bar = IncrementalBar('Processing', max = 33302)
                for dish  in dishes :
                    
                    score = (0.25 * self.get_similarity(case[0],dish)) + (0.25 * self.levenshtein(case[0],dish)) + (0.5 * self.get_mix_similarity(case[0],dish))
                    if  score > case[1] : 
                            if dish not in main[case_tag] : main[case_tag].append(dish) 
                    bar.next()
                bar.finish()

        return main






if __name__=='__main__':
    try :
        cpu_count = multiprocessing.cpu_count()
    except :
        cpu_count = 4 
    dishes = read_JSON('dish_freq.json')

    similarity = Similarity()

    freq_dist = json.loads(open('dish_freq.json').read())

    num_of_dishes = int(input("Enter number of dishes to process :"))

    dishes_to_process = dishes[:num_of_dishes]

    out_file = open('main.json','a+',encoding='utf-8')

    with multiprocessing.Pool(processes= cpu_count * 4) as pool:
        parent = psutil.Process()
        parent.nice(psutil.REALTIME_PRIORITY_CLASS)
        for child in parent.children():
            child.nice(psutil.REALTIME_PRIORITY_CLASS)
        results = pool.starmap( similarity.create_test_cases , [dishes_to_process] ) 
        for result in results :
            print(result)
            json.dump(result,out_file)
    print('\n Done!')

