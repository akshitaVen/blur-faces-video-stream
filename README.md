# blur-faces-video-stream
Output svideo to /dev/video15 in MJPEG format. 

To set up v4l2 Virtual camera:

sudo apt update
sudo apt install v4l2loopback-dkms v4l2loopback-utils

sudo modprobe -r v4l2loopback  # Remove existing v4l2loopback module
sudo modprobe v4l2loopback video_nr=15 card_label="Blurred video" exclusive_caps=1

ls /dev/video*
