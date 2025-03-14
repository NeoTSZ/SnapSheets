from PyQt6.QtCore import Qt as qt
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMainWindow, QFileDialog
from PyQt6.QtGui import QPixmap, QImage
import sys
import styles as ss
import image_processor as ip
import cv2 as cv
from PIL import Image
import os

message1 = '''Welcome to SnapSheets!
'''
message2 = '''With this application, you can take images and convert them into PDFs, hassle free.

Choose an option on the right to begin.  '''
message3 = '''No contours found.
No pages found.'''

class WebcamHandler(QThread):
    updateFrame = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True

    def getFrames(self, interface):
        '''
        Grabs, processes, and projects frames as time goes on.
        '''

        capture = cv.VideoCapture(0)
        # Grabbing webcam frames continuously.
        while self.running == True and capture.isOpened():
            # Grabbing a single frame.
            returnTrigger, frame = capture.read()
            if returnTrigger == False:
                break

            # Processing the frame.
            imageSet = ip.processImage(frame)
            contours = imageSet['contours']
            original = imageSet['original']

            # Displaying contours only when found.
            if isinstance(contours, bool):
                interface.showImage(original)
            else:
                interface.showImage(contours)
                interface.validImage = imageSet
                interface.captureFlag = True
            cv.waitKey(1)
        capture.release()
        cv.destroyAllWindows()

