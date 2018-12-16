# minibot-iface
Remote control interface for the MiniWorld robot (Raspberri Pi 3 B+, camera module V2)

Dependencies:
- Python 3
- NumPy
- pyzmq (https://pyzmq.readthedocs.io)
- picamera library (https://picamera.readthedocs.io)
- Adafruit motor hat library (https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library)
- scipy (for image resizing)

Installing the dependencies:
```
# Picamera (may already be installed on raspbian distro)
sudo apt-get update
sudo apt-get install python3-picamera

pip3 install numpy zmq scipy

# Adafruit motor controller library
git clone https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library.git
cd Adafruit-Motor-HAT-Python-Library
pip3 install --trusted-host pypi.python.org --user -e .
```
