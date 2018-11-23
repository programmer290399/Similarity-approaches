import json 
from progress.bar import IncrementalBar



def read_JSON(name):

       bar = IncrementalBar('Loading Data:', max = 93655 )

       json_data=open(name).read()

       data = json.loads(json_data)

       mappings  = data['foo']

       dishes = list()

       for element in mappings :
              dish_list = element["dish_mappings"]
              for dish in dish_list :
                     dishes.append(dish["dish_name"])
                     bar.next()
       bar.finish()
       return dishes 




if __name__ == '__main__' :
   lst = read_JSON('zomato_menu.json')
   for e in lst :
       print(e)
       