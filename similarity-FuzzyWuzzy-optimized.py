from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from read_data import read_JSON
import json
from progress.bar import IncrementalBar




total = 93655
dishes = read_JSON('zomato_menu.json')
bar = IncrementalBar('Processing', max=total)
out_file = open('similarity_index.json' , 'w+' , encoding='utf-8')


processedDishes = []
matchers = []

for dish in dishes:
    if dish:
        processedDish = fuzz._process_and_sort(dish, True, True)
        processedDishes.append({"processed": processedDish, "dish": dish})


processedDishes.sort(key= lambda x: len(x["processed"]))

for idx, dish in enumerate(processedDishes):
    length = len(dish["processed"])
    matcher = fuzz.SequenceMatcher(None, dish["processed"])
    for idx2 in range(idx + 1, len(processedDishes)):
        dish2 = processedDishes[idx2]
        if 2 * length / (length + len(dish2["processed"])) < 0.85: # upper bound
            break

        matcher.set_seq2(dish2["processed"])

        if matcher.quick_ratio() >= 0.85 and matcher.ratio() >= 0.85: # should also try without quick_ratio() check
            print(dish["dish"], dish2["dish"])