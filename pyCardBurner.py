''' tool to mass flash SD (or other) mass storage cards '''
import dbus
#import gobject
from dbus.mainloop.glib import DBusGMainLoop
from PySide import QtGui
import sys

import BurnerProgressWidget

DBusGMainLoop(set_as_default=True)  #Inform that a main loop will be used


class WaitWindow(QtGui.QWidget):
    def __init__(self):
        super(WaitWindow, self).__init__()
        self.list = QtGui.QListWidget()
        self.initUI()

    def addDevice(self, name):
        new_item = QtGui.QListWidgetItem()
        new_item.setText(name)
        self.list.insertItem(0, new_item)

    def initUI(self):
        description = QtGui.QLabel("Plug in your SD cards" + \
                      "into the card readers now. Close this" + \
                      "window when you plugged in all cards." + \
                      "Detected cards will be listed below:")
        self.setWindowTitle('waiting...')
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(description)
        vbox.addWidget(self.list)
        self.setLayout(vbox)


class CardBurner(QtGui.QWidget):
    def __init__(self, imagefile, devices):
        ''' initializes the pyCardBurner object
        dev_list is the dictionary of device names to be used '''
        super(CardBurner, self).__init__()
        self.dev_list = devices
        self.inputfile = imagefile
        self.initUI()

    def closeEvent(self, event):
        ''' event for window close request (i.e. clicking on the X) '''
        if self.none_busy():
            print("stopping all threads for exit")
            self.stop_all()
            event.accept()
        else:
            print("ignoring users wish to close window, \
                   some card is not flashed yet")
            event.ignore()

    def stop_all(self):
        ''' method to tell all burner widgets to  stop their work '''
        for devicename, burner in self.dev_list.items():
            burner['burner'].stop()

    def none_busy(self):
        ''' find out if all burners are idle '''
        none_busy = True
        for devicename, burner in self.dev_list.items():
            if burner['burner'].is_busy() == True:
                none_busy = False
        return none_busy

    def udisks_device_changed(self, devPath, deviceName, deviceSize):
        ''' event (used as callback from udisks) to signalize
        the change of device properties '''
        if deviceSize == 0:
            if not self.dev_list[deviceName]['size'] == 0:
                self.dev_list[deviceName]['burner'].drive_removed()
                self.dev_list[deviceName]['size'] = 0
        else:
            if self.dev_list[deviceName]['size'] == 0:
                self.dev_list[deviceName]['burner'].drive_inserted()
                self.dev_list[deviceName]['size'] = deviceSize

    def initUI(self):
        ''' initialize the user interface '''
        self.burners = []
        self.setWindowTitle('pyCardBurner')

        hbox = QtGui.QHBoxLayout()
        index = 0
        for deviceName, deviceproperties in self.dev_list.items():
            self.burners. \
                append(BurnerProgressWidget.BurnerProgressWidget \
                           (deviceName, self.inputfile))
            hbox.addWidget(self.burners[index])
            self.dev_list[deviceName]['burner'] = self.burners[index]
            self.dev_list[deviceName]['burnerIndex'] = index
            index += 1

        self.setLayout(hbox)


def getMassStorageDevices(bus):
    dev_list = {}

    for dev in ud_manager.EnumerateDevices():
        device_obj = bus.get_object('org.freedesktop.UDisks', dev)
        device_props = dbus.Interface(device_obj, dbus.PROPERTIES_IFACE)
        deviceFile = str(device_props. \
                         Get('org.freedesktop.UDisks.Device', 'DeviceFile'))
        deviceSize = int(device_props. \
                         Get('org.freedesktop.UDisks.Device', 'DeviceSize'))
        deviceIsPartition = bool(device_props. \
                                 Get('org.freedesktop.UDisks.Device', \
                                     'DeviceIsPartition'))

        if not deviceIsPartition and deviceSize == 0:
            dev_list[deviceFile] = {'size': 0}

    return dev_list

def on_device_changed(dev_path):
    added_dev_obj = bus.get_object("org.freedesktop.UDisks", dev_path)
    #added_dev = dbus.Interface(added_dev_obj, 'org.freedesktop.UDisks')
    added_dev_props = dbus.Interface(added_dev_obj, dbus.PROPERTIES_IFACE)
    deviceFile = str(added_dev_props. \
                     Get('org.freedesktop.UDisks.Device', "DeviceFile"))
    deviceSize = int(added_dev_props. \
                     Get('org.freedesktop.UDisks.Device', "DeviceSize"))
    deviceIsPartition = bool(added_dev_props. \
                             Get('org.freedesktop.UDisks.Device', \
                                 "DeviceIsPartition"))

    if learningmode == True:
        if deviceFile in dev_list \
                and not deviceIsPartition \
                and int(deviceSize) > 0 \
                and dev_list[deviceFile]['size'] == 0:
            dev_list[deviceFile]['size'] = deviceSize
            print("added " + deviceFile + " to the list of used devices")
            waitwindow.addDevice(deviceFile)
    else:
        if deviceFile in dev_list and not deviceIsPartition:
            pdb.udisks_device_changed(dev_path, deviceFile, deviceSize)


raw_input("Connect all your card readers without SD cards inserted and" + \
           "press Enter to start the learning phase")
learningmode = True
bus = dbus.SystemBus()
ud_manager_obj = bus.get_object('org.freedesktop.UDisks', \
                                '/org/freedesktop/UDisks')
ud_manager = dbus.Interface(ud_manager_obj, 'org.freedesktop.UDisks')
ud_manager.connect_to_signal('DeviceChanged', on_device_changed)

dev_list = getMassStorageDevices(bus)

app = QtGui.QApplication(sys.argv)
waitwindow = WaitWindow()
waitwindow.show()
app.exec_()

learningmode = False

for dev, val in dev_list.items():
    if val['size'] == 0:
        dev_list.pop(dev)

inputfile = str(sys.argv[1])

pdb = CardBurner(inputfile, dev_list)
pdb.show()
sys.exit(app.exec_())
