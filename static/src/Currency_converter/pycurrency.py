import requests
import json

#import config


#UNIVERSAL VARIABLES
URL = f"https://v6.exchangerate-api.com/v6/0bad105e04f4e53dfc232b13/latest/USD"


class Currency_Converter:
	"""convert any convercy"""

	def __init__(self):
		self.data = requests.get(URL).json()
		
		#assign need info to varible
		self.base_curruncy = self.data['base_code']
		self.currencies = self.data['conversion_rates']


	def convert(self, from_currency, to_currency, amount): 		
		"""returns amout of needed currency"""

		#convert from currency to base currency.
		#base currency is USD
		convert2_base = amount / self.currencies[from_currency]
		
		conversion_rate = self.currencies[to_currency]
	  
		# return only 2 decimal places 
		amount_figure = round(convert2_base * self.currencies[to_currency], 2)
		amount_figure = f"{to_currency} {amount_figure}"
		
		return 	{
			"from_currency" : from_currency,
			"to_currency" : to_currency,  
			"input_amount" : amount,
			"result" : amount_figure,
			"conversion_rate" : conversion_rate,
		}
		
		 


#For testing
if __name__ == "__main__":
	converter = Currency_Converter()
	print(converter.convert('USD','GHS',0.2))
