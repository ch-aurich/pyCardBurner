from PySide import QtGui
from PySide import QtCore
import time
import signal
from subprocess import Popen, PIPE
import os

DEFAULT_STYLE = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}

QProgressBar::chunk {
    background-color: blue;
    width: 1px;
    margin: 0px;
}
"""

COMPLETED_STYLE = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}

QProgressBar::chunk {
    background-color: green;
    width: 1px;
    margin: 0px;
}
"""


class BurnerProgressThread(QtCore.QThread):
    FLASH_STATE_WAIT_FOR_INSERT = 0
    FLASH_STATE_FLASHING = 1
    FLASH_STATE_VERIFYING = 2
    FLASH_STATE_WAIT_FOR_REMOVAL = 3
    dataReady = QtCore.Signal(int)
    state     = QtCore.Signal(str)
    def __init__(self, deviceName, inputfile):
        QtCore.QThread.__init__(self)
        self.exiting = False
        self.deviceName = deviceName
        self.inputfile = inputfile
        self.filesize = os.path.getsize(inputfile)
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
                self.state.emit("wait for card insert")
                self.dataReady.emit(0)
                time.sleep(1)
            elif (self.flash_state == self.FLASH_STATE_FLASHING):
                self.state.emit("flashing...")
                english_env = dict(os.environ)
                english_env['LANG'] = "LANG=en_US.UTF-8"
                dd = Popen(['dd', 'of=' + self.deviceName, 'bs=1M', 'oflag=direct', 'if=' + self.inputfile], stderr=PIPE, env=english_env)
                while dd.poll() is None:
                    print self.deviceName + ": wait for dd end"
                    time.sleep(1)
                    print self.deviceName + ": wait for dd end"
                    dd.send_signal(signal.SIGUSR1)
                    print self.deviceName + ": sent signal SIGUSR1 to dd"
                    while 1:
                        time.sleep(.1)
                        print self.deviceName + ": in endless loop for reading stderr"
                        l = dd.stderr.readline()
                        print self.deviceName + l
                        if 'bytes' in l:
                            bytes_copied = l.split(' ')[0]
                            print self.deviceName + ": " + str(bytes_copied) + " of " + str(self.filesize) + " bytes copied so far"
                            self.dataReady.emit(99*int(bytes_copied)/self.filesize) #this will reach 99% as maximum
                            break
                
                #switch to next state
                #self.flash_state = self.FLASH_STATE_VERIFYING
                self.dataReady.emit(100)
                self.flash_state = self.FLASH_STATE_WAIT_FOR_REMOVAL
            #elif (self.flash_state == self.FLASH_STATE_VERIFYING):
            #    time.sleep(1)
            #    self.dataReady.emit(60)
            #    self.flash_state = self.FLASH_STATE_WAIT_FOR_REMOVAL
            elif (self.flash_state == self.FLASH_STATE_WAIT_FOR_REMOVAL):
                self.state.emit("wait for card removal")
                time.sleep(1)


class BurnerProgressWidget(QtGui.QWidget):
    def __init__(self, deviceName,inputfile):
        QtGui.QWidget.__init__(self)
        self.initUI(deviceName)
        self.deviceName = deviceName
        self.inputfile = inputfile

        self.thread = BurnerProgressThread(self.deviceName, self.inputfile)
        self.thread.dataReady.connect(self.setProgress, QtCore.Qt.QueuedConnection)
        self.thread.state.connect(self.setState, QtCore.Qt.QueuedConnection)
        self.thread.start()
    def drive_inserted(self):
        self.thread.drive_inserted()
    def drive_removed(self):
        self.thread.drive_removed()
    def setProgress(self,progress):
        print "setting progress"

        self.progress.setValue(progress)

        if (progress == 100):
          self.progress.setStyleSheet(COMPLETED_STYLE)
        else:
          self.progress.setStyleSheet(DEFAULT_STYLE)
    def setState(self, state):
        print "setting state"
        self.actionLabel.setText(state)
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

