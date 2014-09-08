import json
import datetime
import urllib
import os

try:
	import requests
except ImportError:
	print ('Python requests module required, get it from the cheese shop (https://pypi.python.org/pypi/requests/) or run:')
	print ('pip install requests')

try:
	import xlsxwriter
except ImportError:
	print ('Python xlsxwriter module required, get it from the cheese shop (https://pypi.python.org/pypi/XlsxWriter) or run:')
	print ('pip install xlsxwriter')

def get_settings(module):
	settings = json.loads(open('link_manager.json','r').read())
	return settings.get(module)

def pathfinder(path):
	if not os.path.exists(path):
		try:
			os.makedirs(path)
		except:
			raise

class BitlyAPI:
	def __init__(self, settings):
		self.settings = settings

	def api_get_json(self, url):
		r = requests.get(url)
		return json.loads(r.text)

	def get_link_batch(self, start_time, end_time):
		uri = self.settings['user_history']['uri']
		uri['access_token'] = self.settings['oauth_token']
		uri['created_after'] = start_time
		uri['created_before'] = end_time
		link_url = self.settings['base_url']\
				   +self.settings['user_history']['root']+'?'\
				   +urllib.urlencode(uri)	   
		res = self.api_get_json(link_url)
		if res.get('status_code') == 200:
			return res['data']['link_history']

	def get_links(self):
		report_start = int((datetime.date.today() - datetime.timedelta(days=((datetime.date.today().weekday() - 2) % 7) + 7)).strftime("%s")) 
		report_end = int(datetime.datetime.now().strftime('%s')) 
		self.linklist = []
		self.link_data = []
		res = [1,1]
		while len(res) > 1:
			res = self.get_link_batch(report_start, report_end)
			print 'Loaded %s links' % len(res)
			for link in res:
				if link['link'] not in self.linklist:
					self.link_data.append(link)
					self.linklist.append(link['link'])
				else:
					print ('Skipping %s as already in list' % link['link'])
			report_end = res[-1]['created_at']

	def get_link_metrics(self, link):
		uri = self.settings['link_metrics']['uri']
		uri['access_token'] = self.settings['oauth_token']
		uri['link'] = link
		link_url = self.settings['base_url']\
				   +self.settings['link_metrics']['root']+'?'\
				   +urllib.urlencode(uri)	   
		res = self.api_get_json(link_url)
		if res.get('status_code') == 200:
			return res['data']['link_clicks']

	def update_links_with_metrics(self):
		for link in self.link_data:
			print ('Updating click metrics for %s' % link['link'])
			link['link_clicks'] = self.get_link_metrics(link['link'])

class ReportWriter:
	def __init__(self, settings):
		self.settings = settings
		report_path = self.settings['output_path']
		pathfinder(report_path)
		self.report_name = os.path.join(os.getcwd(), report_path, self.settings['output_file'])
	def write_report(self, link_data):
		print ('Writing report...')
		workbook = xlsxwriter.Workbook(self.report_name)
		worksheet = workbook.add_worksheet('Bitly Click Data')
		keys = ['created_at', 'title', 'link_clicks', 'link', 'long_url']
		headings = ['Create Time', 'Title', 'Number of clicks', 'Short URL', 'Long URL']
		for index in range(0, len(headings)):
			worksheet.write(0, index, headings[index])
		row = 1
		for link in link_data:
			for index in range(0, len(keys)):
				worksheet.write(row, index, link[keys[index]])
			row+=1

def main():
	bt = BitlyAPI(get_settings('api'))
	bt.get_links()
	bt.update_links_with_metrics()
	rp = ReportWriter(get_settings('report'))
	rp.write_report(bt.link_data)

if __name__ == '__main__':
	main()