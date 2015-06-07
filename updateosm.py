import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
from optparse import OptionParser

OSMFILE = "mumbai_india.osm"
# OSMFILE = "example_audit.osm"

#street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_type_re = re.compile(r'^\b\S+\.?', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Park", "Sector"]

mapping = { 
             "Ave":"Avenue",
             "St.": "Street",
             "Rd." : "Road",
             "N.":"North",
             "St" : "Street",
             "St." : "Street",
             "no" : "No",
             "Rd." : "Road",
             "Rd" : "Road",
             "ROAD" : "Road",
             "ROad" : "Road",
             "marg" : "Road",
             "road" : "Road",
             "stn" : "Station",
             "Marg" : "Road",
             "lane" : "Lane",
             "sector" : "Sector"

             }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            #return True if need to be updated
            return True
    return False


def is_street_name(elem):
    """
    Perhaps the addr:full should also included to be fixed  
    """
    return (elem.attrib['k'] == "street")

def is_name_is_street(elem):
    """Some people fill the name of the street in k=name.
    
    Should change this"""
    s = street_type_re.search(elem.attrib['v'])
    #print s
    return (elem.attrib['k'] == "name") and s and s.group() in mapping.keys()

def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)

    tree = ET.parse(osm_file)
    
    listtree = list(tree.iter())
    for elem in listtree:
        if elem.tag == "node" or elem.tag == "way":
            n_add = None
            
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    if audit_street_type(street_types, tag.attrib['v']):
                        #Update the tag attribtue
                        tag.attrib['v'] = update_name(tag.attrib['v'],mapping)
                elif is_name_is_street(tag):
                    tag.attrib['v'] = update_name(tag.attrib['v'],mapping)
                    n_add = tag.attrib['v']
                   
            if n_add:
                elem.append(ET.Element('tag',{'k':'addr:street', 'v':n_add}))

            
                
    #write the to the file we've been audit
    tree.write(osmfile[:osmfile.find('.osm')]+'_audit.osm')
    return street_types


def update_name(name, mapping):
    """
    Fixed abreviate name so the name can be uniform.
    
    The reason why mapping in such particular order, is to prevent the shorter keys get first.
    """
    dict_map = sorted(mapping.keys(), key=len, reverse=True)
    for key in dict_map:
        
        if name.find(key) != -1:          
            name = name.replace(key,mapping[key])
            return name


    return name


def test():
    st_types = audit(OSMFILE)
    pprint.pprint(dict(st_types))
    #
    

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping)
            print name, "=>", better_name


if __name__ == '__main__':
    test()

