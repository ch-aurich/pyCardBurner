from PySide import QtGui
from PySide import QtCore
import time
import signal
from subprocess import Popen, PIPE


class BurnerProgressThread(QtCore.QThread):
    FLASH_STATE_WAIT_FOR_INSERT = 0
    FLASH_STATE_FLASHING = 1
    FLASH_STATE_VERIFYING = 2
    FLASH_STATE_WAIT_FOR_REMOVAL = 3
    dataReady = QtCore.Signal(int)
    def __init__(self, deviceName, inputfile):
        QtCore.QThread.__init__(self)
        self.exiting = False
        self.deviceName = deviceName
        self.inputfile = inputfile
        self.flash_state = 1
    def drive_inserted(self):
        #TODO: error handling!, check preconditions
        self.flash_state = 1
    def drive_removed(self):
        #TODO: error handling!, check preconditions
        self.flash_state = 0
    def run(self):
        while self.exiting==False:
            #wait for card to be inserted
            if (self.flash_state == self.FLASH_STATE_WAIT_FOR_INSERT):
                print("wait for insert")
                time.sleep(1)
            elif (self.flash_state == self.FLASH_STATE_FLASHING):
                dd = Popen(['dd', 'of=' + self.deviceName, 'bs=1M', 'if=' + self.inputfile], stderr=PIPE)
                while dd.poll() is None:
                    time.sleep(1)
                    print "in wait for dd end"
                    dd.send_signal(signal.SIGUSR1)
                    while 1:
                        l = dd.stderr.readline()
                        if 'records in' in l:
                            print l[:l.index('+')], 'records',
                        if 'bytes' in l:
                            print l.strip(), '\r',
                            break

                print("flashing - 0")
                self.dataReady.emit(0)

                #run dd
                #verification
                #switch to next state
                self.flash_state = self.FLASH_STATE_VERIFYING
            elif (self.flash_state == self.FLASH_STATE_VERIFYING):
                time.sleep(1)
                print("verifying - 60")
                time.sleep(1)
                print("verifying - 70")
                time.sleep(1)
                print("verifying - 80")
                time.sleep(1)
                print("verifying - 90")
                time.sleep(1)
                print("verifying - 100")
                self.flash_state = self.FLASH_STATE_WAIT_FOR_REMOVAL
            elif (self.flash_state == self.FLASH_STATE_WAIT_FOR_REMOVAL):
                time.sleep(1)


class BurnerProgressWidget(QtGui.QWidget):
    def __init__(self, deviceName,inputfile):
        QtGui.QWidget.__init__(self)
        self.initUI(deviceName)
        self.deviceName = deviceName
        self.inputfile = inputfile

        self.thread = BurnerProgressThread(self.deviceName, self.inputfile)
        self.thread.dataReady.connect(self.setProgress, QtCore.Qt.QueuedConnection)
        self.thread.start()
    def drive_inserted(self):
        self.thread.drive_inserted()
    def drive_removed(self):
        self.thread.drive_removed()
    def setProgress(self,progress):
        print "setting progress"
        self.progress.setValue(progress)
    def initUI(self, deviceName):
        deviceNameDescriptionLabel = QtGui.QLabel("Device:")
        self.deviceNameLabel = QtGui.QLabel(deviceName)
        actionDescriptionLabel = QtGui.QLabel("Action:")
        self.actionLabel = QtGui.QLabel("Waiting for device")

        progressLabel = QtGui.QLabel("Progress:")
        self.progress = QtGui.QProgressBar()
        self.progress.setMinimum=0
        self.progress.setMaximum=100

        frame = QtGui.QFrame()
        frame.setFrameStyle(QtGui.QFrame.Panel)
        frame.setLineWidth(2)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(deviceNameDescriptionLabel, 0, 0)
        layout.addWidget(self.deviceNameLabel, 0,1)
        layout.addWidget(actionDescriptionLabel, 1, 0)
        layout.addWidget(self.actionLabel, 1, 1)
        layout.addWidget(progressLabel, 2, 0)
        layout.addWidget(self.progress, 2, 1)

        frame.setLayout(layout)

        layout2 = QtGui.QHBoxLayout()
        layout2.addWidget(frame)
        self.setLayout(layout2)

