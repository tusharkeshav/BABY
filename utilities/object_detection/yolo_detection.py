from ultralytics import YOLO
import cv2
import os
from utilities.object_detection.compare_images import is_image_similar
from utilities.object_detection.blur_detect import blur_score

from logs.Logging import log
path = os.path.dirname(os.path.abspath(__file__))
model = YOLO(os.path.join(path, 'yolov8n.pt'))

blur_threshold = 100

# path = "another_folder"
# if not os.path.exists(path):
#     os.mkdir(path)
"""
tuple:
(box, cropped_image, conf_score)
"""


def is_subset(box1, box2):
    """
    It will check what frame coincide with each other.
    Let's say, there is a frame with bounding box then next frame should have atleast
    one corner inside the previous bounding box.
    :param box1:
    :param box2:
    :return:
    """
    # x,y , x1,y1
    box_2 = [(box2[0], box2[1]), (box2[2], box2[3]),
             (box2[0], box2[3]), (box2[2], box2[1])]
    for i in range(len(box_2)):
        if box_2[i][0] >= box1[0] and \
                box_2[i][0] <= box1[2] and \
                box_2[i][1] >= box1[1] and \
                box_2[i][1] <= box1[3]:
            return True

    return False
    pass


def is_area_equivalent(box1, box2):
    """
    Area of both the boxes must be lets say A(box1) <= 1.5 A(box2) (or vice versa)
    :param box1:
    :param box2:
    :return:
    """

    def area(box) -> int:
        return abs(box[0] - box[2]) * abs(box[1] - box[3])
        pass

    if area(box2) <= area(box1) <= int(1.5 * area(box2)) or \
            area(box2) >= area(box1) >= int(1.5 * area(box2)):
        return True
    else:
        return False
    pass


def check_images(detected_imgs):
    """
    It will analyse all the detected images and try to extract best possible image.
    It will detect blur image.
    It will also detect previous frame is same as new frame or not. i.e
    Lets say in first frame mobile get detected. but somehow in other frame, a near by keyboard
    got detected. This will create problem. So, it will also check which things get detected the most.
    :param detected_imgs:
    :return:
    """
    log.debug('Checking and analyzing extracted image')
    img_already_covered = []
    dic = {}
    for indX, data in enumerate(detected_imgs):
        if indX in img_already_covered: continue

        if indX not in img_already_covered:
            img_already_covered.append(indX)
            dic['img' + str(indX)] = [detected_imgs[indX][1]]

        for indY in range(indX + 1, len(detected_imgs)):
            # print(
            #     'i m in check images'
            # )
            if indY not in img_already_covered:
                if is_subset(data[0], detected_imgs[indY][0]) and \
                        is_image_similar(img1=data[1], img2=detected_imgs[indY][1]) and \
                        is_area_equivalent(data[0], detected_imgs[indY][0]):
                    # print('YES SUCCESS')
                    img_already_covered.append(indY)
                    dic['img' + str(indX)].append(detected_imgs[indY][1])
                    pass

    img_list = max(dic.values(), key=len)
    tmp_img = [0, None]
    final_img = None
    last_max = -1

    for img in img_list:
        img_blur_score = blur_score(img)
        tmp_img[0], tmp_img[1] = (img_blur_score, img) if tmp_img[0] < img_blur_score else (tmp_img[0], tmp_img[1])

        if img_blur_score < blur_threshold:
            continue

        else:
            # Means img_blur_score >= threshold i.e 100
            if last_max < img_blur_score:
                last_max = img_blur_score
                final_img = img
    # filename = 'image1.jpg'
    # cv2.imwrite(filename, final_img)
    if final_img is None:
        final_img = tmp_img[1]
    return final_img


def get_object_from_live_stream():
    """
    It will try to extract the object from the live video.
    :return:
    """
    detected_img: list = []

    cam = cv2.VideoCapture(0)
    count = 0
    classes = [i for i in range(1, 79)]
    log.debug('Getting object from live stream.')
    while True:
        count += 1
        if count >= 30:
            break
        ret, frame = cam.read()
        results = model.predict(frame, conf=0.1, classes=classes, max_det=1)
        # cv2.imshow("Object Detection", results[0].plot(labels=False))
        cv2.imshow("Object Detection", results[0].plot())
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        for result in results:
            boxes = result.boxes.cpu().numpy()
            for i, box in enumerate(boxes):
                r = box.xyxy[0].astype(int)
                crop = frame[r[1]:r[3], r[0]:r[2]]
                detected_img.append(
                    (r, crop, box.conf)
                )

                if len(detected_img) >= 20:
                    break
    # print(f'len of detected imgs are {len(detected_img)}')
    cv2.destroyAllWindows()
    final_detected_image = check_images(detected_imgs=detected_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return final_detected_image

# get_object_from_live_stream()