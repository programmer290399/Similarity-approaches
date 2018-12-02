import json 
import re 
from progress.bar import IncrementalBar

crap = re.compile(r"[\(\[].*?[\)\]]")
def read_JSON(name):
       data =  list(json.loads(open(name).read()).keys())
       final =   list()
       bar = IncrementalBar('Loading data' , max=31356)
       for dish in data :
              final.append(re.sub( crap , '', dish).strip())
              bar.next()
       bar.finish()
       return final
def clean_JSON(name):
       data =  json.loads(open(name).read())
       final =   dict()
       bar = IncrementalBar('Loading data' , max=33302)
       for dish in data :
              final[re.sub( crap , '', dish).strip()] = data[dish]
              bar.next()
       bar.finish()
       return final
if __name__ == '__main__' :
       cleaned = clean_JSON('dish_freq.json')
       out_file = open('dish_freq_cleaned.json' , 'w+' , encoding='utf-8')
       json.dump(cleaned , out_file)
       out_file.close()