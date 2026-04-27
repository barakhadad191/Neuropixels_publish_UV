import cv2

import numpy as np
import tqdm
from matplotlib import pyplot as plt
from moviepy.editor import *
from skimage.measure import regionprops
from scipy.ndimage import measurements

import sys


def read_video_file_to_array(video_path):
    frames_list = []
    vidcap = cv2.VideoCapture(video_path)
    success, image = vidcap.read()

    count = 0
    while success:
        success, image = vidcap.read()
        # print('Read a new frame: ', success)
        if image is None:
            break
        count += 1
        frames_list.append(image)
    frames_array = np.array(frames_list)
    return frames_array


def prep_video(video_path):
    print("Let's prepare the video")
    rot_path = os.path.splitext(video_path)[0] + '_rot.mp4'

    if not os.path.isfile(rot_path):
        print("Let's rotate!")
        clip = VideoFileClip(video_path)
        sub_clip = clip.subclip(0, 5)

        plt.figure('Pick the line of the cage (two points)')
        plt.imshow(sub_clip.get_frame(3))
        cords_rot = plt.ginput(2)
        plt.show(block=False)

        angle_of_rotation = np.rad2deg(
            np.arctan((cords_rot[0][1] - cords_rot[1][1]) / (cords_rot[0][0] - cords_rot[1][0])))

        clip = clip.rotate(angle_of_rotation)
        clip.write_videofile(rot_path, fps=clip.fps)

    crop_path = os.path.splitext(rot_path)[0] + '_crop.mp4'

    if not os.path.isfile(crop_path):
        print("Let's crop")
        clip = VideoFileClip(rot_path)
        sub_clip = clip.subclip(0, 5)

        plt.figure('Find the crop coordinates for the cage')
        plt.imshow(sub_clip.get_frame(3))
        cords_crop = plt.ginput(2)
        plt.show(block=False)

        cropped_video_array = clip.crop(y1=int(cords_crop[0][1]), x1=int(cords_crop[0][0]), y2=int(cords_crop[1][1]),
                                        x2=int(cords_crop[1][0]))

        cropped_video_array.write_videofile(crop_path, fps=clip.fps)

    print("Done with video prep!!")

    return crop_path


def get_led_vector(video_path):
    print("Get led indicator")
    crop_path = os.path.splitext(video_path)[0] + '_crop.mp4'

    if not os.path.isfile(crop_path):
        clip = VideoFileClip(video_path)
        sub_clip = clip.subclip(0, 5)

        plt.figure('Pick the led crop coordinates')
        plt.imshow(sub_clip.get_frame(3))
        cords_crop = plt.ginput(2)
        plt.show(block=False)

        led_array = clip.crop(y1=int(cords_crop[0][1]), x1=int(cords_crop[0][0]), y2=int(cords_crop[1][1]),
                              x2=int(cords_crop[1][0]))

        led_array.write_videofile(crop_path, fps=clip.fps)

    clip = VideoFileClip(crop_path)
    sub_clip = clip.subclip(0, 5)

    plt.figure('Pick the led coordinates')
    plt.imshow(sub_clip.get_frame(3))
    led_location = plt.ginput(1)
    plt.show(block=False)

    led_vec = [frame[int(led_location[0][1]), int(led_location[0][0]), :] for frame in clip.iter_frames()]

    plt.figure('Auditory Led Vector')
    plt.plot(led_vec)
    plt.show(block=False)

    return led_vec


def find_color_th(image):
    def nothing(x):
        pass

    # Create a window
    cv2.namedWindow('image')

    # create trackbars for color change
    cv2.createTrackbar('HMin', 'image', 0, 179, nothing)  # Hue is from 0-179 for Opencv
    cv2.createTrackbar('SMin', 'image', 0, 255, nothing)
    cv2.createTrackbar('VMin', 'image', 0, 255, nothing)
    cv2.createTrackbar('HMax', 'image', 0, 179, nothing)
    cv2.createTrackbar('SMax', 'image', 0, 255, nothing)
    cv2.createTrackbar('VMax', 'image', 0, 255, nothing)

    # Set default value for MAX HSV trackbars.
    cv2.setTrackbarPos('HMax', 'image', 179)
    cv2.setTrackbarPos('SMax', 'image', 255)
    cv2.setTrackbarPos('VMax', 'image', 255)

    # Initialize to check if HSV min/max value changes
    hMin = sMin = vMin = hMax = sMax = vMax = 0
    phMin = psMin = pvMin = phMax = psMax = pvMax = 0

    img = image
    output = img
    waitTime = 33

    while (1):

        # get current positions of all trackbars
        hMin = cv2.getTrackbarPos('HMin', 'image')
        sMin = cv2.getTrackbarPos('SMin', 'image')
        vMin = cv2.getTrackbarPos('VMin', 'image')

        hMax = cv2.getTrackbarPos('HMax', 'image')
        sMax = cv2.getTrackbarPos('SMax', 'image')
        vMax = cv2.getTrackbarPos('VMax', 'image')

        # Set minimum and max HSV values to display
        lower = np.array([hMin, sMin, vMin])
        upper = np.array([hMax, sMax, vMax])

        # Create HSV Image and threshold into a range.
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        output = cv2.bitwise_and(img, img, mask=mask)

        # Print if there is a change in HSV value
        if ((phMin != hMin) | (psMin != sMin) | (pvMin != vMin) | (phMax != hMax) | (psMax != sMax) | (
                pvMax != vMax)):
            print("(hMin = %d , sMin = %d, vMin = %d), (hMax = %d , sMax = %d, vMax = %d)" % (
                hMin, sMin, vMin, hMax, sMax, vMax))
            phMin = hMin
            psMin = sMin
            pvMin = vMin
            phMax = hMax
            psMax = sMax
            pvMax = vMax

        # Display output image
        cv2.imshow('image', output)

        # Wait longer to prevent freeze for videos.
        if cv2.waitKey(waitTime) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


