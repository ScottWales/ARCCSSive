# This collects all other helper functions 
#!/usr/bin/env python
"""
Copyright 2016 ARC Centre of Excellence for Climate Systems Science

author: Paola Petrelli <paola.petrelli@utas.edu.au>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import print_function

import os
import itertools
from datetime import date
import glob
import subprocess
import argparse
from collections import defaultdict
from ARCCSSive.data import *
#from ARCCSSive.CMIP5.Model import VersionFile
from ARCCSSive.CMIP5.update_db_functions import * 

def parse_input_check():
    ''' Parse input arguments '''
    parser = argparse.ArgumentParser(description=r'''Checks all the CMIP5 ensembles
             (latest official version) on ESGF nodes, matching the constraints 
             passed as arguments and compare them to ones available on raijins.||
             All arguments, except the output file name,  can be repeated, for 
            example to select two variables:||
            -v tas tasmin||
            At least one experiment and one variable should be passed all other 
            arguments are optional.||
            The script returns all the ensembles satifying the constraints
            [var1 OR var2 OR ..] AND [model1 OR model2 OR ..] AND [exp1 OR exp2 OR ...]
            AND [mip1 OR mip2 OR ...]||
            Frequency adds all the correspondent mip_tables to the mip_table list.||
            If a constraint isn't specified for one of the fields automatically all values
            for that field will be selected.''')
    parser.add_argument('-e','--experiment', type=str, nargs="*", help='CMIP5 experiment', required=True)
    parser.add_argument('-m','--model', type=str, nargs="*", help='CMIP5 model', required=False)
    parser.add_argument('-v','--variable', type=str, nargs="*", help='CMIP5 variable', required=True)
    parser.add_argument('-t','--mip_table', type=str, nargs="*", help='CMIP5 MIP table', required=False)
    parser.add_argument('-f','--frequency', type=str, nargs="*", help='CMIP5 frequency', required=False)
    parser.add_argument('-en','--ensemble', type=str, nargs="*", help='CMIP5 ensemble', required=False)
    parser.add_argument('-ve','--version', type=str, nargs="*", help='CMIP5 version', required=False)
    parser.add_argument('-o','--output', type=str, nargs=1, help='database output file name', required=False)
    return vars(parser.parse_args())

def combine_constraints(**kwargs):
   ''' Return a set of dictionaries, one for each constraints combination '''
   return (dict(itertools.izip(kwargs, x)) for x in itertools.product(*kwargs.itervalues()))

def join_varmip(var0,mip0):
    ''' List all combinations of selected variables and mips '''
    comb = ["_".join(x) for x in itertools.product(*[var0,mip0])]
    print(comb)
    return comb

def compare_instances(db,remote,local):
    ''' Compare remote and local search results they're both a list of dictionaries
        :argument remote: each dict has keys version, files (objs), filenames, tracking_ids, dataset_id 
        :argument local: version, files (objs), filenames, tracking_ids, dataset_id
        :return: remote, local with updated dictionaries
    '''
    # loop through all returned remote datasets
    for ind,ds in enumerate(remote):
        # loop through all local versions
        ##P for i in range(len(local)):
        print( local)
        for v in local:
            print(type(v))
            v.checked_on = today
            # compare files for all cases except if version regular but different from remote 
            if v.version in [ds['version'],'NA',r've\d*']:
               extra = compare_files(db,ds,v)
               # if tracking_ids or checksums are same
               if extra==set([]):
                  v.to_update = False
               else:
                  v.to_update = True
            # if local dataset_id is the same as remote skip all other checks
            if v.dataset_id==ds['dataset_id']:
               print("skipping all other checks")
            # if version same as latest on esgf 
            elif v.version == ds['version']:
               v.dataset_id = ds['dataset_id']
               v.is_latest = True
               print('version same',extra,v.version)
            # if version undefined 
            elif v.version in ['NA',r've\d*']:
               if extra==set([]):
                  v.version = ds['version']
                  v.dataset_id = ds['dataset_id']
                  v.is_latest = True
               print('version NA or ve',v.version)
            # if version different or undefined but one or more tracking_ids are different
            # assume different version from latest
            # NB what would happen if we fix faulty files? tracking_ids will be same but md5 different, 
            # need to set a standard warning for them
            else:
               v.is_latest = False
               print('version different',v.version)
    # update local version on database
            print(type(v))
            db.commit()
            #update_item(db,Version,vid,kwargs)
    # add to remote dictionary list of local identical versions
        remote[ind]['same_as']=[v.id for v in local if v.is_latest] 
    return remote, local

def compare_files(db,rds,v):
    ''' Compare files of remote and local version of a dataset
        :argument rds: dictionary of remote dataset object selected attributes  
        :argument v:  local version object   
        :return: result set, NB updating VerisonFiles object in databse if calculating checksums 
    '''
    extra=set([])
    print('trackingids from ESGF',rds['tracking_ids'])
    print('trackingids local',v.tracking_ids())
    # first compare tracking_ids if all are present in local version
    local_ids=v.tracking_ids()
    if (local_ids and "" not in local_ids):
        extra = compare_tracking_ids(rds['tracking_ids'],local_ids)
    # if tracking_ids are the same or if they are not present compare checksums
    # calculate checksums and update local db if necessary  
    if extra==set([]):
       local_sums=[]
       if rds['checksum_type'] in ['md5','MD5']:
          for f in v.files:
             if f.md5 in ["", None]:
                 f.md5 = check_hash(v.path+"/"+f.filename,'md5')
                 update_item(db,VersionFile,f.id,{'md5':f.md5})
             local_sums.append(f.md5) 
       else:
          for f in v.files:
             if f.sha256 in ["",None]:
                 f.sha256=check_hash(v.path+"/"+f.filename,'sha256')
                 update_item(db,VersionFile,f.id,{'sha256':f.sha256})
             local_sums.append(f.sha256) 
       extra = compare_checksums(rds['checksums'],local_sums)
    return extra 
            
def compare_tracking_ids(remote_ids,local_ids):
    ''' Compare the lists of the tracking_ids from a remote and a local version of a dataset
        :argument remote_ids: list of remote tracking_ids  
        :argument local_ids: list of local tracking_ids  
        :return: result set 
    '''
    if remote_ids==set([]):
       return set(['no tracking ids found on ESGF'])
    return set(remote_ids).difference(local_ids)
    
def compare_checksums(remote_sums,local_sums):
    ''' Compare the lists of the checksums from a remote and a local version of a dataset
        :argument remote_sums: list of remote checksums  
        :argument local_sums: list of local checksums  
        :return: result set 
    '''
    return set(remote_sums).difference(local_sums)
    
# these functions are to manage drstree and tmp/tree directories

def list_drstree(**kwargs):
    ''' find directories matching kwargs constraints in drstree
        check if they are in database,
        if not add them to db
        return: list of matches '''
    if 'mip' in kwargs.keys(): kwargs['frequency']=frequency(kwargs['mip'])
    indir=drstree + drs_glob(**kwargs)
    return glob.glob(indir)

def list_tmpdir(flist):
    ''' this read from file list of instances on tmp/tree and return the ones matching constraints '''
# skip first line
# variable,mip_table,model,experiment,ensemble,realm,version,path
    keys=['variable','mip','model','experiment',
             'ensemble', 'realm', 'version', 'path']
    f=open(flist,'r')
    inst_list=[]
    lines=f.readlines()
    for line in lines[1:]:
        values=line[:-1].split(',')
        inst_list.append( {keys[i]:values[i] for i in range(len(keys))} )
    return inst_list

def file_glob(**kwargs):
        """ Get the glob string matching the CMIP5 filename
        """
        value=defaultdict(lambda: "*")
        value.update(kwargs)
        return '%s_%s_%s_%s_%s*.nc'%(
            value['variable'],
            value[ 'mip'],
            value['model'],
            value['experiment'],
            value['ensemble'])

def drs_glob(**kwargs):
    """ Get the glob string matching the directory structure under drstree
    """
    value=defaultdict(lambda: "*")
    value.update(kwargs)
    return '%s/%s/%s/%s/%s/%s'%(
        value['model'],
        value['experiment'],
        value['frequency'],
        value['realm'],
        value['variable'],
        value['ensemble'])

def tree_glob(**kwargs):
    """ Get the glob string matching the directory structure under tmp/tree
    """
    value=defaultdict(lambda: "*")
    value.update(kwargs)
    return '%s/%s/%s/%s/%s/%s'%(
        value['model'],
        value['experiment'],
        value['frequency'],
        value['realm'],
        value['variable'],
        value['ensemble'])

def drs_details(path):
    ''' Split the drstree path in model, experiment, frequency, realm, variable, ensemble '''
    keys=['model','experiment', 'frequency', 'realm', 'variable','ensemble']
    values=path.replace(drstree,"").split('/')
    dummy=dict((keys[i],values[i]) for i in range(len(values)))
    return dummy.pop('frequency'), dummy

def file_details(fname):
    ''' Split the filename in variable, MIP code, model, experiment, ensemble (period is excluded) '''
    keys=['variable','mip','model','experiment','ensemble']
    values = fname.split('_')
    if len(values) >= 5:
      return dict((keys[i],values[i]) for i  in range(len(values[:-1])))
    else:
      return 

def find_version(bits,string):
    ''' Returns matching string if found in directory structure '''
    dummy = filter(lambda el: re.findall( string, el), bits)
    if len(dummy) == 0:
        return 'not_specified'
    else:
        return dummy[0]

def list_drs_versions(path):
    ''' Returns matching string if found in directory structure '''
    return [x.split("/")[-1] for x in glob.glob(path+"/v*")]

def list_drs_files(path):
    ''' Returns matching string if found in directory structure '''
    return [x.split("/")[-1] for x in glob.glob(path+"/*.nc")]
 
def get_mip(path):
    ''' Returns mip for instance 
        input: instance path
    '''
    onefile = os.path.basename(glob.glob(path + "/latest/*.nc")[0]) 
    dummy = file_details(onefile)
    return dummy['mip']

def tree_path(drspath):
    ''' Returns the tmp/tree path for a particular instance &  version from 
        input: drstree path for one the version files
    '''
    path=os.path.realpath(drspath)
    return "/".join(path.split("/")[:-1])

def check_hash(path,hash_type):
    ''' Execute md5sum/sha256sum on file on tree and return True,f same as in wget file '''
    hash_cmd="md5sum"
    if hash_type in ["SHA256","sha256"]: hash_cmd="sha256sum"
    try:
      return subprocess.check_output([hash_cmd, path]).split()[0]
    except:
      print("Warning cannot calculate ",hash_type," for file ",path)
      return ""

# functions to manage dictionaries
def assign_mips(*args):
    ''' Append the cmip5 mip tables corresponding to the input frequency and/or realm
        return updates list of mips '''
    if not mips: mips=[]
    if frq:
       mips.extend(frq_dict[frq]) 
    if realm:
       mips.extend(realm_dict[realm]) 
    return mips

def frequency(mip):
    ''' returns frequency for input mip '''
    return  mip_dict[mip]
     
# this should be taken by setting environment variable DRSTREE
# define root cirectory for drstree and /tmp/tree
try:
  drstree = os.environ['DRSTREE']
except KeyError:
  drstree = "/g/data1/ua6/drstree/CMIP5/GCM/"
drstree="/g/data1/ua8/cmip-download/drstree/CMIP5/GCM/"
tmptree="/g/data1/ua6/unofficial-ESG-replica/tmp/tree/"

# define date string for current date
today = date.today().strftime('%d/%m/%Y')

