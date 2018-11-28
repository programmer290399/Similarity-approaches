import json 

def read_JSON(name):
       return list(json.loads(open(name).read()).keys())


if __name__ == '__main__' :
       lst = read_JSON('dish_freq.json')
       print(len(lst))