def get_movement_vectors(video_path):
    print("Getting location for mice!")
    clip = VideoFileClip(video_path)
    sub_clip = clip

    def filter_black_mouse(image):
        img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # lower = np.array([36, 36, 0])
        # upper = np.array([74, 255, 255])
        lower = np.array([36, 67, 112])
        upper = np.array([74, 255, 255])
        mask = cv2.inRange(img, lower, upper)
        frame = cv2.bitwise_and(img, img, mask=mask)
        frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)

        # cv2.imshow('image', frame)

        a = 5

        (T, frame) = cv2.threshold(frame, 10, 255,
                                   cv2.THRESH_BINARY)
        return frame

    filt_path = video_path[:-4] + '_filt.mp4'

    if not os.path.isfile(filt_path):
        sub_clip_filtered = sub_clip.fl_image(filter_black_mouse)
        sub_clip_filtered.write_videofile(f'{filt_path}', fps=clip.fps)
    else:
        sub_clip_filtered = VideoFileClip(filt_path)

    # sub_clip_filtered = sub_clip_filtered.subclip(int(0*60), int(2*60))
    COM_array = [(0, 0)]

    for frame in tqdm.tqdm(sub_clip_filtered.iter_frames()):
        _, binary_image = cv2.threshold(frame, 128, 255, cv2.THRESH_BINARY)
        com = measurements.center_of_mass(binary_image)
        try:
            COM_array.append((int(com[0]), int(com[1])))
            # COM_array.append(regionprops(frame)[0].centroid)
        except:
            COM_array.append(COM_array[-1])

    # COM_array = [regionprops(frame)[0].centroid for frame in sub_clip_filtered.iter_frames()]
    # plt.figure('Frame following th')
    # plt.subplot(121)
    # plt.imshow(sub_clip_filtered.get_frame(clip.fps*15)[:, :, 0])
    # plt.subplot(122)
    # plt.imshow(sub_clip.get_frame(clip.fps*15)[:, :, 0])
    # plt.show()

    COM_array = COM_array[1:]
    frames = int(sub_clip_filtered.fps * sub_clip_filtered.duration)

    # COM_array = []
    # # WCOM_array = []
    # for frame_num in tqdm.tqdm(range(frames)):
    #     frame = sub_clip_filtered.get_frame(frame_num)
    #     properties = regionprops(frame)
    #     COM_array.append(properties[0].centroid)
    # #   WCOM_array.append(properties[0].weighted_centroid)

    frame_num = 2
    frame = sub_clip_filtered.get_frame(frame_num/sub_clip_filtered.fps)
    plt.figure('Frame')
    plt.imshow(frame)
    plt.scatter(COM_array[frame_num][1], COM_array[frame_num][0], s=1000, c='red', marker='+')
    # plt.scatter(WCOM_array[frame_num][1], WCOM_array[frame_num][0], s=1000, c='green', marker='+')
    plt.show(block=True)

    COM_array = np.array(COM_array)
    # WCOM_array = np.array(WCOM_array)

    x = COM_array[:, 1]
    y = COM_array[:, 0]
    color_scale = np.linspace(0, 1, len(x))

    plt.figure()
    plt.quiver(x[:-1], y[:-1], x[1:] - x[:-1], y[1:] - y[:-1], scale_units='xy', angles='xy', scale=1, cmap=plt.cm.jet)

    plt.show(block=True)
    return COM_array
    # return COM_array, WCOM_array


if __name__ == "__main__":
    video_path = r"\\path\Pixel1\1_auditory_neuropixels_BarakH\20240912_C11_T1_NP2_-10dB_g0\BARAK-240912-115721\CHRONIC11-240911-121436_BARAK-240912-115721_Cam1.avi"
    save_path = r"\\path\Pixel1\1_auditory_neuropixels_BarakH\20240912_C11_T1_NP2_-10dB_g0\video_loc.npz"

    ''' Get led signal for sync of video '''
    led_vector = get_led_vector(video_path)

    ''' Crop and rotate video for analysis '''
    video_ready = prep_video(video_path)

    ''' Threshold green cap and get movement '''
    # location_com, location_wcom = get_movement_vectors(video_ready)
    location_com = get_movement_vectors(video_ready)

    clip = VideoFileClip(video_path)

    np.savez(save_path, led_info=led_vector, location_com=location_com, first_frame=clip.get_frame(1))
    # np.savez(save_path, led_info=led_vector, location_com=location_com, location_wcom=location_wcom, first_frame=clip.get_frame(1))

