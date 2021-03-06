import sys 
sys.path.append('/usr/local/lib/python2.7/site-packages')

# import the necessary packages
from collections import deque
import subprocess
import numpy as np
import argparse
import imutils
import cv2
import time
import moveservo
import threading
import bt_withMain
import time
import gpsdshm

gpsd_shm = gpsdshm.Shm()
dirBuoy = "none"
rudder_channel = 3
exitapp = False

# records coordinates of boat and direction of buoy
# from the boat
coordsList = []
endCoords = [] # coordinates of the end of each vector
directionsList = []
iteration = 0

def main():
	thread1 = threading.Thread(target=ballTrack)
	thread1.start()
	while True:
		global dirBuoy
		print(dirBuoy)
		# used to get majority direction in a given time
		left = 0
		straight = 0
		right = 0
		
		#Converts lat and long degrees to meters from equator and prime meridian respectively
		lat=gpsd_shm.fix.latitude*111*1000 #Latitude in meters from equator
		lon=gpsd_shm.fix.longitude*Math.cos(gpsd_shm.fix.latitude*3.14/180)*111*1000

		# if the buoy is seen record the boats position
		if dirBuoy !=  'none'
			coordsList.append(lat)
			coordsList.append(lon)

			# then record the direction that the buoy is from the boat
			if dirBuoy == 1:
				directionsList.append(gpsd_shm.fix.track - 75)
				
			elif dirBuoy == 2:
				directionsList.append(gpsd_shm.fix.track - 56)	

			elif dirBuoy == 3:
				directionsList.append(gpsd_shm.fix.track - 37)

			elif dirBuoy == 4:
				directionsList.append(gpsd_shm.fix.track - 19)

			elif dirBuoy == 5:
				directionsList.append(gpsd_shm.fix.track)

			elif dirBuoy == 6:
				directionsList.append(gpsd_shm.fix.track + 19)

			elif dirBuoy == 7:
				directionsList.append(gpsd_shm.fix.track + 38)

			elif dirBuoy == 8:
				directionsList.append(gpsd_shm.fix.track + 56)

			elif dirBuoy == 9:
				directionsList.append(gpsd_shm.fix.track + 75)

			else:
				# search for buoy
				findBuoy();
			
			makeVecor(iteration)
			iteration++

			leaveCurCoord(lat, lon)

# turns rudder 45 degrees left or right to turn
# or moves rudder to center to go straight
def turnBoat(dir):
	if dir == 'left':
		moveservo.main(rudder_channel, 437)

	if dir == 'right':
		moveservo.main(rudder_channel, 337)

	if dir == 'straight':
		moveservo.main(rudder_channel, 387)

def makeVector(iteration):
	lat = coordsList[iteration] + math.cos(directionsList[iteration]*3.14/180) * 100
	lon = coordsList[iteration + 1] + math.sin(directionsList[iteration]*3.14/180) * 100
	endCoords.append(lat)
	endCoords.append(lon)

# leaves current area to get more data (coordinates and directions)
# for the buoy location
def leaveCurCoord(lat, lon):
	turnBoat('right')
	time.sleep(5)
	turnBoat('straight')

	newLat = lat*111*1000 #Latitude in meters from equator
	newLon = lon*Math.cos(gpsd_shm.fix.latitude*3.14/180)*111*1000

	while abs(newLat - lat) < 4 and abs(newLon - lon) < 4:
		newLat = gpsd_shm.fix.latitude*111*1000
		newLon = gpsd_shm.fix.longitude*Math.cos(gpsd_shm.fix.latitude*3.14/180)*111*1000


# function to retrieve data from gps
def gps():
    try:
        gpsData = gpsInfo.main()
    except:
        print "gps signal error"
    return gpsData

# when buoy is not in view, search area for buoy
def findBuoy():
	found = False

	while not found:
		print("searching")
		found = True

# based on the boats current position and a given destination
# the boat will navigate to the given coord
def goCoord():
	print("go")


