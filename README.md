BtlyMetrics
===========

###Introduction:
This is a quick process I wrote to download metrics for Bitly links over the last week and create an excel spreadsheet with the click metric data.
The [OAuth token](http://dev.bitly.com/authentication.html) is utilised for authentication, you can get this code from the bitly site.

###Requirements:
The following python modules are required:
- [requests](http://docs.python-requests.org/en/latest/)
- [xlsxwriter](https://xlsxwriter.readthedocs.org)
