import os, csv, re, sys, json, shutil, traceback
from pairtree import *
import harvest

DATASTORE  = '/Users/eliotjordan/Documents/Temp/fix-ogm-metadata/data'
# DATASTORE2 = '/Users/eliotjordan/Documents/mint-arks/step2/data'

pairFactory = PairtreeStorageFactory()
store_arks = pairFactory.get_store(store_dir=DATASTORE, uri_base="ark:/88435/")
arks = store_arks.list_ids()

i = 0

for noid in arks:
	i += 1
	
	except_string = ''

	item = store_arks.get_object(noid)

	try:
		with item.get_bytestream('fgdc.xml',streamable=True) as fgdcDoc:
			fgdc_string = fgdcDoc.read()
			fgdc_tree = harvest.get_tree(fgdc_string)
			gbl_hash = harvest.get_gbl_hash(fgdc_tree, noid,'Restricted','Shapefile')
			gbl_string = harvest.build_schema(gbl_hash)
			# print gbl_string
	except Exception, err:
		except_string = except_string + '  WRITE ERROR  ' + noid + '  ' #+ str(err)
		# traceback.print_exc()

	try:
		item.del_file('geoblacklight.xml')
	except:
		except_string = except_string + '  ERROR  CAN\'T DELETE  '  + noid

	try:
		item.add_bytestream('geoblacklight.xml', gbl_string)
	except:
		except_string = except_string + '  ERROR  CAN\'T ADD  '  + noid

	if except_string != '':
		print str(i) + ',' + noid + ',' + except_string
	else:
		print str(i) + ',' + noid