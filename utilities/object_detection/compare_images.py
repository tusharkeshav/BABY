import cv2
from skimage.metrics import structural_similarity as ssim


def is_image_similar(img1, img2) -> bool:
    """
    It will check the similarity of the image using combination of Mean square error
    and Structural similarity index
    :param img1:
    :param img2:
    :return:
    """

    # if the img1 and img2 is in numpy array then we need to remove these below imread calls
    # image1 = cv2.imread(img1)
    # image2 = cv2.imread(img2)

    image1 = img1
    image2 = img2

    smaller_side = min(image1.shape[0], image1.shape[1], image2.shape[0], image2.shape[1])

    window_size = smaller_side // 7 * 2 + 1

    min_height = min(7, min(image1.shape[0], image2.shape[0]))
    min_width = min(7, min(image1.shape[1], image2.shape[1]))
    image1 = cv2.resize(image1, (min_width, min_height))
    image2 = cv2.resize(image2, (min_width, min_height))

    # Calculate the Mean Squared Error  (MSE)
    mse = ((image1 - image2) ** 2).mean()

    image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # Calculate the Structural Similarity Index (SSIM)
    ssim_score = ssim(image1, image2, multichannel=True)

    # print("Mean Squared Error (MSE):", mse)
    # print("Structural Similarity Index (SSIM):", ssim_score)

    if (ssim_score >= 0.5) or (0.0 > ssim_score > 0.499 and mse < 100.00):
        return True
    else:
        return False
