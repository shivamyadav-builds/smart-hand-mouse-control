import cv2
import mediapipe as mp
import pyautogui
import time
import math
import serial


# initialize mediapipe hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7
)


# connect arduino
arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(3)


# start webcam
cap = cv2.VideoCapture(0)


# click control
click_times = []
clicking = False

scroll_mode = False
freeze_cursor = False


# screenshot control
screenshot_cooldown = 10
last_screenshot_time = 0
screenshot_hold_start = 0
screenshot_taken = False


# emergency control
emergency_hold_start = 0
emergency_start_time = 0
emergency_last_time = 0
emergency_active = False


# screen size
screen_w, screen_h = pyautogui.size()

print("\nSmart Hand Mouse Control System.")


# previous cursor position
prev_screen_x = 0
prev_screen_y = 0

# cursor smoothing
smoothening = 7


if not cap.isOpened():

    print("cannot open camera")
    arduino.close()
    exit()


while True:

    ret, frame = cap.read()

    if not ret:

        print("can't receive frame")
        break


    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)


    if result.multi_hand_landmarks:

        for hand_landmarks in result.multi_hand_landmarks:

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )


        # get finger tips
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]


        # check fingers
        fingers = [
            1 if hand_landmarks.landmark[tip].y <
            hand_landmarks.landmark[tip - 2].y else 0
            for tip in [8, 12, 16, 20]
        ]



        # EMERGENCY GESTURE
        # only pinky finger extended
    

        thumb_folded = math.hypot(
            thumb_tip.x - hand_landmarks.landmark[9].x,
            thumb_tip.y - hand_landmarks.landmark[9].y
        ) < 0.18


        emergency_gesture = (
            fingers == [0, 0, 0, 1]
            and thumb_folded
        )


        if emergency_gesture:

            if emergency_hold_start == 0:

                emergency_hold_start = time.time()


            hold_time = time.time() - emergency_hold_start


            if not emergency_active:

                cv2.putText(
                    frame,
                    "Hold emergency gesture...",
                    (10, 170),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 165, 255),
                    2
                )


            # trigger after 1 second
            if (
                hold_time >= 1
                and not emergency_active
                and time.time() - emergency_last_time >= 20
            ):

                emergency_active = True
                emergency_start_time = time.time()
                emergency_last_time = time.time()


                # send emergency command to Arduino
                arduino.write(b'E')
                arduino.flush()


                print("EMERGENCY ALERT TRIGGERED!")


        else:

            emergency_hold_start = 0


        # emergency alert
        if emergency_active:

            cv2.putText(
                frame,
                "!!! EMERGENCY ALERT !!!",
                (10, 170),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )


            cv2.putText(
                frame,
                "Emergency gesture detected",
                (10, 205),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )


            # emergency active for 10 seconds
            if time.time() - emergency_start_time >= 10:

                emergency_active = False


    
        # DISTANCE BETWEEN THUMB AND INDEX
    

        dist = math.hypot(
            thumb_tip.x - index_tip.x,
            thumb_tip.y - index_tip.y
        )


    
        # CLICK


        if dist < 0.06:

            if not clicking:

                clicking = True
                freeze_cursor = True

                current_time = time.time()


                # double click
                if (
                    len(click_times) > 0
                    and current_time - click_times[-1] < 0.4
                ):

                    pyautogui.doubleClick()


                    cv2.putText(
                        frame,
                        "Double click",
                        (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 255),
                        2
                    )


                    click_times = []


                # first click
                else:

                    pyautogui.click()

                    click_times.append(current_time)


                    cv2.putText(
                        frame,
                        "Single click",
                        (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 0),
                        2
                    )


        else:

            clicking = False
            freeze_cursor = False



        # MOVE CURSOR


        if not freeze_cursor:

            screen_x = int(index_tip.x * screen_w)
            screen_y = int(index_tip.y * screen_h)


            # smooth cursor movement
            curr_screen_x = (
                prev_screen_x +
                (screen_x - prev_screen_x) / smoothening
            )


            curr_screen_y = (
                prev_screen_y +
                (screen_y - prev_screen_y) / smoothening
            )


            pyautogui.moveTo(
                int(curr_screen_x),
                int(curr_screen_y),
                duration=0
            )


            prev_screen_x = curr_screen_x
            prev_screen_y = curr_screen_y


    
        # SCROLL MODE
    

        if sum(fingers) == 4:

            scroll_mode = True

        else:

            scroll_mode = False


        # scroll actions
        if scroll_mode:

            if index_tip.y < 0.4:

                pyautogui.scroll(5)


                cv2.putText(
                    frame,
                    "Scroll up",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )


            elif index_tip.y > 0.6:

                pyautogui.scroll(-5)


                cv2.putText(
                    frame,
                    "Scroll down",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )



        # SCREENSHOT
        # fist must be held for 2 seconds
        # blocked during emergency gesture


        if sum(fingers) == 0 and not emergency_gesture:

            if screenshot_hold_start == 0:

                screenshot_hold_start = time.time()


            hold_time = time.time() - screenshot_hold_start


            if not screenshot_taken:

                cv2.putText(
                    frame,
                    "Hold fist for 2 sec...",
                    (10, 130),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 0),
                    2
                )


                current_time = time.time()


                if (
                    hold_time >= 2
                    and current_time - last_screenshot_time >
                    screenshot_cooldown
                ):

                    pyautogui.hotkey(
                        'shift',
                        'printscreen'
                    )


                    cv2.putText(
                        frame,
                        "Screenshot taken",
                        (10, 130),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 0),
                        2
                    )


                    last_screenshot_time = current_time
                    screenshot_taken = True


        else:

            screenshot_hold_start = 0
            screenshot_taken = False


    # show camera
    cv2.imshow("live video", frame)


    # press q to quit
    if cv2.waitKey(1) == ord('q'):

        break


cap.release()
arduino.close()
cv2.destroyAllWindows()