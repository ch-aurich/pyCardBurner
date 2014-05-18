import dbus
#import gobject
from dbus.mainloop.glib import DBusGMainLoop
from PySide import QtGui
import sys
import time


import BurnerProgressWidget

DBusGMainLoop(set_as_default=True) #Inform that a main loop will be used

class waitWindow(QtGui.QWidget):
    def __init__(self):
        super(waitWindow, self).__init__()
        self.initUI()
    def initUI(self):    
        self.setWindowTitle('waiting...')

        hbox = QtGui.QHBoxLayout()
        self.setLayout(hbox)
        

class pyDiskBurner(QtGui.QWidget):
    
    def __init__(self, inputfile, dev_list):
        ''' initializes the pyDiskBurner object
        number is the number of burner slots '''
        super(pyDiskBurner, self).__init__()
        self.dev_list = dev_list
        self.inputfile = inputfile
        self.initUI()

    def udisks_device_changed(self, deviceName, deviceSize):
        if(deviceSize == 0):
            self.dev_list[deviceName]['burner'].drive_removed()
        else:
            self.dev_list[deviceName]['burner'].drive_inserted()

    def initUI(self):    
        self.burners = []
        self.setWindowTitle('pyDiskBurner')

        hbox = QtGui.QHBoxLayout()
        index = 0
        for deviceName, deviceproperties in self.dev_list.items():
            self.burners.append(BurnerProgressWidget.BurnerProgressWidget(deviceName, self.inputfile))
            hbox.addWidget(self.burners[index])
            self.dev_list[deviceName]['burner'] = self.burners[index]
            self.dev_list[deviceName]['burnerIndex'] = index
            index += 1

        self.setLayout(hbox)


def on_device_changed(dev_path):
    added_dev_obj = bus.get_object("org.freedesktop.UDisks", dev_path)
    added_dev = dbus.Interface(added_dev_obj, 'org.freedesktop.UDisks')
    added_dev_props = dbus.Interface(added_dev_obj, dbus.PROPERTIES_IFACE)
    deviceFile = str(added_dev_props.Get('org.freedesktop.UDisks.Device', "DeviceFile"))
    deviceSize = int(added_dev_props.Get('org.freedesktop.UDisks.Device', "DeviceSize"))
    deviceIsPartition = bool(added_dev_props.Get('org.freedesktop.UDisks.Device', "DeviceIsPartition"))

    if (learningmode == True):
        if (deviceFile in dev_list and not deviceIsPartition and int(deviceSize) > 0 and dev_list[deviceFile]['size'] == 0):
            dev_list[deviceFile]['size'] = deviceSize
            print ("added " + deviceFile + " to the list of used devices")
    else:
        if (deviceFile in dev_list and not deviceIsPartition):
            pdb.udisks_device_changed(dev_path, deviceSize)


raw_input("Connect all your card readers without SD cards inserted and press Enter to start the learning phase")
learningmode = True
bus = dbus.SystemBus()
ud_manager_obj = bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.UDisks')
ud_manager.connect_to_signal('DeviceChanged', on_device_changed)

dev_list = {}

for dev in ud_manager.EnumerateDevices():
    device_obj = bus.get_object("org.freedesktop.UDisks", dev)
    device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
    deviceFile = str(device_props.Get('org.freedesktop.UDisks.Device', "DeviceFile"))
    deviceSize = int(device_props.Get('org.freedesktop.UDisks.Device', "DeviceSize"))
    deviceIsPartition = bool(device_props.Get('org.freedesktop.UDisks.Device', "DeviceIsPartition"))

    if (not deviceIsPartition and deviceSize == 0):
        dev_list[deviceFile] = {'size': 0}

app = QtGui.QApplication(sys.argv)
waitwindow = waitWindow()
waitwindow.show()
app.exec_()

#raw_input("Now Insert cards in each card reader that should be used, press enter to finish the learning phase")
learningmode = False

for dev, val in dev_list.items():
    if val['size'] == 0:
        dev_list.pop(dev)

inputfile = str(sys.argv[1])

pdb = pyDiskBurner(inputfile, dev_list)
pdb.show()
sys.exit(app.exec_())
