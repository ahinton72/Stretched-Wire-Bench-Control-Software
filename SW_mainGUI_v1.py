from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QMutex
from PyQt5.QtWidgets import QFileDialog
from SW_GUI_prototype_PM1000 import Ui_MainWindow  # import MainWindow created from designer and exported to .py file

import motor_controller_PM1000
import traceback, sys
import numpy as np
import csv
import time
import re
import datetime
import serial
from os.path import exists
from SWPositionsWorker import PositionsWorker
from SWRelativeMoveWorker1 import RelativeMoveWorker1
from SWRelativeMoveWorker2 import RelativeMoveWorker2
from SWGlobalMoveWorker1 import GlobalMoveWorker1
from SWGlobalMoveWorker2 import GlobalMoveWorker2
from SWsetMotorSettings import setMotorSettingsWorker
from SW_x_syncWorker import x_syncWorker
from SW_y_syncWorker import y_syncWorker
from SW_theta_syncWorker import theta_syncWorker


mc = motor_controller_PM1000.MotorController()
x1 = mc.axis['fc x1']
y1 = mc.axis['fc y1']
x2 = mc.axis['fc x2']
y2 = mc.axis['fc y2']
z2 = mc.axis['fc z2']
theta1 = mc.axis['fc theta 1']
theta2 = mc.axis['fc theta 2']

class mywindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.version_label.setText('Magnet Lab Controls - Stretched Wire v1.0')

        self.ui.tabWidget.tabBarClicked.connect(self.sleepGUI)  # sleep GUI

        # Infinite Loop for continuously updating probe position and field measurements
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(False)
        self.timer.setInterval(500)  # in milliseconds, so 5000 = 5 seconds
        # self.timer.timeout.connect(self.update_current_measurements)
        self.timer.timeout.connect(self.ReadPositions)  # connect timer to read positions function
        self.timer.start()

        # Connect Radio buttons on movement tab to MovementRadio function
        self.ui.relativeRadio.toggled.connect(self.movement_radio)  # connect relative movement radio button to function
        self.ui.globalRadio.toggled.connect(self.movement_radio)  # connect global movement radio button to function
        self.ui.relativeRadio.toggled.connect(self.sleepGUI)  # connect relative movement radio button to sleep function
        self.ui.globalRadio.toggled.connect(self.sleepGUI)

        # Connect Push Buttons on Movement Tab to functions to execute movement
        self.ui.stage1_relativemoveButton.clicked.connect(
            self.stage1_relative_move_click)  # Connect relative move push button to function
        self.ui.stage1_globalmoveButton.clicked.connect(
            self.stage1_global_move_click)  # connect global move push button to function
        self.ui.stage2_relativemoveButton.clicked.connect(
            self.stage2_relative_move_click)  # Connect relative move push button to function
        self.ui.stage2_globalmoveButton.clicked.connect(
            self.stage2_global_move_click)  # connect global move push button to function

        self.ui.x_sync_pushButton.clicked.connect(self.x_sync_move_click)
        self.ui.y_sync_pushButton.clicked.connect(self.y_sync_move_click)
        self.ui.theta_sync_pushButton.clicked.connect(self.theta_sync_move_click)

        # Connect push buttons on motor settings tab
        self.ui.motorsettingsButton.clicked.connect(self.motor_settings_click)

        self.position_labels = [self.ui.stage1_x_label, self.ui.stage1_y_label,
                                self.ui.stage2_x_label, self.ui.stage2_y_label, self.ui.stage2_z_label,
                                self.ui.stage1_theta_label, self.ui.stage2_theta_label] # list of position labels


        """

        # Second timer for updating settings
        self.timer2 = QtCore.QTimer(self)
        self.timer2.setSingleShot(False)
        self.timer2.setInterval(5000)  # in milliseconds, so 5000 = 5 seconds
        self.timer2.timeout.connect(self.ReadProbeSettings)  # connect timer to read probe settings function
        # self.timer2.timeout.connect(self.ReadMotorSettings)  ###Connect timer to read motor settings function
        self.timer2.start()

        # Connect Radio buttons on movement tab to MovementRadio function
        self.ui.relativeRadio.toggled.connect(self.movement_radio)  # connect relative movement radio button to function
        self.ui.globalRadio.toggled.connect(self.movement_radio)  # connect global movement radio button to function
        self.ui.relativeRadio.toggled.connect(self.sleepGUI)  # connect relative movement radio button to sleep function
        self.ui.globalRadio.toggled.connect(self.sleepGUI)

        

        # Connect buttons to zero position to functions
        self.ui.xzeroButton.clicked.connect(self.x_zero_click)
        self.ui.yzeroButton.clicked.connect(self.y_zero_click)
        self.ui.zzeroButton.clicked.connect(self.z_zero_click)

        # Connect fixed point radio buttons on scan tab to the functions to block out line edits
        self.ui.xplaneRadio.toggled.connect(self.fixed_x_radio)
        self.ui.yplaneRadio.toggled.connect(self.fixed_y_radio)
        self.ui.zplaneRadio.toggled.connect(self.fixed_z_radio)
        self.ui.xplaneRadio.toggled.connect(self.sleepGUI)
        self.ui.yplaneRadio.toggled.connect(self.sleepGUI)
        self.ui.zplaneRadio.toggled.connect(self.sleepGUI)

        # Connect radio buttons on motor settings page
        self.ui.xlimRadio.toggled.connect(self.xlimitRadio)
        self.ui.ylimRadio.toggled.connect(self.ylimitRadio)
        self.ui.zlimRadio.toggled.connect(self.zlimitRadio)
        self.ui.xlimRadio.toggled.connect(self.sleepGUI)
        self.ui.ylimRadio.toggled.connect(self.sleepGUI)
        self.ui.zlimRadio.toggled.connect(self.sleepGUI)

        """

        # Initialise motor settings page
        self.axes = [x1, y1, x2, y2, z2, theta1, theta2]
        self.speed_labels = [self.ui.x1speedLabel, self.ui.y1speedLabel,
                             self.ui.x2speedLabel, self.ui.y2speedLabel, self.ui.z2speedLabel,
                             self.ui.theta1speedLabel, self.ui.theta2speedLabel]
        self.speed_edits = [self.ui.x1speedEdit, self.ui.y1speedEdit,
                            self.ui.x2speedEdit, self.ui.y2speedEdit, self.ui.z2speedEdit,
                            self.ui.theta1speedEdit, self.ui.theta2speedEdit]
        self.lower_labels = [self.ui.x1lowerLabel, self.ui.y1lowerLabel,
                             self.ui.x2lowerLabel, self.ui.y2lowerLabel, self.ui.z2lowerLabel,
                             self.ui.theta1lowerLabel, self.ui.theta2lowerLabel]
        self.lower_edits = [self.ui.x1lowerEdit, self.ui.y1lowerEdit,
                            self.ui.x2lowerEdit, self.ui.y2lowerEdit, self.ui.z2lowerEdit,
                            self.ui.theta1lowerEdit, self.ui.theta2lowerEdit]
        self.upper_labels = [self.ui.x1upperLabel, self.ui.y1upperLabel,
                             self.ui.x2upperLabel, self.ui.y2upperLabel, self.ui.z2upperLabel,
                             self.ui.theta1upperLabel, self.ui.theta2upperLabel]
        self.upper_edits = [self.ui.x1upperEdit, self.ui.y1upperEdit,
                            self.ui.x2upperEdit, self.ui.y2upperEdit, self.ui.z2upperEdit,
                            self.ui.theta1upperEdit, self.ui.theta2upperEdit]

        for i in range(len(self.axes)):
            axis = self.axes[i]
            speed = "{:.1f}".format(axis.getSpeed())
            self.speed_labels[i].setText(speed)
            self.speed_edits[i].setText(speed)
            limits = axis.getLimits()
            lower = "{:.3f}".format(limits[0])
            self.lower_labels[i].setText(lower)
            self.lower_edits[i].setText(lower)
            upper = "{:.3f}".format(limits[1])
            self.upper_labels[i].setText(upper)
            self.upper_edits[i].setText(upper)

        # Initialise QThreadPool
        self.pool = QThreadPool.globalInstance()
        print('max thread count before = ', self.pool.maxThreadCount())
        self.pool.setMaxThreadCount(1)
        print('max thread count after = ', self.pool.maxThreadCount())
        print('active threads= ', self.pool.activeThreadCount())

        self.worker = None  # initial global worker

    def sleepGUI(self):
        """Set GUI to sleep for short time after button click to try to avoid crashing"""
        self.setEnabled(False)
        time.sleep(0.2)
        self.setEnabled(True)

    def track_progess(self, value):
        """Create progress bar to track progress of actions"""
        if self.progress.wasCanceled():  # if cancel button has been pressed
            print('Movement cancelled!!!')
            self.worker.isRun = False  # stop current worker from running further
        else:  # if progress not cancelled
            self.progress.setValue(value - 1)  # set progress bar value
            if value == 99:
                self.progress.setValue(100)

    def movement_radio(self):
        """Function to Select correct page of stacked widget for selected movement type"""
        if self.ui.relativeRadio.isChecked():  # if Relative Radio checked
            self.ui.movementStack.setCurrentIndex(0)  # set stacked widget to relative motion page
        else:  # if Global radio checked
            self.ui.movementStack.setCurrentIndex(1)  # set stacked widget to global motion page

    def SoftLimitWarning(self):
        """Raise warning message if movement values outside soft limits"""
        print('Raised on exception, create warning')
        self.progress.close()  # close progress bar
        warning = QtWidgets.QMessageBox.warning(self, 'Movement Outside Soft Limits',
                                                "Please change movement distance or soft limit settings",
                                                QtWidgets.QMessageBox.Ok)  # Create warning message box to user

    def thread_complete(self):
        """Function to be executed when a thread is completed"""
        print('Thread complete')
        self.worker = None  # reset worker class to none - does this help prevent GUI crashing between scans?
        self.sleepGUI()
        try: # restart timers if been paused
            self.timer.start()
            print('timers restarted')
        except:
            print('timers not restarted')
            pass

    def pause_timers(self):
        """Pause timers to allow methods to be run"""
        # Stop timers
        self.timer.stop()  # stop timers to recurring threads
        time.sleep(0.1)
        count0 = self.pool.activeThreadCount()  # number of active threads when program termination started
        print('Number of threads to close = ', count0)
        self.pool.clear()  # clear thread pool
        time.sleep(0.2)
        while self.pool.activeThreadCount() > 0:
            count_i = self.pool.activeThreadCount()  # current number of active threads
        print('new count = ', self.pool.activeThreadCount())

    def check_float(self, values, edits):
        """Function to check values entered into line edits are float type"""
        print('Checking if float')
        for i in range(len(edits)):  # for all values in edits list
            edits[i].setStyleSheet('background-color: rgb(255, 255, 255);')  # reset line edit colour to white
        try:
            for i in range(len(values)):  # for all values entered
                values[i] = float(values[i])  # check values are numbers
        except ValueError:  # if any entered values are not numbers
            print('Invalid Numbers Entered')
            warning = QtWidgets.QMessageBox.warning(self, 'Invalid Numbers',
                                                    "Please type valid numbers into the boxes",
                                                    QtWidgets.QMessageBox.Ok)  # Create warning message box to user
        else:  # if no value errors
            print('No errors')
            return values
        finally:  # after error loop completed, needed because loop stops after encountering first error
            for i in range(len(edits)):  # for all line edits
                try:
                    values[i] = float(values[i])  # check values are numbers
                except ValueError:  # if value is not a number
                    edits[i].setStyleSheet('background-color: rgb(255, 0, 0);')  # reset line edit colour to red

    def UpdatePositions(self, positions):
        """Update position labels on GUI"""
        for i in range(len(self.position_labels)):
            self.position_labels[i].setText(positions[i])

    def UpdateSettings(self, result):
        """Update motor settings display"""
        speeds = result[0][0]
        lowers = result[0][1]
        uppers = result[0][2]
        for i in range(len(self.axes)):
            speed = speeds[i]
            self.speed_labels[i].setText(speed)
            lower = lowers[i]
            self.lower_labels[i].setText(lower)
            upper = uppers[i]
            self.upper_labels[i].setText(upper)

    def UpdatePositions_stage1(self, positions):
        """Update position labels on GUI"""
        self.ui.stage1_x_label.setText(positions[0])
        self.ui.stage1_y_label.setText(positions[1])
        self.ui.stage1_theta_label.setText(positions[2])

    def UpdatePositions_stage2(self, positions):
        """Update position labels on GUI"""
        self.ui.stage2_x_label.setText(positions[0])
        self.ui.stage2_y_label.setText(positions[1])
        self.ui.stage2_z_label.setText(positions[2])
        self.ui.stage2_theta_label.setText(positions[3])


    def ReadPositions(self):
        """Read current axis positions"""
        # print('read positions now')
        worker = PositionsWorker(mc)  # connect to FieldsWorker object
        worker.signals.result.connect(self.UpdatePositions)
        worker.setAutoDelete(True)  # make worker auto-deletable so can be cleared
        self.pool.start(worker)

    def stage1_relative_move_click(self):
        """Function to be executed when relative movement button is clicked"""
        print('Move stage 1 relative')
        self.pause_timers()

        x1 = (self.ui.stage1_x_rel_edit.text())  # x value is current value in line Edit
        y1 = (self.ui.stage1_y_rel_edit.text())  # y value is current value in line Edit
        theta1 = (self.ui.stage1_theta_rel_edit.text())  # theta value is current value in line Edit

        edits = [self.ui.stage1_x_rel_edit, self.ui.stage1_y_rel_edit,
                 self.ui.stage1_theta_rel_edit]  # group all line edit names together in a list
        values = [x1, y1, theta1]  # create empty list to store values from line edits in

        check_values = self.check_float(values, edits)  # check if entered values were floats

        if check_values != None:  # if values are floats, execute command
            print('Move stage')
            print('Values = ', values)
            x = values[0]
            y = values [1]
            theta= values[2]
            self.worker = RelativeMoveWorker1(mc, x, y, theta)

            print('worker = ', print(self.worker))

            print('created')

            self.worker.setAutoDelete(True)
            self.worker.signals.result.connect(self.UpdatePositions_stage1)
            print('connect progress')
            self.worker.signals.progress.connect(self.track_progess)
            print('progress connected')
            self.worker.signals.error.connect(self.SoftLimitWarning)

            self.worker.signals.finished.connect(self.thread_complete)

            # Create progress bar
            # Set window text, stop button text, minimum value, maximum value
            print('create progress bar')
            self.progress = QtWidgets.QProgressDialog("Moving Relative Distance", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            self.pool.start(self.worker, priority=5)  # start pool after initialising progress bar

    def stage2_relative_move_click(self):
        """Function to be executed when relative movement button is clicked"""
        print('Move stage 2 relative')
        self.pause_timers()

        x2 = (self.ui.stage2_x_rel_edit.text())  # x value is current value in line Edit
        y2 = (self.ui.stage2_y_rel_edit.text())  # y value is current value in line Edit
        z2 = (self.ui.stage2_z_rel_edit.text())
        theta2 = (self.ui.stage1_theta_rel_edit.text())  # theta value is current value in line Edit

        edits = [self.ui.stage2_x_rel_edit, self.ui.stage2_y_rel_edit,
                 self.ui.stage2_z_rel_edit,
                 self.ui.stage2_theta_rel_edit]  # group all line edit names together in a list
        values = [x2, y2, z2, theta2]  # create empty list to store values from line edits in

        check_values = self.check_float(values, edits)  # check if entered values were floats

        if check_values != None:  # if values are floats, execute command
            print('Move stage')
            print('Values = ', values)

            x = values[0]
            y = values[1]
            z = values[2]
            theta = values[3]
            self.worker = RelativeMoveWorker2(mc, x, y, z, theta)

            print('worker = ', print(self.worker))

            print('created')

            self.worker.setAutoDelete(True)
            self.worker.signals.result.connect(self.UpdatePositions_stage2)
            print('connect progress')
            self.worker.signals.progress.connect(self.track_progess)
            print('progress connected')
            self.worker.signals.error.connect(self.SoftLimitWarning)

            self.worker.signals.finished.connect(self.thread_complete)

            # Create progress bar
            # Set window text, stop button text, minimum value, maximum value
            print('create progress bar')
            self.progress = QtWidgets.QProgressDialog("Moving Relative Distance", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            self.pool.start(self.worker, priority=5)  # start pool after initialising progress bar

    def stage1_global_move_click(self):
        """Function to be executed when global movement button is clicked"""
        print('Move stage 1 global')
        self.pause_timers()

        x1 = (self.ui.stage1_x_abs_edit.text())  # x value is current value in line Edit
        y1 = (self.ui.stage1_y_abs_edit.text())  # y value is current value in line Edit
        theta1 = (self.ui.stage1_theta_abs_edit.text())  # theta value is current value in line Edit

        edits = [self.ui.stage1_x_abs_edit, self.ui.stage1_y_abs_edit,
                 self.ui.stage1_theta_abs_edit]  # group all line edit names together in a list
        values = [x1, y1, theta1]  # create empty list to store values from line edits in

        check_values = self.check_float(values, edits)  # check if entered values were floats

        if check_values != None:  # if values are floats, execute command
            print('Move stage')
            print('Values = ', values)
            x = values[0]
            y = values[1]
            theta = values[2]
            self.worker = GlobalMoveWorker1(mc, x, y, theta)

            print('worker = ', print(self.worker))

            print('created')

            self.worker.setAutoDelete(True)
            self.worker.signals.result.connect(self.UpdatePositions_stage1)
            print('connect progress')
            self.worker.signals.progress.connect(self.track_progess)
            print('progress connected')
            self.worker.signals.error.connect(self.SoftLimitWarning)

            self.worker.signals.finished.connect(self.thread_complete)

            # Create progress bar
            # Set window text, stop button text, minimum value, maximum value
            print('create progress bar')
            self.progress = QtWidgets.QProgressDialog("Moving To Position", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            self.pool.start(self.worker, priority=5)  # start pool after initialising progress bar

    def stage2_global_move_click(self):
        """Function to be executed when global movement button is clicked"""
        print('Move stage 2 global')
        self.pause_timers()

        x2 = (self.ui.stage2_x_abs_edit.text())  # x value is current value in line Edit
        y2 = (self.ui.stage2_y_abs_edit.text())  # y value is current value in line Edit
        z2 = (self.ui.stage2_z_abs_edit.text())
        theta2 = (self.ui.stage2_theta_abs_edit.text())  # theta value is current value in line Edit

        edits = [self.ui.stage2_x_abs_edit, self.ui.stage2_y_abs_edit,
                 self.ui.stage2_z_abs_edit,
                 self.ui.stage2_theta_abs_edit]  # group all line edit names together in a list
        values = [x2, y2, z2, theta2]  # create empty list to store values from line edits in

        check_values = self.check_float(values, edits)  # check if entered values were floats

        if check_values != None:  # if values are floats, execute command
            print('Move stage')
            print('Values = ', values)
            x = values[0]
            y = values[1]
            z = values[2]
            theta = values[3]
            self.worker = GlobalMoveWorker2(mc, x, y, z, theta)

            print('worker = ', print(self.worker))

            print('created')

            self.worker.setAutoDelete(True)
            self.worker.signals.result.connect(self.UpdatePositions_stage2)
            print('connect progress')
            self.worker.signals.progress.connect(self.track_progess)
            print('progress connected')
            self.worker.signals.error.connect(self.SoftLimitWarning)

            self.worker.signals.finished.connect(self.thread_complete)

            # Create progress bar
            # Set window text, stop button text, minimum value, maximum value
            print('create progress bar')
            self.progress = QtWidgets.QProgressDialog("Moving to Position", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            self.pool.start(self.worker, priority=5)  # start pool after initialising progress bar

    def x_sync_move_click(self):
        """Function to move x axes in sync"""
        print('Moving x in sync')
        self.pause_timers()

        x1 = (self.ui.x1_sync_lineEdit.text())  # x value is current value in line Edit
        x2 = (self.ui.x2_sync_lineEdit.text())  # y value is current value in line Edit

        edits = [self.ui.x1_sync_lineEdit, self.ui.x2_sync_lineEdit]  # group all line edit names together in a list
        values = [x1, x2]  # create empty list to store values from line edits in

        check_values = self.check_float(values, edits)  # check if entered values were floats

        if check_values != None:  # if values are floats, execute command
            print('Move stage')
            print('Values = ', values)
            x1 = values[0]
            x2 = values[1]
            self.worker = x_syncWorker(mc, x1, x2)

            print('worker = ', print(self.worker))

            print('created')

            self.worker.setAutoDelete(True)
            self.worker.signals.result.connect(self.UpdatePositions)
            print('connect progress')
            self.worker.signals.progress.connect(self.track_progess)
            print('progress connected')
            self.worker.signals.error.connect(self.SoftLimitWarning)

            self.worker.signals.finished.connect(self.thread_complete)

            # Create progress bar
            # Set window text, stop button text, minimum value, maximum value
            print('create progress bar')
            self.progress = QtWidgets.QProgressDialog("Moving Relative Distance", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            self.pool.start(self.worker, priority=5)  # start pool after initialising progress bar

    def y_sync_move_click(self):
        """Function to move y axes in sync"""
        print('Moving y in sync')
        self.pause_timers()

        y1 = (self.ui.y1_sync_lineEdit.text())  # x value is current value in line Edit
        y2 = (self.ui.y2_sync_lineEdit.text())  # y value is current value in line Edit

        edits = [self.ui.y1_sync_lineEdit, self.ui.y2_sync_lineEdit]  # group all line edit names together in a list
        values = [y1, y2]  # create empty list to store values from line edits in

        check_values = self.check_float(values, edits)  # check if entered values were floats

        if check_values != None:  # if values are floats, execute command
            print('Move stage')
            print('Values = ', values)
            y1 = values[0]
            y2 = values[1]
            self.worker = y_syncWorker(mc, y1, y2)

            print('worker = ', print(self.worker))

            print('created')

            self.worker.setAutoDelete(True)
            self.worker.signals.result.connect(self.UpdatePositions)
            print('connect progress')
            self.worker.signals.progress.connect(self.track_progess)
            print('progress connected')
            self.worker.signals.error.connect(self.SoftLimitWarning)

            self.worker.signals.finished.connect(self.thread_complete)

            # Create progress bar
            # Set window text, stop button text, minimum value, maximum value
            print('create progress bar')
            self.progress = QtWidgets.QProgressDialog("Moving Relative Distance", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            self.pool.start(self.worker, priority=5)  # start pool after initialising progress bar

    def theta_sync_move_click(self):
        """Function to move rotation axes in sync"""
        print('Moving theta in sync')
        self.pause_timers()

        theta1 = (self.ui.theta1_sync_lineEdit.text())  # x value is current value in line Edit
        theta2 = (self.ui.theta2_sync_lineEdit.text())  # y value is current value in line Edit

        edits = [self.ui.theta1_sync_lineEdit, self.ui.theta2_sync_lineEdit]  # group all line edit names together in a list
        values = [theta1, theta2]  # create empty list to store values from line edits in

        check_values = self.check_float(values, edits)  # check if entered values were floats

        if check_values != None:  # if values are floats, execute command
            print('Move stage')
            print('Values = ', values)
            theta1 = values[0]
            theta2 = values[1]
            self.worker = theta_syncWorker(mc, theta1, theta2)

            print('worker = ', print(self.worker))

            print('created')

            self.worker.setAutoDelete(True)
            self.worker.signals.result.connect(self.UpdatePositions)
            print('connect progress')
            self.worker.signals.progress.connect(self.track_progess)
            print('progress connected')
            self.worker.signals.error.connect(self.SoftLimitWarning)

            self.worker.signals.finished.connect(self.thread_complete)

            # Create progress bar
            # Set window text, stop button text, minimum value, maximum value
            print('create progress bar')
            self.progress = QtWidgets.QProgressDialog("Moving Relative Distance", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            self.pool.start(self.worker, priority=5)  # start pool after initialising progress bar

    def motor_settings_click(self):
        """Function to update motor controller settings"""
        print('Update motor settings')
        self.pause_timers()

        edits = [self.ui.x1speedEdit, self.ui.x1lowerEdit, self.ui.x1upperEdit,
                 self.ui.y1speedEdit, self.ui.y1lowerEdit, self.ui.y1upperEdit,
                 self.ui.x2speedEdit, self.ui.x2lowerEdit, self.ui.x2upperEdit,
                 self.ui.y2speedEdit, self.ui.y2lowerEdit, self.ui.y2upperEdit,
                 self.ui.z2speedEdit, self.ui.z2lowerEdit, self.ui.z2upperEdit,
                 self.ui.theta1speedEdit, self.ui.theta1lowerEdit, self.ui.theta1upperEdit,
                 self.ui.theta2speedEdit, self.ui.theta2lowerEdit, self.ui.theta2upperEdit]
        values = []
        for i in range(len(edits)):
            value = edits[i].text()
            values.append(value)

        check_values = self.check_float(values, edits)  # check if entered values were floats

        if check_values != None:  # if values are floats, execute command
            print('Update motor settings')
            print('Values = ', values)

            self.worker = setMotorSettingsWorker(mc, values)

            print('worker = ', print(self.worker))

            print('created')

            self.worker.setAutoDelete(True)
            self.worker.signals.result.connect(self.UpdateSettings)
            print('connect progress')
            self.worker.signals.progress.connect(self.track_progess)
            print('progress connected')
            self.worker.signals.finished.connect(self.thread_complete)

            # Create progress bar
            # Set window text, stop button text, minimum value, maximum value
            print('create progress bar')
            self.progress = QtWidgets.QProgressDialog("Updating Motor Settings", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            self.pool.start(self.worker, priority=5)  # start pool after initialising progress bar

    def changeEvent(self, event):
        """Function to be executed when GUI window minimised"""
        # does this function reduce likelihood of GUI freezing after being minimised?
        if event.type() == QtCore.QEvent.WindowStateChange:
            if self.windowState() & QtCore.Qt.WindowMinimized:
                print('window minimised')
                #event.ignore()
                return

    def closeEvent(self, event):
        """Function to check that user wants to exit program when close button pressed"""
        self.sleepGUI()
        choice = QtWidgets.QMessageBox.question(self, 'Magnet Lab Controls',
                                                "Do you want to exit the program?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        if choice == QtWidgets.QMessageBox.Yes:

            print(datetime.datetime.now())
            self.timer.stop()  # stop timers to recurring threads
            #self.timer2.stop()
            time.sleep(0.1)

            count0 = self.pool.activeThreadCount()  # number of active threads when program termination started
            print('Number of threads to close = ', count0)

            self.pool.clear()  # clear thread pool
            time.sleep(0.2)

            # Set window text, stop button text, minimum value, maximum value
            self.progress = QtWidgets.QProgressDialog("Closing down", "STOP", 0, 100, self)
            self.progress.setWindowTitle('Please wait...')
            self.progress.setAutoClose(True)  # Automatically close dialog once progress completed
            self.progress.setWindowModality(
                QtCore.Qt.WindowModal)  # Make window modal so processes can take place in background
            self.progress.canceled.connect(self.progress.close)  # Close dialog when close button pressed
            self.progress.show()  # Show progress dialog

            while self.pool.activeThreadCount() > 0:
                count_i = self.pool.activeThreadCount()  # current number of active threads
                closed_threads = count0 - count_i
                progress = int(100 * closed_threads / count0)
                self.track_progess(progress - 1)

            print('new count = ', self.pool.activeThreadCount())

            self.pool.waitForDone()

            print('final count = ', self.pool.activeThreadCount())

            mc.close()  # close serial connection with motor controller

            print('Closing down...')
            print(datetime.datetime.now())
            sys.exit()
        else:
            print('Do not quit')
            event.ignore()


app = QtWidgets.QApplication([])
application = mywindow()
application.show()
sys.exit(app.exec())  # create window
