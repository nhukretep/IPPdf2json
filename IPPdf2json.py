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

categories = {}

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
category = ''

# Set horizontal ranges for location of columns
range_min = [110, 250, 390, 540, 686]
range_max = [249, 389, 539, 685, 816]

isCategory = False
x = 0
price_index = 0

for entry in data:
    text = entry['text']
    if text == 'Veggie' or\
       text == 'Traditionelle Küche' or\
       text == 'Internationale Küche' or\
       text == 'Specials':
        category = text
        categories[category] = []

        for k in range(0,5): 
            categories[category].append({
                'meal': "",
                'price': None,
                'x': ""
                })

        price_index = 0
        isCategory = True
        x = entry['x']
        continue

    if x == 0:
        continue

    if '€' in text:
        
        categories[category][price_index]['price'] = text
        price_index += 1
        continue

    for i in range(0,5):

        if (range_min[i] < entry['x'] < range_max[i]):

            categories[category][i]['meal'] += " " + text
            categories[category][i]['x'] += " " + str(entry['x'])

    x = entry['x']

with open('menu.json', 'w') as outfile:
    json.dump(categories, outfile)

