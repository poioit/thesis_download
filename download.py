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
        print(child)
        ret = child.findall( target, spaces)
        if ret:
            return ret
        else:
            findNode(child, spaces, target)

restclient.add_resource(resource_name='thesis')
#parsexml('./elsevier/The Adrenal Ascorbic Acid Content of Molting Hens and the Effect of ACTH on the Adrenal Ascorbic Acid Content of Laying Hens103382ps0380996.xml')
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
        replaced = re.sub('[\[\]\'\.\/]', '', cur_title+str(record['doi']))
        print(replaced)
        cur_filename = './elsevier/'+replaced+'.'+filetype
        my_file = open(cur_filename, 'wb')  # Need to use 'wb' on Windows
        #my_html_file = open('./crossref/'+str(i)+'.html', 'wb')
        ret = downloader.get_xml_from_doi(record['doi'], my_file, 'elsevier')
        #downloader.get_html_from_doi(doi, my_html_file, 'elsevier')
        
        my_file.close()
        if ret != True:
            continue
        if filetype == 'xml':
            tree = ET.parse(cur_filename)
            root = tree.getroot()
            my_namespaces = dict([
                node for _, node in ET.iterparse(
                    cur_filename, events=['start-ns']
                    )
                    ])
            import pprint
            for child in root:
                for neighbor in root.iter(child.tag):
                    if neighbor.tag.find('originalText') != -1 :
                        rawtexts = findNode(neighbor, my_namespaces, 'xocs:rawtext')
                        for rawtext in rawtexts:
                            print(rawtext.text)
                            body = {'doi':record['doi'], 'text':rawtext.text,  'url':str(record['url']), 'title':cur_title}
                            pprint.pprint(restclient.thesis.actions)
                            response = restclient.thesis.list(body=None, params={'doi':record['doi']}, headers={})
                            if response.status_code == 200 and response.body['total'] >= 1:
                                continue
                            response = restclient.thesis.create(body=body, params={}, headers={})
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


