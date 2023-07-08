import cv2


def blur_score(image):
    """
    This will calculate laplacian blur detection and return blur score
    :param image:
    :return:
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    _blur_score = laplacian.var()
    return _blur_score
