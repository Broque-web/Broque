import scrapy
from scrapy.crawler import CrawlerProcess as cp
from helpers import save_as_json as sj



class Predict_Match_spider(scrapy.Spider):
	name = "matches_spider"


	def __init__(self, **kwargs):
			super().__init__(**kwargs)
			self.output_callback = kwargs.get('args').get('callback')


	def start_requests(self):
		#download the page
		#and send it to self.parse

		yield scrapy.Request(url="https://forebet.com/en/football-tips-and-predictions-for-today",
			callback = self.parse)


	def parse(self,response):
		"""Scrape matches predictions"""

		

		#details section seperated to 
		#avoid most of the code crashing
		section1_matches = response.xpath('///div[@class="rcnt tr_0"]')
		section2_matches = response.xpath('//div[@class="rcnt tr_1"]')

		self.results = []


		#find all parent_class tags in `
		#which the prediction x found
		for y in section1_matches:
			#need to seperate parent tag from child
			teams = y.xpath('div[@class="tnms"]')
			prob = y.xpath('div[@class="fprc"]')

			#the source code changes a moment
			#the match start, so 1 declaration 
			#wont work, first assigin child paths
			#to each varible and return the other
			#varibale if first variable returns null
			correct = y.xpath('div[@class="avg_sc tabonly"]/text()').get()
			correct1 = y.xpath('div[@class="avg_sc exact_yes tabonly"]/text()').get()

			team_win1 = y.xpath('div[@class="predict"]/span/span/text()').get()
			team_win2 = y.xpath('div[@class="predict_no"]/span/span/text()').get()



			#i know the dictionary code looks messy
			#but assigning to variable and refering 
			#that variable inside the dictionary wont work
			dict = {
			"home": teams.xpath('div/a/span[@class="homeTeam"]/span/text()').get(),
			"away": teams.xpath('div/a/span[@class="awayTeam"]/span/text()').get(),
			"date_time" : teams.xpath('div/a/time/span/text()').get(),
			"probability_percentage" : {"1x": prob.xpath('span[1]/text()').get(),
			"X" : prob.xpath('span[2]/text()').get(),
			"2x" : prob.xpath('span[3]/text()').get(),
			},
			"winner" : team_win2 if not team_win1 else team_win1,
			"avg.goals" : correct1 if not correct else correct,
			"correct_score" : y.xpath('div[@class="ex_sc tabonly"]/text()').get(),
			"odds" : y.xpath('div[@class="bigOnly prmod"]/span/text()').get(),
			}

			self.results.append(dict)

		for x in section2_matches:
			#need to seperate parent tag from child
			teams = x.xpath('div[@class="tnms"]')
			prob = x.xpath('div[@class="fprc"]')

			#the source code changes a moment
			#the match start, so 1 declaration 
			#wont work, first assigin child paths
			#to each varible and return the other
			#varibale if first variable returns null
			correct = x.xpath('div[@class="avg_sc tabonly"]/text()').get()
			correct1 = x.xpath('div[@class="avg_sc exact_yes tabonly"]/text()').get()

			team_win1 = x.xpath('div[@class="predict"]/span/span/text()').get()
			team_win2 = x.xpath('div[@class="predict_no"]/span/span/text()').get()



			#i know the dictionary code looks messy
			#but assigning to variable and refering 
			#that variable inside the dictionary wont work
			dict = {
			"home": teams.xpath('div/a/span[@class="homeTeam"]/span/text()').get(),
			"away": teams.xpath('div/a/span[@class="awayTeam"]/span/text()').get(),
			"date_time" : teams.xpath('div/a/time/span/text()').get(),
			"probability_percentage" : {"1x": prob.xpath('span[1]/text()').get(),
			"X" : prob.xpath('span[2]/text()').get(),
			"2x" : prob.xpath('span[3]/text()').get(),
			},
			"winner" : team_win2 if not team_win1 else team_win1,
			"avg.goals" : correct1 if not correct else correct,
			"correct_score" : x.xpath('div[@class="ex_sc tabonly"]/text()').get(),
			"odds" : x.xpath('div[@class="bigOnly prmod"]/span/text()').get(),
			}

			self.results.append(dict)


		return self.results

	def close(self, spider):
		#Tell class to return only
		#the result of the output 
		  self.output_callback(self.results)





#This class return only the output of the code
#scrapy does not allow you to get only the output 
#but i found a way to return only the output without any trouble

class Bet_Scraper:

	def __init__(self): 
		self.output = None

		#Dont display uneeded log messages
		self.process = cp(settings={'LOG_ENABLED': False})

	def yield_output(self, data):
		#set var as callback to none
		#so class can use var to hold
		#self.results
		self.output = data 

	def crawl(self):
		"""set callback and clean code properly for scrapy"""

		self.process.crawl(Predict_Match_spider, args={
						   'callback': self.yield_output})
		self.process.start()

	def output_results(self):
		"""return only the results"""
		crawler = Bet_Scraper()
		crawler.crawl()
		return crawler.output



