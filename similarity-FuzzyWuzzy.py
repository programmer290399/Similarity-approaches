from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from read_data import read_JSON
import json
from progress.bar import IncrementalBar

total = 93655
dishes = read_JSON('zomato_menu.json')
bar = IncrementalBar('Processing', max=total)
out_file = open('similarity_index.json' , 'w+' , encoding='utf-8')


main = {'data' : []}
for dish_A in dishes :
    index = dict()
    index[dish_A] = list()    
    for dish_B in dishes :
        a = fuzz.ratio(dish_A, dish_B)
        b = fuzz.partial_ratio(dish_A, dish_B)
        c = fuzz.token_sort_ratio(dish_A, dish_B)
        d = fuzz.token_set_ratio(dish_A, dish_B)
        score = (a + b + c + d)/4
        if score > 50 : index[dish_A].append(dish_B)
    main['data'].append(index)
    bar.next()            




json.dump(main, out_file)
    
    



out_file.close()
bar.finish()
print('done !!')



