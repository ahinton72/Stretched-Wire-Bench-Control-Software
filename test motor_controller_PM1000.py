import motor_controller_PM1000
mc = motor_controller_PM1000.MotorController()
from time import sleep

# Set motor controller classes
xa = mc.axis['x']
ya = mc.axis['y']
za = mc.axis['z']
x1 = mc.axis['fc x1']
y1 = mc.axis['fc y1']
x2 = mc.axis['fc x2']
y2 = mc.axis['fc y2']
z2 = mc.axis['fc z2']
theta1 = mc.axis['fc theta 1']
theta2 = mc.axis['fc theta 2']

for i in range(1):
    com1 = x1.move(-2, relative=True, sync_move=True)
    com2 = x2.move(2, relative=True, sync_move=True)

mc.synchronous((com1, com2))


mc.close() # close motor controller object