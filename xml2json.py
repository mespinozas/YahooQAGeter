'''A module for converting xml into json.'''

import json

from lxml import etree

def xml_to_json(etree_xml):
	dictionary = etree_to_dict(etree_xml, True)
	return json.dumps(dictionary, sort_keys=True, indent=4)

def etree_to_dict(tree, only_child):
	mydict = dict([(item[0], item[1]) for item in tree.items()])
	children = tree.getchildren()
	if children:
		if len(children) > 1:
			if(tree.text is not None):
				mydict['text'] = tree.text
			mydict['text'] = tree.text
			mydict['children'] = [etree_to_dict(child, False) for child in children]
		else:
			if(tree.text is not None):
				mydict['text'] = tree.text
			child = children[0]
			mydict[child.tag] = etree_to_dict(child, True)
	else:
		if(tree.text is not None):
			mydict['text'] = tree.text
	if only_child:
		return mydict
	else:
		return {tree.tag: mydict}
