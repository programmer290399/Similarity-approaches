import json 
import re 
from progress.bar import IncrementalBar

crap = re.compile(r"[\(\[].*?[\)\]]")
def read_JSON(name):
       data =  list(json.loads(open(name).read()).keys())
       final =   list()
       bar = IncrementalBar('Loading data' , max=33302)
       for dish in data :
              final.append(re.sub( crap , '', dish).strip())
              bar.next()
       bar.finish()
       return final

if __name__ == '__main__' :
       lst = read_JSON('dish_freq.json')
       print(len(lst))