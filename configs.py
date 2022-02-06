from cv2 import imread


KEYS_IMAGE_NAME = "keys.png"
keys_img = imread(KEYS_IMAGE_NAME)
KEYS_IMG_WIDTH = keys_img.shape[1]
KEYS_IMG_HEIGHT = keys_img.shape[0]
TOTAL_WHITE_KEYS = 52
TOTAL_BLACK_KEYS = 36
WHITE_KEYS_WIDTH = KEYS_IMG_WIDTH / TOTAL_WHITE_KEYS
WHITE_KEYS_WIDTH_NORMALIZED = WHITE_KEYS_WIDTH / KEYS_IMG_WIDTH
HAND_WIDTH = 5. / TOTAL_WHITE_KEYS * KEYS_IMG_WIDTH * 0.8
ALPHA = 0.1
