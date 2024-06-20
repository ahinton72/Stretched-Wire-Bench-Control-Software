import PyQt5
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QMutex
import traceback
import sys
import datetime
from WorkerSignals import WorkerSignals

mutex = QMutex()


class x_syncWorker(QRunnable):
    def __init__(self, mc, x1, x2):
        super(x_syncWorker, self).__init__()
        self.distance = None
        self.signals = WorkerSignals()
        self.isRun = True  # isRun flag = true; do not stop action

        self.mc = mc
        self.x1 = mc.axis['fc x1']
        self.y1 = mc.axis['fc y1']
        self.x2 = mc.axis['fc x2']
        self.y2 = mc.axis['fc y2']
        self.z2 = mc.axis['fc z2']
        self.theta1 = mc.axis['fc theta 1']
        self.theta2 = mc.axis['fc theta 2']
        self.delta_x1 = x1 #distance to move stage 1 x
        self.delta_x2 = x2 # distance to move stage 2 x

    def run(self):
        """Function to move Hall probe relative distance and track progress"""
        print('rel move running')
        try:
            x1_0 = self.x1.get_position()  # get starting x position
            x2_0 = self.x2.get_position()

            total_distance = abs(float(self.delta_x1)) + abs(float(self.delta_x2)) # total distance for motors to travel

            print('no problems yet - move motors')

            # Move motors
            cmd1 = self.x1.move(float(self.delta_x1), relative=True, sync_move=True)
            cmd2 = self.x2.move(float(self.delta_x2), relative=True, sync_move=True)

            self.mc.synchronous((cmd1, cmd2))

        except:  # if Value error raised by soft limits exception
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))

        else:  # if no exceptions

            print('no errors')

            self.distance = 0  # dummy variable, starts at 0

            if total_distance == 0:  # if total move distance = 0, skip loop

                self.distance = 100

                self.signals.progress.emit(self.distance - 1)

            while self.distance < 100:  # while total distance travelled less than 100%

                if not self.isRun:  # check if STOP button pressed

                    print('Movement cancelled!')  # print to console

                    # Send STOP command to motor
                    self.x1.stop()
                    self.x2.stop()

                    print('Movement stopped')

                    break  # break out of loop

                # Determine distances travelled in x, y, z

                current_x1_position = self.x1.get_position()
                x1_distance_travelled = abs(current_x1_position - x1_0)

                current_x2_position = self.x2.get_position()
                x2_distance_travelled = abs(current_x2_position - x2_0)

                x1 = "{:.3f}".format(self.x1.get_position())
                y1 = "{:.3f}".format(self.y1.get_position())
                x2 = "{:.3f}".format(self.x2.get_position())
                y2 = "{:.3f}".format(self.y2.get_position())
                z2 = "{:.3f}".format(self.z2.get_position())
                theta1 = "{:.3f}".format(self.theta1.get_position())
                theta2 = "{:.3f}".format(self.theta2.get_position())
                self.signals.result.emit([x1, y1, x2, y2, z2, theta1, theta2])  # emit fields

                # Determine distance travelled as fraction of total distance to travel

                self.distance = int(

                    100 * (x1_distance_travelled + x2_distance_travelled) / total_distance)

                print('progress=', self.distance)

                self.signals.progress.emit(self.distance)  # send progress signal to GUI

                # Set progress bar to 100% when current probe readings are as expected

                tolerance = 0.1  # tolerance on expected vs desired final position

                if abs(self.x1.get_position() - (x1_0 + float(self.delta_x1))) < tolerance and abs(

                        self.x2.get_position() - (x2_0 + float(self.delta_x2))) < tolerance:
                    self.distance = 100

                    print('set progress bar to 100')

                    self.signals.progress.emit(

                        self.distance - 1)  # Finally, set progress bar value to target maximum'''

        finally:

            print('emit finished signal')

            self.signals.finished.emit()

            print('finish signal emitted')
