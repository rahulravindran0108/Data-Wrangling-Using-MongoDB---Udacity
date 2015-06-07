import xml.etree.ElementTree as ET
import pprint
import re
import codecs
import json
from pymongo import MongoClient

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
addresschars = re.compile(r'addr:(\w+)')
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
OSM_FILE = 'mumbai_india_audit.osm'

def shape_element(element):
    #node = defaultdict(set)
    node = {}
    if element.tag == "node" or element.tag == "way" :
        #create the dictionary based on exaclty the value in element attribute.
        node = {'created':{}, 'type':element.tag}
        for k in element.attrib:
            try:
                v = element.attrib[k]
            except KeyError:
                continue
            if k == 'lat' or k == 'lon':
                continue
            if k in CREATED:
                node['created'][k] = v
            else:
                node[k] = v
        try:
            node['pos']=[float(element.attrib['lat']),float(element.attrib['lon'])]
        except KeyError:
            pass
        
        if 'address' not in node.keys():
            node['address'] = {}
        #Iterate the content of the tag
        for stag in element.iter('tag'):
            #Init the dictionry

            k = stag.attrib['k']
            v = stag.attrib['v']
            #Checking if indeed prefix with 'addr' and no ':' afterwards
            if k.startswith('addr:'):
                if len(k.split(':')) == 2:
                    content = addresschars.search(k)
                    if content:
                        node['address'][content.group(1)] = v
            else:
                node[k]=v
        if not node['address']:
            node.pop('address',None)
        #Special case when the tag == way,  scrap all the nd key
        if element.tag == "way":
            node['node_refs'] = []
            for nd in element.iter('nd'):
                node['node_refs'].append(nd.attrib['ref'])
#         if  'address' in node.keys():
#             pprint.pprint(node['address'])
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    """
    Process the osm file to json file to be prepared for input file to monggo
    """
    file_out = "mumbai_audit.json"
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def test():

    data = process_map(OSM_FILE)
    client  = MongoClient('mongodb://localhost:27017')
    db = client.examples
    [db.mumbai.insert(e) for e in data]


if __name__ == "__main__":
    test()