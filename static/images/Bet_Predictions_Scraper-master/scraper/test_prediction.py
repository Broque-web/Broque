from prediction_scraper import Bet_Scraper
from helpers import save_as_json as sj


#This is how you should import and use the class
x = Bet_Scraper().output_results()
print(len(x))

#This saves the results
#into a json
sj(x,"results")