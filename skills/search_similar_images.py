import os.path
import webbrowser
import subprocess
import sys
from urllib.parse import urlparse
from speech.text2speech import speak

from bs4 import BeautifulSoup as BS
try:
    import cv2
except ImportError:
    speak('Looks like you are using this feature for first time. Downloading few additional files. Please wait')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python==4.8.0.74"])
    import cv2

from utilities.object_detection.yolo_detection import get_object_from_live_stream
from utilities.img_search import reverse_image_search, reverse_image_search_details
from logs.Logging import log
from speech.text2speech import speak

file = 'detected_img.jpg'
path = '/tmp'
web_page_path = '/tmp/output.html'

buy_vendors = ['amazon', 'flipkart', 'aliexpress', 'ebay', 'lenskart', 'meesho', 'jiomart',
               'ajio', 'myntra', 'olx']


def base_method(image: str = None):
    """
    Base method to get image from the recognizer(or say object detector algo)
    then feeding that image to google lens.
    :param image: Image path. If image path is given then, it will skip taking input
    from video stream
    :return: URL of the Google Lens.
    """

    if image is None:
        img_path = os.path.join(path, file)
        image = get_object_from_live_stream()
        cv2.imwrite(img_path, image)
    else:
        img_path = image

    # img_path = '/home/akhil/PycharmProjects/yolov5/0.jpg'
    url = reverse_image_search(img_path)
    return url


def base_method_img_details(image: str = None):
    """
    It returns the html page which can be parsed to extract data from it.
    :param image: Image path. If image path is given then, it will skip taking input
    from video stream
    :return: HTML page
    """

    if image is None:
        img_path = os.path.join(path, file)
        image = get_object_from_live_stream()
        cv2.imwrite(img_path, image)
    else:
        img_path = image

    # img_path = '/home/akhil/PycharmProjects/yolov5/0.jpg'
    # img_path = '/home/akhil/PycharmProjects/object-detection-opencv/spectacles.jpg'
    soup = reverse_image_search_details(img_path)
    return soup


def get_image_header_detail(html: str = None) -> tuple:
    """
    Steps:
    1. Get image
    1. Try to extract header
    :param: html -> Html page if any.
    :return: Header (str)
    """
    if html is None:
        html = base_method_img_details()
    soup = BS(html, 'html.parser')
    header_classes = ['.DeMn2d', '.piBj5']
    # Extract image header det1ails: CLASS: .DeMn2d
    try:
        for header_class in header_classes:
            header_data = soup.select(header_class)
            if len(header_data) != 0:
                header = header_data[0].get_text()
                log.debug(f"Extracted image header: {header}")
                return header, None
    except Exception as e:
        log.exception(f'Exception occurred while fetching image header: {e}')

    return None, html


def get_all_image_info(html=None):
    from utilities.similar_image_display import display_result
    if html is None:
        html = base_method_img_details()
    soup = BS(html, 'html.parser')
    data = {}
    result = []
    try:
        div1 = soup.select('.aah4tc > div:nth-child(1)')  # > div:nth-child(5) > div:nth-child(1)')
        max_iteration = 10
        ind = 1

        while True:
            div2 = div1[0].select(f'div:nth-child({ind}) > div:nth-child(1) > a:nth-child(1)')
            if len(div2) == 0 or max_iteration == 0:
                break
            url = div2[0].get('href')
            div3 = div2[0].select('div:nth-child(1)')
            title = div3[0].get('data-item-title')
            image_url = div3[0].get('data-thumbnail-url')

            data = {
                'image_url': image_url,
                'info': title,
                'url': url
            }
            result.append(data)

            print(f'title of image: {title}')
            print(f'image url: {image_url}')
            print(f'url: {url}')
            ind += 1
            max_iteration -= 1
    except Exception as e:
        log.exception(f'Exception occurred while trying to extract buying link: {e}')
        if len(result) >= 2:
            display_result(result)
            return result
    display_result(result)
    return result


def get_image_header():
    header, html = get_image_header_detail()
    if header is not None:
        print(f'I think it is {header}')
        speak(f'It looks like it is {header}')
    else:
        # speak('I am finding difficulty while searching object. But, here something related to this object ')
        speak('Here is what I found.')
        # search_similar_images_from_image()
        get_all_image_info(html)


def search_amazon_for_product(html: str = None):
    amazon_search_link = 'https://www.amazon.in/s?k={query}'
    header = get_image_header_detail(html)[0]
    if header is not None:
        speak('Searching amazon for something similar.')
        header = header.replace(' ', '+')
        webbrowser.open(amazon_search_link.format(query=header))
        return True
    return False


def get_buy_link_if_any():
    """
    it will try to extract shopping link for the image
    :return:
    """
    html_page = base_method_img_details()
    soup = BS(html_page, 'html.parser')

    if search_amazon_for_product(html = html_page):
        return

    try:
        div1 = soup.select('.aah4tc > div:nth-child(1)')  # > div:nth-child(5) > div:nth-child(1)')
        max_iteration = 10
        ind = 1

        text_class = '.UAiK1e'
        while True:
            div2 = div1[0].select(f'div:nth-child({ind}) > div:nth-child(1) > a:nth-child(1)')
            if len(div2) == 0 or ind == 3:
                break
            url = div2[0].get('href')

            if url is not None:
                url_split = urlparse(url).netloc.split('.')
                for vendee in buy_vendors:
                    if vendee in url_split:
                        print(f'Found result in {vendee} site')
                        speak(f'Found something similar to this on {vendee}. Showing results')
                        webbrowser.open(url)
                        return

            text = div2[0].select(text_class)[0].get_text()
            print(text)

            ind += 1
            max_iteration -= 1
    except Exception as e:
        log.exception(f'Exception occurred while trying to extract buying link: {e}')

    speak('I cant find anything you asked for. Showing all similar found.')
    # webbrowser.open(web_page_path)
    get_all_image_info(html_page)


def search_similar_image():
    """
    This will be exposed to search for similar images from the Google Lens.
    This will open camera to record the frame and that frame will be fed to google lens
    :return:
    """
    url = base_method()
    speak('Sure, showing similar items.')
    webbrowser.open(url)
    pass


def search_similar_images_from_image():
    url = base_method(image=os.path.join(path, file))
    webbrowser.open(url)

# get_buy_link_if_any()
