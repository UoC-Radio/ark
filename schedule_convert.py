import os
import json
import xml
import xml.etree.ElementTree as ET


tree = ET.parse('.test/schedule.xml')
root = tree.getroot()

days = {
    'Mon': ('Monday', 'Δευτέρα'),
    'Tue': ('Tuesday', 'Τρίτη'),
    'Wed': ('Wednesday', 'Τετάρτη'),
    'Thu': ('Thursday', 'Πέμπτη'),
    'Fri': ('Friday', 'Παρασκευή'),
    'Sat': ('Saturday', 'Σάββατο'),
    'Sun': ('Sunday', 'Κυριακη'),
}

doc = {'days': {}, 'schedule': {}}

for i, child in enumerate(root):
    doc['days'][str(i+1)] = (*days[child.tag], child.tag)
    doc['schedule'][str(i + 1)] = []
    for e in child:
        doc['schedule'][str(i + 1)].append({'from_time': e.attrib['Start'], 'name': e.attrib['Name']})

json.dump(doc, open('schedule_rastapank.json', 'w'))