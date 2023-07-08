import bs4
import requests
import webbrowser
import re

web_page_path = '/tmp/output.html'


def reverse_image_search(file_path: str) -> str:
    """
    This mehtod will reverse search the google lens for the given file.
    :param file_path: File path of the object you want to search on google
    :return: URL (str)
    """
    search_url = 'https://lens.google.com/_/upload/'
    header = {
        'X-Goog-Upload-Command': 'upload, finalize',
        'X-Goog-Upload-Offset': '0'
    }

    multipart = {
        'encoded_image': (file_path, open(file_path, 'rb')),
        'image_content': ''
    }
    response = requests.post(search_url, files=multipart, allow_redirects=False, headers=header)
    # fetchUrl = response.headers['Location/']
    url = re.search(r'URL=(.+)"', response.text).group(1)
    print(response.text)
    # webbrowser.open(url)
    return url


def reverse_image_search_details(file_path: str) -> str:
    """
    This will search google and try to retrieve more info. It can help you to proviode
    response in form that beautiful soup can read and can be used to extract more info.
    :param file_path:
    :return: HtML Page (str)
    """
    url = 'https://lens.google.com/v3/upload?ssb=1&cpe=1&ifg204=1&&' \
          'hl=en-IN&re=df&st=1688569073203&cd=CPa3uyI&plm=Cg8IARILCPGJlqUGEMCR5mA%3D&' \
          'vpw=1366&vph=652&ep=gisbubb'

    # url = 'https://lens.google.com/v3/upload'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://images.google.com/',
        'Origin': 'https://images.google.com'
    }

    multipart = {'encoded_image': ('0.jpg', open(file_path, 'rb'), 'image/jpeg'), 'image_content': '',
                 'filename': '0.jpg'}

    response = requests.post(url=url, headers=headers, files=multipart)
    web_page = open(web_page_path, 'w')
    web_page.write(response.text)
    web_page.close()
    # webbrowser.open(web_page_path)
    return response.text


# print(reverse_image_search_details('/home/akhil/PycharmProjects/object-detection-opencv/spectacles.jpg'))