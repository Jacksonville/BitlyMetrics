BitlyMetrics
===========

###Introduction:
This is a quick process I wrote to download metrics for Bitly links over the last week and create an excel spreadsheet with the click metric data.
The [OAuth token](https://bitly.com/a/oauth_apps) is utilised for authentication, you can get this code from the bitly site.

###Requirements:
The following python modules are required:
- [requests](http://docs.python-requests.org/en/latest/)
- [xlsxwriter](https://xlsxwriter.readthedocs.org)

###Notes:
When downloading historical links only 50 are returned by default and a max of 100 per request. These are sorted in reverse chronological order (Newest to Oldest) so links are retrieved in batches using the date modified values.
The from date is currently defaulted to the previous Wednesday + 7, this is configurable via the commandline parameter `--report_start`.

###TODO:
- Add additional report output types (json, html, csv)
