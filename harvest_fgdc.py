import json, pairtree, collections, xmltodict
from lxml import etree as ET

INSTITUTION = 'Princeton'
UUID_PREFIX = 'http://arks.princeton.edu/ark:/88435/'
SLUG_PREFIX = 'princeton-'
BASE_URL = 'http://map.princeton.edu/items/'

def build_schema(gbl):

	root = ET.Element('add', attrib={"xmlns": "http://lucene.apache.org/solr/4/document"})
	doc = ET.SubElement(root, 'doc')

	for field in gbl:

		val = gbl[field]

		# is the value a string
		if isinstance(val, basestring):
			# add value to element
			ET.SubElement(doc, 'field', attrib={"name": field}).text = val
		else:
			# add mulitple elements to doc
			for item in val:
				ET.SubElement(doc, 'field', attrib={"name": field}).text = item
	
	return ET.tostring(root,  pretty_print=True, encoding='utf8', xml_declaration = True)

def get_gbl_hash(fgdc,noid,access,layer_format):
	gbl = collections.OrderedDict()

	refs = get_refs(fgdc,noid)
	bounds = fgdc['metadata']['idinfo']['spdom']['bounding']
	s = bounds['southbc']['#text']
	w = bounds['westbc']['#text']
	n = bounds['northbc']['#text']
	e = bounds['eastbc']['#text']

	gbl["uuid"] = UUID_PREFIX + noid
	gbl["dc_creator_sm"] = fgdc['metadata']['idinfo']['citation']['citeinfo']['origin']
	gbl["dc_description_s"] = fgdc['metadata']['idinfo']['descript']['abstract']
	gbl["dc_format_s"] = layer_format
	gbl["dc_identifier_s"] = noid
	gbl["dc_language_s"] = 'English'
	gbl["dc_publisher_s"] = fgdc['metadata']['idinfo']['citation']['citeinfo']['pubinfo']['publish']
	gbl["dc_rights_s"] = access
	gbl["dc_subject_sm"] = to_list(fgdc['metadata']['idinfo']['keywords']['theme']['themekey'])
	gbl["dc_title_s"] = fgdc['metadata']['idinfo']['citation']['citeinfo']['title']
	gbl["dc_type_s"] = 'Dataset'
	gbl["dct_references_s"] = json.dumps(refs)
	gbl["dct_spatial_sm"] = to_list(fgdc['metadata']['idinfo']['keywords']['place']['placekey'])
	gbl["dct_temporal_sm"] = to_list(fgdc['metadata']['idinfo']['keywords']['temporal']['tempkey'])
	gbl["dct:issued"] = fgdc['metadata']['idinfo']['citation']['citeinfo']['pubdate']
	gbl["dct_provenance_s"] = INSTITUTION
	gbl["georss_box_s"] = "{s} {w} {n} {e}".format(**vars())
	gbl["georss_polygon_s"] = "{n} {w} {n} {e} {s} {e} {s} {w} {n} {w}".format(**vars())
	gbl["layer_slug_s"] = SLUG_PREFIX + noid
	gbl["layer_id_s"] = noid
	gbl["layer_geom_type_s"] = get_geom_type(fgdc)
	gbl["solr_bbox"] = "{w} {s} {e} {n}".format(**vars())
	gbl["solr_ne_pt"] = "{n},{e}".format(**vars())
	gbl["solr_sw_pt"] = "{s},{w}".format(**vars())
	gbl["solr_geom"] = "ENVELOPE({w}, {e}, {n}, {s})".format(**vars())
	gbl["solr_year_i"] = to_list(fgdc['metadata']['idinfo']['keywords']['temporal']['tempkey'])[0]

	return gbl

def get_fgdc_dict(path):
	with open ("/Users/eliotjordan/Documents/Temp/fix-ogm-metadata/ogm_utils-python/fgdc.xml", "r") as fgdcDoc:
		return xmltodict.parse(fgdcDoc.read())

def get_geom_type(fgdc):
	geom = fgdc['metadata']['spdoinfo']['ptvctinf']['esriterm']['efeageom']['#text'] or ""
	if geom == 'Multipoint':
		return 'Point'
	elif geom == 'Polyline':
		return 'Polygon'
	elif geom == 'Point' or 'Line' or 'Polygon' or 'Raster' or 'Scanned Map' or 'Paper Map':
		return geom
	return 'Unknown'

def get_refs(fgdc,noid):
	itemPath = pairtree.id2path(noid).strip('/obj')

	refDict = {}
	refDict["http://schema.org/url"] = UUID_PREFIX + noid
	refDict["http://schema.org/thumbnailUrl"] = BASE_URL + itemPath + '/preview.jpg'
	refDict["http://schema.org/downloadUrl"] = BASE_URL + itemPath  + '/restricted/data.zip'
	refDict["http://www.opengis.net/cat/csw/csdgm"] = BASE_URL + itemPath  + '/fgdc.xml'

	return refDict

def to_list(s):
	if isinstance(s, basestring):
		return [s]
	else:
		return s

path = '/Users/eliotjordan/Documents/Temp/fix-ogm-metadata/ogm_utils-python/fgdc.xml'
el = get_fgdc_dict(path)
out = get_gbl_hash(el,'8910jw16d','Restricted','Shapefile')
print build_schema(out)
