''' Qt (PySide) Widget that can be used to flash SD cards with a progressbar '''
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
    ''' Qt Thread that handles the actual work to write to the driver '''
    FLASH_STATE_WAIT_FOR_INSERT = 0
    FLASH_STATE_FLASHING = 1
    FLASH_STATE_VERIFYING = 2
    FLASH_STATE_WAIT_FOR_REMOVAL = 3
    dataReady = QtCore.Signal(int)
    state     = QtCore.Signal(str)
    def __init__(self, deviceName, inputfile):
        ''' initialization of the thread '''
        QtCore.QThread.__init__(self)
        self.exiting = False
        self.deviceName = deviceName
        self.inputfile = inputfile
        self.filesize = os.path.getsize(inputfile)
        self.flash_state = 1
    def is_busy(self):
        ''' request if the burner process is in progress or in a wait state '''
        if self.flash_state == self.FLASH_STATE_WAIT_FOR_INSERT or \
           self.flash_state == self.FLASH_STATE_WAIT_FOR_REMOVAL:
            return False
        else:
            return True
    def drive_inserted(self):
        ''' notify thread that a card has been inserted into the drive '''
        #TODO: error handling!, check preconditions
        self.flash_state = 1
    def drive_removed(self):
        ''' notify thread that a card has been removed from the drive '''
        #TODO: error handling!, check preconditions
        self.flash_state = 0
    def run(self):
        ''' 
        endless running function with state machine for handling the flash 
        process
        '''
        while self.exiting == False:
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
                dd_process = Popen(['dd', 'of=' + self.deviceName, \
                                    'bs=1M', 'oflag=direct', \
                                    'if=' + self.inputfile], \
                                    stderr=PIPE, env=english_env)
                while dd_process.poll() is None:
                    print self.deviceName + ": wait for dd end"
                    time.sleep(1)
                    print self.deviceName + ": wait for dd end"
                    dd_process.send_signal(signal.SIGUSR1)
                    print self.deviceName + ": sent signal SIGUSR1 to dd"
                    while 1:
                        time.sleep(.1)
                        print self.deviceName + \
                               ": in endless loop for reading stderr"
                        dd_line = dd_process.stderr.readline()
                        print self.deviceName + dd_line
                        if 'bytes' in dd_line:
                            bytes_copied = dd_line.split(' ')[0]
                            print self.deviceName + ": " + str(bytes_copied) +\
                                   " of " + str(self.filesize) + \
                                   " bytes copied so far"
                            #the following calculation will reach 99% as maximum
                            self.dataReady.emit(99*int(bytes_copied) \
                                                / self.filesize)
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
    '''
    Qt (PySide) Widget that can be used to flash SD cards with a progressbar
    '''
    def __init__(self, deviceName, inputfile):
        ''' initialization of the widget '''
        QtGui.QWidget.__init__(self)

        self.actionLabel = None
        self.progress = None
        self.deviceNameLabel = None

        self.initUI(deviceName)
        self.deviceName = deviceName
        self.inputfile = inputfile

        self.thread = BurnerProgressThread(self.deviceName, self.inputfile)
        self.thread.dataReady.connect(self.setProgress, \
                                      QtCore.Qt.QueuedConnection)
        self.thread.state.connect(self.setState, QtCore.Qt.QueuedConnection)
        self.thread.start()
    def is_busy(self):
        ''' request if the burner process is in progress or in a wait state '''
        return self.thread.is_busy()
    def stop(self):
        ''' 
        marks the thread to stop whenever it reaches the next wait 
        state and waits for the thread to finish
        '''
        self.thread.exiting = True
        #wait for thread to end
        while(self.thread.isRunning()):
            time.sleep(.1)
    def drive_inserted(self):
        ''' notify the widget that a card has been inserted into the drive '''
        self.thread.drive_inserted()
    def drive_removed(self):
        ''' notify the widget that a card has been removed from the drive '''
        self.thread.drive_removed()
    def setProgress(self, progress):
        '''
        slot to set the progress of the widget - i.e. what is the displayed 
        progress of the progressbar
        '''
        print "setting progress"

        self.progress.setValue(progress)

        if (progress == 100):
            self.progress.setStyleSheet(COMPLETED_STYLE)
        else:
            self.progress.setStyleSheet(DEFAULT_STYLE)
    def setState(self, state):
        ''' slot to set the description of the current state '''
        print "setting state"
        self.actionLabel.setText(state)
    def initUI(self, deviceName):
        ''' method to initialize the user interface '''
        deviceNameDescriptionLabel = QtGui.QLabel("Device:")
        self.deviceNameLabel = QtGui.QLabel(deviceName)
        actionDescriptionLabel = QtGui.QLabel("Action:")
        self.actionLabel = QtGui.QLabel("Waiting for device")

        progressLabel = QtGui.QLabel("Progress:")
        self.progress = QtGui.QProgressBar()
        self.progress.setMinimum = 0
        self.progress.setMaximum = 100

        frame = QtGui.QFrame()
        frame.setFrameStyle(QtGui.QFrame.Panel)
        frame.setLineWidth(2)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(deviceNameDescriptionLabel, 0, 0)
        layout.addWidget(self.deviceNameLabel, 0, 1)
        layout.addWidget(actionDescriptionLabel, 1, 0)
        layout.addWidget(self.actionLabel, 1, 1)
        layout.addWidget(progressLabel, 2, 0)
        layout.addWidget(self.progress, 2, 1)

        frame.setLayout(layout)

        layout2 = QtGui.QHBoxLayout()
        layout2.addWidget(frame)
        self.setLayout(layout2)

