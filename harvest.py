import json, pairtree, collections, datetime
from lxml import etree as ET

INSTITUTION = 'Princeton'
UUID_PREFIX = 'http://arks.princeton.edu/ark:/88435/'
SLUG_PREFIX = 'princeton-'
BASE_URL = 'http://map.princeton.edu/items/'

def build_schema(gbl):

	root = ET.Element('add', attrib={"xmlns": "http://lucene.apache.org/solr/4/document"})
	doc = ET.SubElement(root, 'doc')

	required_fields = ['uuid','dc_identifier_s','dc_title_s','dc_rights_s','dct_provenance_s','dct_references_s','georss_box_s','layer_id_s','layer_geom_type_s','layer_modified_dt','layer_slug_s','solr_bbox'] 

	for field in gbl:

		val = gbl[field]

		# Check if required values are empty
		if field in required_fields:
			if val == "":
				print 'Missing Required Field: ' + str(field)
				raise Exception
				return

		# Remove any values that are empty strings
		if val == "":
			del gbl[field]
			continue

		# is the value a string
		if isinstance(val, basestring):
			# add value to element
			ET.SubElement(doc, 'field', attrib={"name": field}).text = val
		else:
			# add mulitple elements to doc
			for item in val:
				ET.SubElement(doc, 'field', attrib={"name": field}).text = item
	
	return ET.tostring(root,  pretty_print=True, encoding='utf8', xml_declaration = True)

def get_gbl_hash(fgdc_tree,noid,access,layer_format):
	gbl = collections.OrderedDict()

	refs = get_refs(noid)

	bounds = get_bounds(fgdc_tree)
	w = bounds['w']
	s = bounds['s']
	e = bounds['e']
	n = bounds['n']

	gbl["uuid"] = UUID_PREFIX + noid
	gbl["dc_creator_sm"] = get_element_val(fgdc_tree,'idinfo/citation/citeinfo/origin')
	gbl["dc_description_s"] = get_element_val(fgdc_tree,'idinfo/descript/abstract')
	gbl["dc_format_s"] = layer_format
	gbl["dc_identifier_s"] = noid
	gbl["dc_language_s"] = 'English'
	gbl["dc_publisher_s"] = get_element_val(fgdc_tree,'idinfo/citation/citeinfo/pubinfo/publish')
	gbl["dc_rights_s"] = access
	gbl["dc_subject_sm"] = get_element_multival(fgdc_tree,'idinfo/keywords/theme/themekey')
	gbl["dc_title_s"] = get_element_val(fgdc_tree,'idinfo/citation/citeinfo/title')
	gbl["dc_type_s"] = 'Dataset'
	gbl["dct_references_s"] = json.dumps(refs)
	gbl["dct_spatial_sm"] = get_element_multival(fgdc_tree,'idinfo/keywords/place/placekey')
	gbl["dct_temporal_sm"] = get_element_multival(fgdc_tree,'idinfo/keywords/temporal/tempkey')
	gbl["dct:issued"] = get_element_val(fgdc_tree,'idinfo/citation/citeinfo/pubdate')
	gbl["dct_provenance_s"] = INSTITUTION
	gbl["georss_box_s"] = "{s} {w} {n} {e}".format(**vars())
	gbl["georss_polygon_s"] = "{n} {w} {n} {e} {s} {e} {s} {w} {n} {w}".format(**vars())
	gbl["layer_slug_s"] = SLUG_PREFIX + noid
	gbl["layer_id_s"] = noid
	gbl["layer_modified_dt"] = get_date()
	gbl["layer_geom_type_s"] = get_geom_type(fgdc_tree)
	gbl["solr_bbox"] = "{w} {s} {e} {n}".format(**vars())
	gbl["solr_ne_pt"] = "{n},{e}".format(**vars())
	gbl["solr_sw_pt"] = "{s},{w}".format(**vars())
	gbl["solr_geom"] = "ENVELOPE({w}, {e}, {n}, {s})".format(**vars())
	gbl["solr_year_i"] = get_element_val(fgdc_tree,'idinfo/keywords/temporal/tempkey')

	return gbl

def get_element_val(fgdc_tree,branch_string):
	# default is empty string
	val = ""
	
	try:
		fgdc_val = fgdc_tree.find(branch_string).text
		
		# if no errors set val to fgdc val
		val = fgdc_val
	finally:
		return val

def get_element_multival(fgdc_tree,branch_string):
	# default is empty string
	val_list = []
	
	try:
		fgdc_elements = fgdc_tree.findall(branch_string)
		fgdc_val_list = []

		for element in fgdc_elements:
			fgdc_val_list.append(element.text)

		# if no errors set val to fgdc_val_list
		val_list = fgdc_val_list
	finally:
		return val_list

def get_bounds(fgdc_tree):
	# default bounding box (New Jersey)
	bounds = {'w': -75.55911, 's': 38.92822, 'e': -73.90233, 'n': 41.35744}

	try:
		base_tree =  'idinfo/spdom/bounding/'

		# get bbox values from metadata
		fgdc_bounds = {}
		fgdc_bounds['w'] = fgdc_tree.find(base_tree + 'westbc').text
		fgdc_bounds['s'] = fgdc_tree.find(base_tree + 'southbc').text
		fgdc_bounds['e'] = fgdc_tree.find(base_tree + 'eastbc').text
		fgdc_bounds['n'] = fgdc_tree.find(base_tree + 'northbc').text

		# if no errors set bounds to new values
		bounds = fgdc_bounds
	finally:
		return bounds

def get_tree(fgdc_string):
	return ET.fromstring(fgdc_string)

def get_geom_type(fgdc_tree):
	geom = 'Unknown'

	try:
		fgdc_geom = fgdc_tree.find('spdoinfo/ptvctinf/esriterm/efeageom').text

		if fgdc_geom == 'Multipoint':
			fgdc_geom = 'Point'
		elif fgdc_geom == 'Polyline':
			fgdc_geom = 'Polygon'
		elif fgdc_geom == 'Point' or 'Line' or 'Polygon' or 'Raster' or 'Scanned Map' or 'Paper Map':
			fgdc_geom = fgdc_geom
		else:
			fgdc_geom = 'Unknown'

		geom = fgdc_geom
	finally:
		return geom

def get_refs(noid):
	itemPath = pairtree.id2path(noid).strip('/obj')

	refDict = {}
	refDict["http://schema.org/url"] = UUID_PREFIX + noid
	refDict["http://schema.org/thumbnailUrl"] = BASE_URL + noid + '/preview.jpg'
	refDict["http://schema.org/downloadUrl"] = BASE_URL + noid  + '/restricted/data.zip'
	refDict["http://www.opengis.net/cat/csw/csdgm"] = BASE_URL + noid  + '/fgdc.xml'

	return refDict

def to_list(s):
	if isinstance(s, basestring):
		return [s]
	else:
		return s

def get_date():
	now = datetime.datetime.now()
	return now.replace(microsecond=0).isoformat() + 'Z'


# with open ("/Users/eliotjordan/Documents/Temp/fix-ogm-metadata/ogm_utils-python/fgdc.xml", "r") as fgdcDoc:
# 	tree = get_tree(fgdcDoc.read())
# 	gbl_hash = get_gbl_hash(tree,'8910jw16d','Restricted','Shapefile')
# 	print build_schema(gbl_hash)

	# bnds = get_bounds(fgdcDoc.read())
	# print bnds['w']