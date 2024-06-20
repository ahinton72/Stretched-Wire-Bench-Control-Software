import PyQt5
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QRunnable, pyqtSlot, QThreadPool, QMutex
import traceback
import sys
import datetime
from WorkerSignals import WorkerSignals

mutex = QMutex()


class GlobalMoveWorker1(QRunnable):
    def __init__(self, mc, x, y, theta):
        super(GlobalMoveWorker1, self).__init__()
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
        self.x = x
        self.y = y
        self.theta = theta

        print('relative move worker initialised')

    def run(self):
        """Function to move Hall probe relative distance and track progress"""
        print('rel move running')
        try:
            x0 = self.x1.get_position()  # get starting x position
            y0 = self.y1.get_position()  # get starting y position
            theta0 = self.theta1.get_position()  # get starting z position
            print('positions read ok')

            total_distance = abs(float(self.x) - float(x0)) + abs(float(self.y) - float(y0)) + abs(float(self.theta) - float(theta0))  # total distance for motors to travel

            print('no problems yet - move motors')

            # Move motors
            self.x1.move(float(self.x))
            self.y1.move(float(self.y))
            self.theta1.move(float(self.theta))

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
                    self.y1.stop()
                    self.theta1.stop()

                    print('Movement stopped')

                    break  # break out of loop

                # Determine distances travelled in x, y, z

                current_x_position = self.x1.get_position()

                x_distance_travelled = abs(current_x_position - x0)

                current_y_position = self.y1.get_position()

                y_distance_travelled = abs(current_y_position - y0)

                current_theta_position = self.theta1.get_position()

                theta_distance_travelled = abs(current_theta_position - theta0)

                self.signals.result.emit(
                    ["{:.3f}".format(current_x_position), "{:.3f}".format(current_y_position), "{:.3f}".format(current_theta_position)])

                # Determine distance travelled as fraction of total distance to travel

                self.distance = int(

                    100 * (x_distance_travelled + y_distance_travelled + theta_distance_travelled) / total_distance)

                print('progress=', self.distance)

                self.signals.progress.emit(self.distance)  # send progress signal to GUI

                # Set progress bar to 100% when current probe readings are as expected

                tolerance = 0.1  # tolerance on expected vs desired final position

                if abs(self.x1.get_position() - (float(self.x))) < tolerance and abs(

                        self.y1.get_position() - (float(self.y))) < tolerance and abs(

                        self.theta1.get_position() - (float(self.theta))) < tolerance:
                    self.distance = 100

                    print('set progress bar to 100')

                    self.signals.progress.emit(

                        self.distance - 1)  # Finally, set progress bar value to target maximum'''

        finally:

            print('emit finished signal')

            self.signals.finished.emit()

            print('finish signal emitted')
