#!/usr/bin/env python2

import os,sys
import re,tempfile
import gzip
from StringIO import StringIO
import magic
import dpkt
import sqlite3
import IP
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
    toIns = dict()
    matches=re.findall(contentRegex,content,re.DOTALL)
    host = dict((['src',dict()],['dst',dict()]))
    [host['src']['IP'],host['dst']['IP']] = re.findall('('+IR+')',matches[0][0])
    host['src']['data'] = ''
    host['dst']['data'] = ''
    for mat in matches:
        if mat[0] == matches[0][0]:
            host['src']['data'] = host['src']['data'] + mat[1]
        else:
            host['dst']['data'] = host['dst']['data'] + mat[1]
    for hostType in ['src','dst']:
        t = hostType.upper()
        cur.execute('SELECT '+t+'NUM FROM '+t+'HOST WHERE '+t+'IP = ?',[host[hostType]['IP']]);
        try:
            toIns[t+'NUM']=cur.fetchone()[0]
        except TypeError:
            if(hostType=='src'):
                cur.execute('INSERT INTO '+t+'HOST('+t+'IP) VALUES(?)',[host[hostType]['IP']]);
            else if(hostType=='dst'):
                dstHostInfo = dict()
                dstHostInfo['DSTIP'] = host[hostType]['IP']
                location = IP.find(host[hostType]['IP']).split('\t')
                for i in range(len(location)):
                    dstHostInfo['DSTIPLOC'+str(i)]=location[i]
                dstHostCol = ','.join(dstHostInfo.keys())
                dstHostHolder = ','.join('?' * len(dstHostInfo))
                insSql = 'INSERT INTO DSTHOST ({}) VALUES({})'''.format(dstHostCol, dstHostHolder)
                cur.execute(insSql, dstHostInfo.values())
            toIns[t+'NUM']=cur.lastrowid
        try:
            if(hostType=='src'):
                http = dpkt.http.Request(host[hostType]['data'])
                toIns['SRCDESCRIPTION'] = http.method+' http://'+http.headers['host']+http.uri
            if(hostType=='dst'):
                http = dpkt.http.Response(host[hostType]['data'])
                toIns['DSTdESCRIPTION'] = 'HTTP/'+' '.join([http.version,http.status,http.reason])
                if "content-encoding" in http.headers and http.headers["content-encoding"] == "gzip":
                    buf = StringIO(http.body)
                    f = gzip.GzipFile(fileobj=buf)
                    http.body = f.read()
                toIns['FILETYPE'] = mag.buffer(http.body)
            for attr in http.headers:
                if attr not in headerAttr[hostType]:
                    cur.execute('''INSERT INTO '''+t+'''HEADER (COLUMNATTR) VALUES(?)''',[attr])
                    colNum = cur.lastrowid
                    headerAttr[hostType][attr]=colNum
                    cur.execute('''ALTER TABLE STREAM ADD '''+t+'''HEADER'''+str(colNum)+''' TEXT''') 
                toIns[t+'HEADER'+str(headerAttr[hostType][attr])]=''.join(http.headers[attr])
            toIns[t+'BODY']=sqlite3.Binary(http.body)
        except dpkt.dpkt.UnpackError:
            toIns[hostType+'Data'] = sqlite3.Binary(host[hostType]['data'])

    columns = ','.join(toIns.keys())
    placeholders = ','.join('?' * len(toIns))
    insSql = 'INSERT INTO STREAM ({}) VALUES({})'''.format(columns, placeholders)
    try:
        cur.execute(insSql, toIns.values())
    except:
        import pdb
        pdb.set_trace()

tmpdir = tempfile.mkdtemp()
mag = magic.open(magic.MAGIC_NONE)
mag.load()

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

conn = sqlite3.connect('data.db')
conn.row_factory = sqlite3.Row
conn.text_factory = str
cur = conn.cursor()

headerAttr=dict()
for hostType in ['src','dst']:
    t = hostType.upper()
    sqlResult=cur.execute('SELECT * FROM '+t+'HEADER').fetchall()
    headerAttr[hostType] = dict()
    for attrRow in sqlResult:
        headerAttr[hostType][attrRow[1]] = attrRow[0]

for connfile in os.listdir(tmpdir):
    addToDB(os.path.join(tmpdir,connfile))
conn.commit()
