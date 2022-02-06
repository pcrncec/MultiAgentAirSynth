import cv2
import numpy as np


def get_min_max_landmarks(landmarks):
    x_landmarks = [keypoint.x for keypoint in landmarks.landmark]
    y_landmarks = [keypoint.y for keypoint in landmarks.landmark]

    min_x = max(0, min(x_landmarks))
    min_y = max(0, min(y_landmarks))
    max_x = min(1, max(x_landmarks))
    max_y = min(1, max(y_landmarks))
    return min_x, max_x, min_y, max_y


def draw_hand_bbox(image, min_x, max_x, min_y, max_y):
    cv2.rectangle(image, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (255, 0, 0), 2)
    return image


def get_pressed_keys_coords(landmarks):
    y_landmarks = [keypoint.y for keypoint in landmarks.landmark]
    x_landmarks = [keypoint.x for keypoint in landmarks.landmark]
    first_finger_landmarks_ind = [2, 6, 10, 14, 18]
    last_finger_landmarks_ind = [4, 8, 12, 16, 20]
    pressed_keys = {}

    for i in range(len(first_finger_landmarks_ind)):
        if y_landmarks[last_finger_landmarks_ind[i]] > y_landmarks[first_finger_landmarks_ind[i]]:
            x_landmarks = np.clip(x_landmarks, 0, 1)
            y_landmarks = np.clip(y_landmarks, 0, 1)
            pressed_keys[last_finger_landmarks_ind[i]] = (x_landmarks[last_finger_landmarks_ind[i]], y_landmarks[last_finger_landmarks_ind[i]])
    return pressed_keys


def get_played_and_stopped_chords(prev_pressed_keys, new_pressed_keys):
    chords_to_play = [int(x) for x in new_pressed_keys if x not in prev_pressed_keys]
    chords_to_stop = [int(x) for x in prev_pressed_keys if x not in new_pressed_keys]
    return [chords_to_play, chords_to_stop]


def resize_img_with_aspect_ratio(img, width):
    org_h, org_w = img.shape[:2]
    ratio = width / float(org_w)
    if ratio < 1:
        resized_img = cv2.resize(img, (int(width), int(org_h * ratio)), interpolation=cv2.INTER_AREA)
    else:
        resized_img = cv2.resize(img, (int(width), int(org_h * ratio)), interpolation=cv2.INTER_LINEAR)
    return resized_img
