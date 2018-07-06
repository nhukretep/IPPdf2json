from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from io import StringIO
import pdfminer
import csv
import json
import requests
import datetime

### Extract text from pdf ###
 
# Get PDF file.

# today = datetime.date.today()
# year = today.year
# month = today.month
# CW = today.isocalendar()[1] # week of the year
# weekday = today.weekday()
# monday = today - datetime.timedelta(days=weekday)
# friday = today - datetime.timedelta(days=weekday - 5)

# mon = monday.strftime('%d.%m')
# fri = friday.strftime('%d.%m.%y')

# url = 'http://konradhof-catering.de/wp-content/uploads/' + year + '/' + month + '/KW-' + CW + '_' + mon + '-' + fri + '.pdf'

# response = requests.get(url)

# with open('IPP_menu.pdf', 'wb') as f:
#     f.write(response.content)

fp = open('IPP_menu.pdf', 'rb')

parser = PDFParser(fp)

document = PDFDocument(parser)

if not document.is_extractable:
    raise PDFTextExtractionNotAllowed

rsrcmgr = PDFResourceManager()

device = PDFDevice(rsrcmgr)

# BEGIN LAYOUT ANALYSIS
laparams = LAParams()

device = PDFPageAggregator(rsrcmgr, laparams=laparams)

interpreter = PDFPageInterpreter(rsrcmgr, device)

menu = {}

def parse_obj(lt_objs):
    result = []
    for obj in lt_objs:

        if isinstance(obj, pdfminer.layout.LTTextBoxHorizontal):
            text = obj.get_text().replace('\n', ' ').strip()
            if text:
                result.append({
                    "x":obj.bbox[0],
                    "y":obj.bbox[1],
                    "text":text
                })

        elif isinstance(obj, pdfminer.layout.LTFigure):
            parse_obj(obj._objs)
    return result

# read the page into a layout object
interpreter.process_page(next(PDFPage.create_pages(document)))
layout = device.get_result()

# extract text from this object
data = parse_obj(layout._objs)


### Sort text into json ###

# Set horizontal ranges for location of columns
lon_min = [110, 250, 390, 538, 686]
lon_max = [249, 389, 537, 685, 816]

# Set vertical ranges for location of rows
lat_min = [230, 165, 85, 20]
lat_max = [310, 229, 164, 84]

categories = ['Veggie','Traditionelle Küche','Internationale Küche','Specials']

for category in categories:
    menu[category] = []

    for k in range(0,5): 
        menu[category].append({
            'meal': "",
            'price': None,
            'x': "",
            'y': ""
            })

for entry in data:
    category = ""
    weekday = None
    text = entry['text']
    lon = entry['x']
    lat = entry['y']
    
    for i in range(0,4):

        if (lat_min[i] < lat < lat_max[i]):

            category = categories[i]

    for i in range(0,5):

        if (lon_min[i] < entry['x'] < lon_max[i]):
            
            weekday = i

    if text == '0':
        continue

    if (category != "" and weekday != None and '€' in text):
        menu[category][weekday]['price'] = text
        continue

    if (category != "" and weekday != None):
        menu[category][weekday]['meal'] += " " + text
        menu[category][weekday]['x'] += " " + str(lon)
        menu[category][weekday]['y'] += " " + str(lat)

with open('menu.json', 'w') as outfile:
    json.dump(menu, outfile)

