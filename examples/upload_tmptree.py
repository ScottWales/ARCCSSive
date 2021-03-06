# a tentative script to upload all existing drstree "versions" into CMIP sqlite database
# each variable, mip, experiment, model, ensemble combination add a new instance in "instance"
# for each instance there should be at least one version in "version" table 
# for each version add at least one file in table "files" 

from __future__ import print_function

#import argparse
from ARCCSSive.CMIP5.update_db_functions import insert_unique, add_bulk_items 
from ARCCSSive.CMIP5.other_functions import *
#NB tmptree root dir is also defined there
from ARCCSSive.CMIP5 import DB 
from ARCCSSive.CMIP5.Model import Instance, Version, VersionFile 


# open local database using ARCSSive interface
conn = DB.connect()
db = conn.session
flist = "/home/581/pxp581/allcmip5data.csv"

#loop through entire drstree or a subdir by using constraints **kwargs
# variable,mip_table,model,experiment,ensemble,realm,version,path

instances=list_tmpdir(flist)
#print(instances)
#for each instance individuated add instance row
for kw_instance in instances:
# return dictionary
    # could create an Instance, Version and file object instead and pass that on?
    kw_version={}
    kw_files={}
    kw_version['version'] = kw_instance.pop('version')
    kw_version['path'] = kw_instance.pop('path')
    print(kw_version['path'])
    #frequency = mip_dict(kw_instance['mip'])
# make sure details list isn't empty
    inst_obj,new = insert_unique(db, Instance, **kw_instance)
    kw_version['instance_id'] = inst_obj.id
    files = list_drs_files(kw_version['path']) 
    #print(kw_version.items())
    v_obj,new = insert_unique(db, Version, **kw_version)
    if v_obj.filenames()==[]: 
        rows=[]
        for f in files:
            checksum=check_hash(v_obj.path+"/"+f,'sha256')
            rows.append(dict(filename=f, sha256=checksum, version_id=v_obj.id))
        add_bulk_items(db, VersionFile, rows)
    else:
        kw_files['version_id']=v_obj.id
        for f in files:
            kw_files['filename']=f
            kw_files['sha256']=check_hash(v_obj.path+"/"+f,'sha256')
            insert_unique(db, VersionFile, **kw_files)
       