class Interface(QMainWindow):
    def __init__(self):
        '''Initializes the interface window.'''

        # Creating the application instance.
        super().__init__()
        self.validImage = None
        self.camHandler = None
        self.captureFlag = False
        self.setWindowTitle('SnapSheets!')
        self.loadUI()

    def loadUI(self):
        '''
        Loads the starting page.
        '''

        # Preparing the layouts.
        self.welcomeBox = QVBoxLayout()
        self.buttonBox = QVBoxLayout()
        self.previewBox = QHBoxLayout()
        self.headerBox = QVBoxLayout()
        self.master = QHBoxLayout()

        # Preparing the welcome message.
        self.welcome = QLabel(message1)
        self.welcome.setObjectName('welcome')
        self.welcome.adjustSize()
        self.info = QLabel(message2)
        self.info.adjustSize()
        self.welcomeBox.addWidget(self.welcome)
        self.welcomeBox.addWidget(self.info)

        # Preparing the buttons.
        self.upload = QPushButton('Upload a file.')
        self.webcam = QPushButton('Open your webcam.')
        self.clip = QPushButton('Capture with webcam.')
        self.nocam = QPushButton('Close your webcam.')
        self.convert = QPushButton('Convert to PDF.')
        self.upload.clicked.connect(self.exploreImage)
        self.webcam.clicked.connect(self.openCam)
        self.nocam.clicked.connect(self.closeCam)
        self.clip.clicked.connect(self.clipCam)
        self.convert.clicked.connect(self.makePDF)
        self.buttonBox.addWidget(self.upload)
        self.buttonBox.addWidget(self.webcam)
        self.buttonBox.addWidget(self.nocam)
        self.buttonBox.addWidget(self.clip)

        # Preparing more buttons.
        self.contours = QPushButton('View contours.')
        self.straight = QPushButton('View the page only.')
        self.buttonBox.addWidget(self.contours)
        self.buttonBox.addWidget(self.straight)
        self.buttonBox.addWidget(self.convert)

        # Setting the header.
        self.headerBox.addLayout(self.welcomeBox)
        self.headerBox.addLayout(self.previewBox)

        # Preparing the preview box.
        self.preview = QLabel('Nothing to preview.')
        self.previewInfo = QLabel('No image in preview.')
        self.preview.setObjectName('preview')
        self.preview.adjustSize()
        self.previewBox.addWidget(self.preview)
        self.buttonBox.addWidget(self.previewInfo)

        # Preparing the master layout.
        self.masterWidget = QWidget()
        self.master.addLayout(self.headerBox)
        self.master.addLayout(self.buttonBox)
        self.masterWidget.setLayout(self.master)
        self.masterWidget.setStyleSheet(ss.allStyles)
        self.setCentralWidget(self.masterWidget)

    def showImage(self, image):
        '''
        Shows an image of OpenCV type.
        '''

        # Getting image dimensions and scaling.
        height, width, depth = image.shape
        aspectRatio = width / height
        lineBytes = depth * width
        qOriginal = QImage(
            image.data,
            width, height, lineBytes, QImage.Format.Format_RGB888
        )
        targetHeight = 660
        targetWidth = int(aspectRatio * targetHeight)
        qMap = QPixmap.fromImage(qOriginal)
        qMap = qMap.scaled(
            targetWidth,
            targetHeight
        )
        self.preview.setMinimumSize(
            targetWidth,
            targetHeight
        )
        self.preview.setPixmap(qMap)

    def openImage(self):
        '''
        Scales the loaded image and puts it within the label.
        '''

        # Checking for the validity of the chosen image.
        image = cv.imread(self.path)
        imageSet = ip.processImage(image)
        validFlag = False

        original = imageSet['original']
        contours = imageSet['contours']
        straight = imageSet['straight']

        # Checking the imageSet.
        if isinstance(contours, bool) or isinstance(contours, bool):
            self.previewInfo.setText(message3)
        else:
            self.previewInfo.setText('Image loaded.')
            validFlag = True

        self.showImage(original)

        # Leaving the function if nothing can be done.
        if validFlag == False:
            return

        self.captureFlag = False

        # Enabling options for other image variants.
        self.contours.clicked.connect(lambda: self.showImage(contours))
        self.straight.clicked.connect(lambda: self.showImage(straight))

        # Saving the straightened image.
        self.validImage = imageSet

    def exploreImage(self):
        '''
        Enables the user to explore File Explorer.
        '''

        # Loading the file and filtering the different possibilities.
        self.path, _ = QFileDialog.getOpenFileName(
            self.preview,
            'Select an image.'
        )
        if self.path == '':
            self.previewInfo.setText('Image picking cancelled.')
        elif '.png' not in self.path and '.jpg' not in self.path and '.jpeg' not in self.path:
            self.previewInfo.setText('Invalid file type chosen.')
        else:
            self.openImage()

    def openCam(self):
        '''
        Enables the camera.
        '''

        if self.camHandler == None or self.camHandler.running == False:
            self.webcam.setText('Disable webcam.')
            self.previewInfo.setText('The webcam is live.')
            self.camHandler = WebcamHandler()
            self.camHandler.getFrames(self)

    def closeCam(self):
        '''
        Disables the camera.
        '''

        # Checking if any valid image was ever caught.
        if self.camHandler == None:
            return

        if self.camHandler != None or self.camHandler.running == True:
            # Resetting and closing all sorts of things.
            self.webcam.setText('Use your webcam.')
            self.previewInfo.setText('The webcam was disabled.')
            self.camHandler.running = False
            self.camHandler.terminate()
            self.camHandler.wait()
            self.preview.setText('Nothing to preview.')
            cv.destroyAllWindows()
            self.preview.setMinimumHeight(200)
            self.preview.setMinimumWidth(200)

    def clipCam(self):
        '''
        Clips a webcam image.
        '''

        # Checking if any valid image was ever caught.
        if self.validImage == None or self.camHandler == None or self.captureFlag == False:
            return

        if self.camHandler != None or self.camHandler.running == True:
            # Showing the image.
            self.closeCam()
            self.showImage(self.validImage['contours'])

            # Enabling options for other image variants.
            self.contours.clicked.connect(lambda: self.showImage(self.validImage['contours']))
            self.straight.clicked.connect(lambda: self.showImage(self.validImage['straight']))

    def makePDF(self):
        '''
        Generates and outputs a PDF.
        '''

        # Checking if there is an image to convert.
        if self.validImage == None:
            return

        # Temporarily outputting the image before conversion.
        output = cv.cvtColor(self.validImage['straight'], cv.COLOR_RGB2BGR)
        cv.imwrite('pdf_conversion_temp.png', output)
        temp = Image.open('pdf_conversion_temp.png')
        temp.convert('RGB').save('output.pdf')
        os.remove('pdf_conversion_temp.png')
        self.previewInfo.setText('PDF generated!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    interface = Interface()
    interface.show()
    app.exec()