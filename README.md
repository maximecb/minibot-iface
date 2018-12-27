# minibot-iface

Remote control interface for the MiniWorld robot. The robot uses a Raspberri Pi 3 B+, the camera module V2, an [Adafruit motor hat](https://www.adafruit.com/product/2348) and two differential drive motors.

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
sudo apt-get install -y python3-pip python3-picamera python3-smbus i2c-tools libatlas-base-dev

pip3 install numpy zmq scipy==1.1.0

# Adafruit motor controller library
git clone https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library.git
cd Adafruit-Motor-HAT-Python-Library
pip3 install --trusted-host pypi.python.org --user -e .
```

To enable I2C ports, you should uncomment the necessary line in `/boot/config.txt`, and add a line with `i2c-dev` to `/etc/modules`.

# Troubleshooting

Note that some Python packages can take forever to build and install with pip. It's worth consulting the list of available precompiled wheels on [piwheels](https://www.piwheels.hostedpi.com/packages.html), and specifying to install a package version that you know has a precompiled wheel.
