import PyQt5
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QMutex
import traceback
import sys
import datetime
from WorkerSignals import WorkerSignals
import time
mutex = QMutex()


class setMotorSettingsWorker(QRunnable):
    """Worker class to read and update motor positions"""

    def __init__(self, mc, values):
        print('motor settings')
        super(setMotorSettingsWorker, self).__init__()
        self.signals = WorkerSignals()  # can send signals to main GUI
        self.mc = mc
        self.x1 = mc.axis['fc x1']
        self.y1 = mc.axis['fc y1']
        self.x2 = mc.axis['fc x2']
        self.y2 = mc.axis['fc y2']
        self.z2 = mc.axis['fc z2']
        self.theta1 = mc.axis['fc theta 1']
        self.theta2 = mc.axis['fc theta 2']
        self.axes = [self.x1, self.y1, self.x2, self.y2, self.z2, self.theta1, self.theta2]
        self.values = values

    def run(self):
        """Task to read motor positions and emit signal"""
        try:
            progress = 10
            self.signals.progress.emit(progress)  # send progress signal to GUI
            # x1
            self.x1.setSpeed(self.values[0])
            self.x1.setLimits((self.values[1], self.values[2]))
            progress += 5
            self.signals.progress.emit(progress)
            # y1
            self.y1.setSpeed(self.values[0])
            self.y1.setLimits((self.values[1], self.values[2]))
            progress += 5
            self.signals.progress.emit(progress)
            # x2
            self.x2.setSpeed(self.values[0])
            self.x2.setLimits((self.values[1], self.values[2]))
            progress += 5
            self.signals.progress.emit(progress)
            # y2
            self.y2.setSpeed(self.values[0])
            self.y2.setLimits((self.values[1], self.values[2]))
            progress += 5
            self.signals.progress.emit(progress)
            # z2
            self.z2.setSpeed(self.values[0])
            self.z2.setLimits((self.values[1], self.values[2]))
            progress += 5
            self.signals.progress.emit(progress)
            # theta1
            self.theta1.setSpeed(self.values[0])
            self.theta1.setLimits((self.values[1], self.values[2]))
            progress += 5
            self.signals.progress.emit(progress)
            # theta2
            self.theta2.setSpeed(self.values[0])
            self.theta2.setLimits((self.values[1], self.values[2]))
            progress += 5
            self.signals.progress.emit(progress)


            self.signals.progress.emit(50)

        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:  # if no exceptions
            # Emit signal
            speeds = []
            lowers = []
            uppers = []

            progress = 50

            for i in range(len(self.axes)):
                axis = self.axes[i]
                speed = "{:.1f}".format(axis.getSpeed())
                speeds.append(speed)
                limits = axis.getLimits()
                lower = "{:.3f}".format(limits[0])
                lowers.append(lower)
                upper = "{:.3f}".format(limits[1])
                uppers.append(upper)
                progress += 5
                self.signals.progress.emit(progress)

            self.signals.result.emit([(speeds, lowers, uppers)])  # emit fields
            print('speeds emitted')
        finally:
            print('motor settings worker thread completed')
            self.signals.progress.emit(99)
            self.signals.finished.emit()
            print('finished')