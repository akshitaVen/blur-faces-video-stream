import av
import cv2
import time

# Load the pre-trained face detection model (Haar cascade)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Open the USB webcam with PyAV
try:
    input_container = av.open('/dev/video0')
    print("[INFO] Opened video source /dev/video0")
except Exception as e:
    print(f"[ERROR] Failed to open video source: {e}")
    exit(1)

# Create an output container for the virtual camera (explicitly specifying v4l2 format)
try:
    output_container = av.open('/dev/video15', mode='w', format='v4l2')
    print("[INFO] Opened virtual camera output /dev/video15")
except Exception as e:
    print(f"[ERROR] Failed to open virtual camera output: {e}")
    exit(1)

# Define the video stream properties for the virtual camera
try:
    # stream = output_container.add_stream('mjpeg', rate=60)  # Set frame rate h264
    stream = output_container.add_stream('mjpeg', rate=60) 
    stream.width = 1920
    stream.height = 1080
    stream.pix_fmt = 'yuvj422p'  # MJPEG often works with yuvj422p
    print("[INFO] Stream setup complete with resolution 640x480 and pixel format yuvj422p")
except Exception as e:
    print(f"[ERROR] Failed to add video stream: {e}")
    exit(1)

# Frame rate control (to ensure we process in real-time)
frame_interval = 1.0 / 30.0  # Target 30 FPS
last_frame_time = time.time()

frame_count = 0

try:
    # Log: Start the decoding loop
    print("[INFO] Starting video processing loop")
    
    for frame in input_container.decode(video=0):
        current_time = time.time()
        frame_count += 1
        
        # Log: Check if frame is received
        print(f"[INFO] Processing frame {frame_count} at time {current_time}")

        # Convert frame to numpy array
        try:
            img = frame.to_ndarray(format='bgr24')
            print(f"[INFO] Successfully converted frame {frame_count} to BGR format")
        except Exception as e:
            print(f"[ERROR] Failed to convert frame {frame_count} to BGR format: {e}")
            continue

        # Convert the image to grayscale for face detection
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            print(f"[INFO] Successfully converted frame {frame_count} to grayscale for face detection")
        except Exception as e:
            print(f"[ERROR] Failed to convert frame {frame_count} to grayscale: {e}")
            continue

        # Detect faces
        try:
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            print(f"[INFO] Detected {len(faces)} faces in frame {frame_count}")
        except Exception as e:
            print(f"[ERROR] Failed to detect faces in frame {frame_count}: {e}")
            continue

        # Blur detected faces
        try:
            for (x, y, w, h) in faces:
                face = img[y:y+h, x:x+w]
                blurred_face = cv2.GaussianBlur(face, (99, 99), 30)
                img[y:y+h, x:x+w] = blurred_face
            print(f"[INFO] Successfully blurred faces in frame {frame_count}")
        except Exception as e:
            print(f"[ERROR] Failed to blur faces in frame {frame_count}: {e}")
            continue

        # Convert the BGR image to MJPEG-compatible format (YUV format)
        try:
            video_frame = av.VideoFrame.from_ndarray(img, format='bgr24')
            print(f"[INFO] Created VideoFrame from numpy array for frame {frame_count}")
        except Exception as e:
            print(f"[ERROR] Failed to create VideoFrame for frame {frame_count}: {e}")
            continue

        # Encode the frame and write to the virtual camera
        try:
            packets = stream.encode(video_frame)
            for packet in packets:
                output_container.mux(packet)
            print(f"[INFO] Successfully encoded and muxed frame {frame_count}")
        except Exception as e:
            print(f"[ERROR] Failed to encode or mux frame {frame_count}: {e}")
            continue

        # Display the frame for debugging (Optional)
        # try:
        #     cv2.imshow('Video with Face Blur', img)
        #     if cv2.waitKey(1) & 0xFF == 27:  # Press ESC to exit
        #         print("[INFO] Exiting video loop on user command")
        #         break
        # except Exception as e:
        #     print(f"[ERROR] Failed to display frame {frame_count}: {e}")

        # Frame rate control to avoid overloading the virtual camera
        elapsed_time = time.time() - last_frame_time
        if elapsed_time < frame_interval:
            time.sleep(frame_interval - elapsed_time)
        last_frame_time = time.time()

        # Log: Frame processed successfully
        print(f"[INFO] Frame {frame_count} processed successfully")

except Exception as e:
    print(f"[ERROR] Fatal error during video processing: {e}")
finally:
    # Log: Exit loop or finalization
    print("[INFO] Finalizing: Closing all resources")
    
    # Flush the stream and close resources
    try:
        packets = stream.encode(None)  # Flush encoder
        for packet in packets:
            output_container.mux(packet)
        print("[INFO] Flushed the stream")
    except Exception as e:
        print(f"[ERROR] Failed to flush the stream: {e}")

    input_container.close()
    output_container.close()
    cv2.destroyAllWindows()
    print("[INFO] Closed all resources")

