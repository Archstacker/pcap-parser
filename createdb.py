#!/usr/bin/env python2

import os,sys
import re,tempfile
sys.path.append("./jamaal-re-tools/tsron")
from libtsron import Tsron 

header = "__libtsron_packet__"

IR = r'[0-9]{1,3}(?:\.[0-9]{1,3}){3}'
PR = r'[0-9]{1,5}'
SR = IR+'_'+PR+'_'+IR+'_'+PR
contentRegex = r'(?=<--__=('+SR+r')=__-->'+header+'(.*?)(?=<--__=('+SR+r')=__-->'+header+'|\Z))'
def addToDB(filepath):
    f=open(filepath)
    content=f.read()
    matches=re.findall(contentRegex,content,re.DOTALL)
    srcInfo=[matches[0][0],'']
    dstInfo=[matches[1][0],'']
    for mat in matches:
        if mat[0]==srcInfo[0]:
            srcInfo[1] = srcInfo[1] + mat[1]
        else:
            dstInfo[1] = dstInfo[1] + mat[1]

tmpdir = tempfile.mkdtemp()

# // targs 
targs = {
'typestream': 'TCP',     # // TCP, UDP or GRE 
'header': header,            # // delimit each packet with a user defined header  
'srcpcap': "test.pcap", 	 # // File name of pcap 
'streamnum': 0,          # // 0 stream means all streams
'display': False,        # // Display stream stats 
'outdir': tmpdir,          # // output directory to write streams, if not, return streams to variable 
'connheader': True      # // Include connection flow information as apart of the header 
}

streamObj=Tsron(**targs) # // create instance of Tsron 
x = streamObj.TCP()      # // return TCP stream from PCAP to var x 

print tmpdir  # // print the raw ordered TCP data :D 

for connfile in os.listdir(tmpdir):
    addToDB(os.path.join(tmpdir,connfile))
