import PyQt5
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QMutex
import traceback
import sys
from WorkerSignals import WorkerSignals

mutex = QMutex()


class PositionsWorker(QRunnable):
    """Worker class to read and update motor positions"""

    def __init__(self, mc):
        super(PositionsWorker, self).__init__()
        self.mc = mc
        self.x1 = mc.axis['fc x1']
        self.y1 = mc.axis['fc y1']
        self.x2 = mc.axis['fc x2']
        self.y2 = mc.axis['fc y2']
        self.z2 = mc.axis['fc z2']
        self.theta1 = mc.axis['fc theta 1']
        self.theta2 = mc.axis['fc theta 2']
        self.signals = WorkerSignals()  # can send signals to main GUI

    def run(self):
        """Task to read motor positions and emit signal"""
        # global mc
        try:
            x1 = "{:.3f}".format(self.x1.get_position())
            y1 = "{:.3f}".format(self.y1.get_position())
            x2 = "{:.3f}".format(self.x2.get_position())
            y2 = "{:.3f}".format(self.y2.get_position())
            z2 = "{:.3f}".format(self.z2.get_position())
            theta1 = "{:.3f}".format(self.theta1.get_position())
            theta2 = "{:.3f}".format(self.theta2.get_position())
        except:
            print('error')
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:  # if no exceptions
            # Emit signal
            self.signals.result.emit([x1, y1, x2, y2, z2, theta1, theta2])  # emit fields
        finally:
            self.signals.finished.emit()
