import numpy as np
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import cv2
import mediapipe as mp
import utils
import configs
import json


class DetectorAgent(Agent):
    def __init__(self, jid, password, receiver_jid):
        super().__init__(jid, password)
        self.receiver_jid = receiver_jid
        self.cap = cv2.VideoCapture(0)
        self.hand_detector = mp.solutions.hands.Hands(model_complexity=1,
                                                      min_detection_confidence=0.3,
                                                      min_tracking_confidence=0.4)
        self.camera_frame = None
        self.img_dims = None
        self.hand_keypoints = None
        self.pressed_keys_coords = None
        self.prev_pressed_keys = []
        self.new_pressed_keys = []
        
    class DetectorAgentBehaviour(FSMBehaviour):
        async def on_start(self):
            print("Starting Detector Agent.")

        async def on_end(self):
            print("Ending Detector Agent.")

    class ReadCameraFrame(State):
        async def run(self):
            if not self.agent.cap.isOpened():
                self.agent.cap.release()
                self.agent.stop()
                return
            success, image = self.agent.cap.read()
            if not success:
                print("Couldn't read camera frame")
                return
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.agent.camera_frame = image
            self.agent.img_dims = image.shape[:2]
            self.set_next_state("DetectHandKeypoints")

    class DetectHandKeypoints(State):
        async def run(self):
            self.agent.hand_keypoints = self.agent.hand_detector.process(self.agent.camera_frame)
            self.agent.camera_frame.flags.writeable = True
            self.agent.camera_frame = cv2.cvtColor(self.agent.camera_frame, cv2.COLOR_RGB2BGR)
            self.set_next_state("Visualize")

    class Visualize(State):
        async def run(self):
            if self.agent.hand_keypoints.multi_hand_landmarks:
                for hand_landmarks in self.agent.hand_keypoints.multi_hand_landmarks:
                    min_x, max_x, min_y, max_y = utils.get_min_max_landmarks(hand_landmarks)
                    x_center_norm, y_center_norm = min_x + (max_x - min_x) / 2. - 0.065, min_y + (max_y - min_y) / 2.
                    min_x, max_x, min_y, max_y = int(min_x * self.agent.img_dims[1]), int(max_x * self.agent.img_dims[1]), int(
                        min_y * self.agent.img_dims[0]), int(max_y * self.agent.img_dims[0])
                    cropped_hand = self.agent.camera_frame[min_y:max_y, min_x:max_x]
                    cropped_hand = cv2.resize(cropped_hand, (int(configs.HAND_WIDTH), 300), interpolation=cv2.INTER_AREA)
                    cropped_hand_width, cropped_hand_height = cropped_hand.shape[1], cropped_hand.shape[0]
                    keys_with_hand_img = configs.keys_img.copy()

                    hand_min_x = int(configs.KEYS_IMG_WIDTH * x_center_norm - cropped_hand_width / 2.)
                    hand_max_x = int(configs.KEYS_IMG_WIDTH * x_center_norm + cropped_hand_width / 2.)
                    hand_min_y = int(configs.KEYS_IMG_HEIGHT * y_center_norm - cropped_hand_height / 2.)
                    hand_max_y = int(configs.KEYS_IMG_HEIGHT * y_center_norm + cropped_hand_height / 2.)

                    if hand_min_x <= 0:
                        hand_min_x = 0
                        cropped_hand = cropped_hand[:, cropped_hand.shape[1] - (hand_max_x - hand_min_x):]
                    if hand_min_y <= 0:
                        hand_min_y = 0
                        cropped_hand = cropped_hand[cropped_hand.shape[0] - (hand_max_y - hand_min_y):, :]
                    if hand_max_x >= configs.KEYS_IMG_WIDTH:
                        hand_max_x = configs.KEYS_IMG_WIDTH
                        cropped_hand = cropped_hand[:, 0:hand_max_x - hand_min_x]
                    if hand_max_y >= configs.KEYS_IMG_HEIGHT:
                        hand_max_y = configs.KEYS_IMG_HEIGHT
                        cropped_hand = cropped_hand[0:hand_max_y - hand_min_y, :]

                    keys_with_hand_img[hand_min_y:hand_max_y, hand_min_x:hand_max_x] = cv2.addWeighted(
                        keys_with_hand_img[hand_min_y:hand_max_y, hand_min_x:hand_max_x],
                        configs.ALPHA, cropped_hand, (1.0 - configs.ALPHA), 0.0
                    )

                    cv2.imshow('Synthesizer', keys_with_hand_img)

            if cv2.waitKey(5) & 0xFF == 27:
                self.agent.camera_frame.release()
                self.agent.stop()
                return
            self.set_next_state("DetectPressedChords")

    class DetectPressedChords(State):
        async def run(self):
            if self.agent.hand_keypoints.multi_hand_landmarks:
                self.agent.pressed_keys_coords = utils.get_pressed_keys_coords(self.agent.hand_keypoints.multi_hand_landmarks[0])
                pressed_x = [coord[0] for coord in self.agent.pressed_keys_coords.values()]
                # pressed_y = [coord[1] for coord in self.agent.pressed_keys_coords.values()]
                self.agent.new_pressed_keys = [
                    np.clip(int(x / configs.WHITE_KEYS_WIDTH_NORMALIZED), 0, configs.TOTAL_WHITE_KEYS - 1)
                    for x in pressed_x]
                [chords_to_play, chords_to_stop] = utils.get_played_and_stopped_chords(self.agent.prev_pressed_keys,
                                                                                     self.agent.new_pressed_keys)

                self.agent.prev_pressed_keys = self.agent.new_pressed_keys
                msg = Message(
                    to=self.agent.receiver_jid,
                    body=json.dumps([chords_to_play, chords_to_stop]),
                    metadata={"ontology": "airsynth"})
                await self.send(msg)
            else:
                self.agent.pressed_keys_coords = None
                all_keys = np.arange(0, configs.TOTAL_WHITE_KEYS).tolist()
                msg = Message(
                    to=self.agent.receiver_jid,
                    body=json.dumps([[], all_keys]),
                    metadata={"ontology": "airsynth"})
                await self.send(msg)
            self.set_next_state("ReadCameraFrame")

    async def setup(self):
        fsm = self.DetectorAgentBehaviour()
        fsm.add_state(name="ReadCameraFrame", state=self.ReadCameraFrame(), initial=True)
        fsm.add_state(name="DetectHandKeypoints", state=self.DetectHandKeypoints())
        fsm.add_state(name="Visualize", state=self.Visualize())
        fsm.add_state(name="DetectPressedChords", state=self.DetectPressedChords())
        
        fsm.add_transition(source="ReadCameraFrame", dest="DetectHandKeypoints")
        fsm.add_transition(source="DetectHandKeypoints", dest="Visualize")
        fsm.add_transition(source="Visualize", dest="DetectPressedChords")
        fsm.add_transition(source="DetectPressedChords", dest="ReadCameraFrame")
        self.add_behaviour(fsm)