# tracks ball shaped object in recorded video
def ballTrack():
	while not exitapp:
		# take video with pi camera
		subprocess.call("/home/pi/camera/video.sh", shell=True)

		# construct the argument parse and parse the arguments
		ap = argparse.ArgumentParser()
		ap.add_argument("-v", "--video", default="/home/pi/camera/videoMP4.mp4",
			help="path to the (optional) video file")
		ap.add_argument("-b", "--buffer", type=int, default=64,
			help="max buffer size")
		args = vars(ap.parse_args())
		print args

		# define the lower and upper boundaries of the "green"
		# ball in the HSV color space, then initialize the
		# list of tracked points
		redLower = (169, 100, 100)
		redUpper = (189, 255, 255)
		pts = deque(maxlen=args["buffer"])

		# if a video path was not supplied, grab the reference
		# to the webcam
		if not args.get("video", False):
			camera = cv2.VideoCapture(0)

		# otherwise, grab a reference to the video file
		else:
			camera = cv2.VideoCapture(args["video"])

		# keep looping
		while True:
			# executes bash script to take an image and save
			#subprocess.call("/home/pi/camera/camera.sh", shell=True)

			#time.sleep(2)

			#camera = cv2.VideoCapture("/home/pi/camera/image.jpg")

			# grab the current frame
			(grabbed, frame) = camera.read()

			# if we are viewing a video and we did not grab a frame,
			# then we have reached the end of the video
			if args.get("video") and not grabbed:
				print("breaking")
				break

			# resize the frame, blur it, and convert it to the HSV
			# color space
			frame = imutils.resize(frame, width=600)

			blurred = cv2.GaussianBlur(frame, (11, 11), 0)
			hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

			# construct a mask for the color "green", then perform
			# a series of dilations and erosions to remove any small
			# blobs left in the mask
			mask = cv2.inRange(hsv, redLower, redUpper)
			mask = cv2.erode(mask, None, iterations=2)
			mask = cv2.dilate(mask, None, iterations=2)

			# find contours in the mask and initialize the current
			# (x, y) center of the ball
			cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
				cv2.CHAIN_APPROX_SIMPLE)[-2]
			center = None
			# only proceed if at least one contour was found
			if len(cnts) > 0:
				# find the largest contour in the mask, then use
				# it to compute the minimum enclosing circle and
				# centroid
				c = max(cnts, key=cv2.contourArea)
				((x, y), radius) = cv2.minEnclosingCircle(c)
				M = cv2.moments(c)
				center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

				# only proceed if the radius meets a minimum size
				if radius > 10:
					# draw the circle and centroid on the frame,
					# then update the list of tracked points
					cv2.circle(frame, (int(x), int(y)), int(radius),
						(0, 255, 255), 2)
					cv2.circle(frame, center, 5, (0, 0, 255), -1)
				global dirBuoy
				# frame size is 600, left middle and right are split into 3 zones
				if center[0] < 67:
					dirBuoy = "1"
				elif center[0] < 134:
					dirBuoy = "2"
				elif center[0] < 201:
					dirBuoy = "3"
				elif center[0] < 268:
					dirBuoy = "4"
				elif center[0] < 335:
					dirBuoy = "5"
				elif center[0] < 402:
					dirBuoy = "6"
				elif center[0] < 469:
					dirBuoy = "7"
				elif center[0] < 536:
					dirBuoy = "8"
				elif center[0] <= 600:
					dirBuoy = "9"
				else:
					dirBuoy = "none"
			# update the points queue
			pts.appendleft(center)

			# loop over the set of tracked points
			for i in xrange(1, len(pts)):
				if pts[i - 1] is None or pts[i] is None:
					continue

				# otherwise, compute the thickness of the line and
				# draw the connecting lines
				thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
				cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

			# show the frame to our screen
			#cv2.imshow("Frame", frame)
			key = cv2.waitKey(1) & 0xFF

			# if the 'q' key is pressed, stop the loop
			if key == ord("q"):
				break

		# cleanup the camera and close any open windows
		camera.release()
		cv2.destroyAllWindows()


#Protects main from being run when imported and only run when executed.
#Runs main()
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exitapp = True
        raise
