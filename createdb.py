#!/usr/bin/env python2

import os,sys
import re,tempfile
import sqlite3
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
    ip = re.findall('('+IR+')',matches[0][0])
    srcInfo=[ip[0],'']
    dstInfo=[ip[1],'']
    for mat in matches:
        if mat[0] == matches[0][0]:
            srcInfo[1] = srcInfo[1] + mat[1]
        else:
            dstInfo[1] = dstInfo[1] + mat[1]
    cur.execute('''SELECT SRCNUM FROM SRCHOST WHERE SRCIP = ?''',[srcInfo[0]]);
    srcNum=cur.fetchone()
    if srcNum is None:
        cur.execute('''INSERT INTO SRCHOST(SRCIP) VALUES(?)''',[srcInfo[0]]);
        cur.execute('''SELECT SRCNUM FROM SRCHOST WHERE SRCIP = ?''',[srcInfo[0]]);
        srcNum=cur.fetchone()
    cur.execute('''SELECT DSTNUM FROM DSTHOST WHERE DSTIP = ?''',[dstInfo[0]]);
    dstNum=cur.fetchone()
    if dstNum is None:
        cur.execute('''INSERT INTO DSTHOST(DSTIP) VALUES(?)''',[dstInfo[0]]);
        cur.execute('''SELECT DSTNUM FROM DSTHOST WHERE DSTIP = ?''',[dstInfo[0]]);
        dstNum=cur.fetchone()
    cur.execute('''INSERT INTO STREAM VALUES(NULL,?,?,NULL,?,?)''',[srcNum[0],dstNum[0],sqlite3.Binary(srcInfo[1]),sqlite3.Binary(dstInfo[1])]);

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

conn = sqlite3.connect('data.db');
cur = conn.cursor()

#print tmpdir  # // print the raw ordered TCP data :D 

for connfile in os.listdir(tmpdir):
    addToDB(os.path.join(tmpdir,connfile))
conn.commit()
