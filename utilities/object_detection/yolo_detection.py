import math
import gc
import os
import subprocess
import sys
try:
    """Note: To reduce package size, we will be installing Yolo at fly."""
    from ultralytics import YOLO
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics==8.0.125"])
    from ultralytics import YOLO

try:
    import cv2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python==4.8.0.74"])
    import cv2

from utilities.object_detection.compare_images import is_image_similar
from utilities.object_detection.blur_detect import blur_score
from config.get_config import get_config

from logs.Logging import log, configured_log_level
path = os.path.dirname(os.path.abspath(__file__))
model = YOLO(os.path.join(path, 'yolov8n.pt'))

"""
:param method: Method can be either of closest or max_detection or mixed

method = closest : It will detect object that is more near to centre of window.
Its based on the fact that user will place object near camera close to centre

method = max_detection : It will prefer object which is detected majorly in video stream.
It's based on fact that the object detected should be more than once in the video stream.

method = mixed : Its based on both closest and max_detection. It actually calculate weight 
of max_detection vs closest. It assumes that object should be detected more with its distance from centre is minimum
"""
method = get_config(section='objectDetection',
                    key='method')

total_frame_to_record = get_config(section='objectDetection',
                                   key='total_frame_input',
                                   fallback='mixed')
blur_threshold = 100

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


def calculate_image_distance_weight():

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
    processed_images_dict = {}
    distance_score = {}
    for indX, data in enumerate(detected_imgs):
        if indX in img_already_covered: continue

        if indX not in img_already_covered:
            img_already_covered.append(indX)
            processed_images_dict['img' + str(indX)] = [detected_imgs[indX][1]]
            distance_score['img' + str(indX)] = [detected_imgs[indX][3]]

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
                    processed_images_dict['img' + str(indX)].append(detected_imgs[indY][1])
                    distance_score['img' + str(indX)].append(detected_imgs[indY][3])
                    pass
    if method == 'max_detection':
        img_list = max(processed_images_dict.values(), key=len)
        pass
    elif method == 'closest':
        closest_image_dict_key = min(distance_score,
                                     key=lambda key: sum(distance_score[key]) / len(distance_score[key]))
        img_list = processed_images_dict[closest_image_dict_key]

        pass
    elif method == 'mixed':
        weighted_score = {key: len(processed_images_dict[key]) / {k: sum(distance_score[k])/len(distance_score[k])
                         for k in distance_score}[key] * 100 for key in processed_images_dict}
        max_weighted_score_key = max(weighted_score,  key=lambda key: weighted_score[key])
        img_list = processed_images_dict[max_weighted_score_key]
        del weighted_score
        del max_weighted_score_key
        gc.collect()
    else:
        log.exception('Method of objection detection is invalid. check config')
        raise Exception('Method of objection should be: max_detection or closest or mixed ')

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
    del img_list
    gc.collect()
    if final_img is None:
        final_img = tmp_img[1]
    cv2.imwrite('detected_image.jpg', final_img)
    return final_img


def find_centre(x1, y1, x2, y2):
    centre = ((x2 + x1) // 2, (y2 + y1) // 2)  # (width, height)
    return centre


def two_point_distance(point1: tuple, point2: tuple) -> float:
    return math.dist(point1, point2)


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
        results = model.predict(frame, conf=0.1, classes=classes, max_det=1) if configured_log_level == 'DEBUG' \
            else model.predict(frame, conf=0.1, classes=classes, max_det=1, verbose=False)
        # cv2.imshow("Object Detection", results[0].plot(labels=False))

        processed_frame = results[0].plot()
        frame_height = processed_frame.shape[0]
        frame_width = processed_frame.shape[1]
        start_pt = center = (frame_width // 2, frame_height // 2)  # (x,y) or say (width, height)
        if configured_log_level == 'DEBUG':
            color = (0, 255, 0)
            thickness = 1
            try:
                boxes = results[0].boxes.cpu().numpy()
                box = boxes[0].xyxy[0].astype(int)
                start_pt = find_centre(box[0], box[1], box[2], box[3])
            except:
                pass
            img = cv2.line(processed_frame, start_pt, center, color, thickness)
            cv2.imshow("Object Detection", img)

        else:
            cv2.imshow("Object Detection", results[0].plot(labels=False))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        for result in results:
            boxes = result.boxes.cpu().numpy()
            for i, box in enumerate(boxes):
                r = box.xyxy[0].astype(int)
                crop = frame[r[1]:r[3], r[0]:r[2]]
                box_center = find_centre(r[0], r[1], r[2], r[3])
                # print('two point distance is: ' + str(two_point_distance(center, box_center)))
                detected_img.append(
                    (r, crop, box.conf, two_point_distance(center, box_center))
                )

                if len(detected_img) >= 20:
                    break
    # print(f'len of detected imgs are {len(detected_img)}')
    cv2.destroyAllWindows()
    final_detected_image = check_images(detected_imgs=detected_img)
    return final_detected_image

# get_object_from_live_stream()