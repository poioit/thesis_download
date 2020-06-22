from articledownloader.articledownloader import ArticleDownloader
from scidownl.scihub import *
from io import StringIO
import re
from simple_rest_client.api import API
from PdfConverter import PdfConverter
import xml.etree.ElementTree as ET

restclient = API(
    api_root_url='https://botadmin.luxurai.com/',
    #api_root_url='http://localhost:3030',
    params={},
    headers={},
    timeout=2,
    append_slash=False,
    json_encode_body=True,
)
def parsexml(myfile):
    try:
        tree = ET.parse(myfile)
        root = tree.getroot()
        for child in root:
            print(child.tag, child.attrib)
    except Exception as e:
        print(str(e))

def findNode(root, spaces, target):
    for child in root:
        '''
        print(child)
        if child.tag.find('article') != -1:
            print(child)
        '''
        ret = child.findall( target, spaces)
        if ret:
            return ret
        else:
            findNode(child, spaces, target)

def findText(cur_filename):
    tree = ET.parse(cur_filename)
    root = tree.getroot()
    my_namespaces = dict([
        node for _, node in ET.iterparse(
            cur_filename, events=['start-ns']
            )
            ])
    from pprint import pprint
    #pprint(my_namespaces)
    rawtext = ''
    
    for child in root:
        for neighbor in root.iter(child.tag):
            if neighbor.tag.find('originalText') != -1 :
                rawtexts = findNode(neighbor, my_namespaces, 'xocs:rawtext')
                if rawtexts != None:
                    return rawtexts[0].text
                else:
                    for child in root.iter():
                        #print(child.tag)
                        ret = child.find( 'ja:body', my_namespaces)
                        if ret != None:
                            for c in ret.findall('.//ce:sections/ce:section', my_namespaces):
                                for sec in c.iter():
                                    if sec.tag.find('section-title') != -1:
                                        #print(sec.text)
                                        rawtext += sec.text+'\n'
                                    if sec.tag.find('para') != -1:
                                        #print(sec.text)
                                        rawtext += sec.text+'\n'
                    #print(rawtext)
                    return rawtext


restclient.add_resource(resource_name='thesis')
#text = findText('./elsevier/A quick method for the simultaneous determination of ascorbic acid and sorbic acid in fruit juices by capillary zone el.xml')
#sys.exit(0)
try:
    downloader = ArticleDownloader(els_api_key='e88e30b8118b3ed42ca752c0d6b59686')
    #https://api.elsevier.com/content/search/sciencedirect?query=nutrition&APIKey=e88e30b8118b3ed42ca752c0d6b59686
    #dois = downloader.get_dois_from_journal_issn('1476-4686', rows=500, pub_after=2000)
    filetype = 'xml'
    #78 is for elsevier
    records = downloader.get_dict_from_search('ascorbic acid+extraction+fruit&filter=member:78',200)
    for i, record in enumerate(records):
        print(i)
        cur_title = re.sub('[\[\]\'\.\/]', '', str(record['title']))
        replaced = re.sub('[\[\]\'\.\/]', '', str(record['doi']))
        print(replaced)
        cur_filename = './elsevier/'+replaced+'.'+filetype
        try:
            my_file = open(cur_filename, 'wb')  # Need to use 'wb' on Windows
        except Exception as e:
            print(str(e))
        #my_html_file = open('./crossref/'+str(i)+'.html', 'wb')
        ret = downloader.get_xml_from_doi(record['doi'], my_file, 'elsevier')
        #downloader.get_html_from_doi(doi, my_html_file, 'elsevier')
        
        my_file.close()
        if ret != True:
            continue
        if filetype == 'xml':
            rawtext = findText(cur_filename)
            print(rawtext)
            if rawtext == None:
                rawtext = ''
            body = {'doi':record['doi'], 'text':rawtext,  'url':str(record['url']), 'title':cur_title}
            
            response = restclient.thesis.list(body=None, params={'doi':record['doi']}, headers={})
            if response.status_code == 200 and response.body['total'] >= 1:
                continue
            try:
                response = restclient.thesis.create(body=body, params={}, headers={})
            except Exception as e:
                print(str(e))
            if response.status_code == 201:
                print( 'insert ok')
                
            pass
        elif filetype == 'pdf':
            pdfConverter = PdfConverter(file_path=cur_filename)
            
            text = pdfConverter.convert_pdf_to_txt()
            
            body = {'doi':record['doi'], 'text':text,  'url':str(record['url']), 'title':cur_title}
            response = restclient.thesis.create(body=body, params={}, headers={})
            if response.status_code == 200:
                print( 'insert ok')
        #SciHub(doi, 'scihub').download(choose_scihub_url_index=1)
except Exception as e:
    print(str(e))


