import json
import datetime
import urllib
import os
import argparse
from time import sleep

from Queue import Queue
from threading import Thread

try:
    import requests
except ImportError:
    print ('Python requests module required, get it from the cheese shop (https://pypi.python.org/pypi/requests/) or run:')
    print ('pip install requests')
    raise

try:
    import xlsxwriter
except ImportError:
    print ('Python xlsxwriter module required, get it from the cheese shop (https://pypi.python.org/pypi/XlsxWriter) or run:')
    print ('pip install xlsxwriter')
    raise

xstr = lambda s: s or ""

def get_settings(module):
    settings = json.loads(open(os.path.join(os.path.dirname(__file__), 'link_manager.json'), 'r').read())
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
        self.links = []
        self.done = False
        self.num_threads = 35

    def api_get_json(self, url):
        r = requests.get(url)
        return json.loads(r.text)

    def get_link_batch(self, start_time, end_time):
        uri = self.settings['user_history']['uri']
        uri['access_token'] = self.settings['oauth_token']
        uri['created_after'] = start_time
        uri['created_before'] = end_time
        link_url = self.settings['base_url']\
                   + self.settings['user_history']['root'] + '?'\
                   + urllib.urlencode(uri)
        res = self.api_get_json(link_url)
        if res.get('status_code') == 200:
            return res['data']['link_history']

    def get_links(self, report_start):
        report_end = int(datetime.datetime.now().strftime('%s'))
        self.linklist = []
        self.link_data = []
        res = [1, 1]
        while len(res) > 1:
            res = self.get_link_batch(report_start, report_end)
            print (('Loaded %s links' % len(res)))
            if len(res)>0:
                for link in res:
                    if link['link'] not in self.linklist:
                        self.link_data.append(link)
                        self.linklist.append(link['link'])
                    else:
                        print (('Skipping %s as already in list' % link['link']))
                report_end = res[-1]['created_at']
            else:
                print (('No links returned in this batch'))

    def get_link_metrics(self, queue, thread_id):
        while queue.qsize() > 0:
            link = queue.get()
            print (('Thread-{0} Updating click metrics for {1}'.format(thread_id,link['link'])))
            uri = self.settings['link_metrics']['uri']
            uri['access_token'] = self.settings['oauth_token']
            uri['link'] = link['link']
            link_url = self.settings['base_url']\
                       + self.settings['link_metrics']['root'] + '?'\
                       + urllib.urlencode(uri)
            res = self.api_get_json(link_url)
            if res.get('status_code') == 200:
                link['link_clicks'] = res['data']['link_clicks']
                self.links.append(link)
            
    def update_links_with_metrics(self):
        q = Queue()
        for link in self.link_data:
            q.put(link)
            q.task_done()
        for i in range(self.num_threads):
            x = Thread(target=self.get_link_metrics, args=(q, i,))
            x.setDaemon(True)
            x.start()
        queue_length = len(self.link_data)
        q.join()
        while q.qsize() > 0:
            sleep(1)

class ReportWriter:
    def __init__(self, settings):
        self.settings = settings
        report_path = self.settings['output_path']
        pathfinder(report_path)
        self.report_name = os.path.join(os.path.split(os.path.abspath(__file__))[0], report_path, self.settings['output_file'] % (datetime.datetime.now().strftime("%Y-%m-%d")))

    def write_report(self, link_data):
        print ('Writing report...')
        workbook = xlsxwriter.Workbook(self.report_name)
        worksheet = workbook.add_worksheet('Bitly Click Data')
        keys = ['created_at', 'title', 'link_clicks', 'link', 'long_url']
        headings = ['Create Time', 'Title', 'Number of clicks', 'Short URL', 'Long URL']
        boldfmt = workbook.add_format({'bold': True})
        datefmt = workbook.add_format({'num_format': 'yyyy/mm/dd hh:mm'})
        numfmt = workbook.add_format({'num_format': '# ##0'})
        colwidths = {}
        for index in range(0, len(headings)):
            worksheet.write(0, index, headings[index], boldfmt)
            colwidths[keys[index]] = [len(headings[index])]
        row = 1
        for link in link_data:
            worksheet.write_string(row, 0, datetime.datetime.fromtimestamp(link[keys[0]]).strftime('%Y-%m-%d %H:%M:%S'), datefmt)
            worksheet.write_string(row, 1, xstr(link[keys[1]]))
            worksheet.write_number(row, 2, link[keys[2]], numfmt)
            worksheet.write_url(row, 3, link[keys[3]])
            worksheet.write_url(row, 4, link[keys[4]])
            for index in range(0, len(keys)):
                if index == 0:
                    colwidths[keys[index]].append(len(datetime.datetime.fromtimestamp(link[keys[0]]).strftime('%Y-%m-%d %H:%M:%S')))
                else:
                    colwidths[keys[index]].append(len(unicode(link[keys[index]])))
            row += 1
        print (("%s rows written" % len(link_data)))
        col = 0
        for key in keys:
            print (("Resizing column %s width to %s" % (key, max(colwidths[key]))))
            worksheet.set_column(col, col, max(colwidths[key]))
            col += 1
        print ('Freezing top row')
        worksheet.freeze_panes(1, 0)
        if 'tab_colour' in self.settings:
            print ('Setting tab colour')
            worksheet.set_tab_color(self.settings['tab_colour'])


def main(report_start):
    bt = BitlyAPI(get_settings('api'))
    bt.get_links(report_start)
    bt.update_links_with_metrics()
    rp = ReportWriter(get_settings('report'))
    rp.write_report(bt.links)
    return rp.report_name

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get stats on bitly links')
    parser.add_argument('--report_start',
                        dest='report_start',
                        default=(datetime.date.today() - datetime.timedelta(days=((datetime.date.today().weekday() - 2) % 7) + 7)),
                        help='Start date for the report - yyyy-mm-dd')
    args = parser.parse_args()
    if type(args.report_start) == str:
        report_start = int(datetime.datetime.strptime(args.report_start, '%Y-%m-%d').strftime("%s"))
    else:
        report_start = int(args.report_start.strftime("%s"))
    main(report_start)
