#!/usr/bin/env python
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))

import sys
import unittest
import rospy
from std_msgs.msg import *
import sensor_msgs.msg
from src.RobotCarrier import RobotCarrier

import math
from TestModule import TestModule
import inspect
import subprocess

processes = []

class Test_Robot_Carrier_Communication(unittest.TestCase,TestModule):

    robot1 = RobotCarrier(1,0,-28, math.pi/2)
    processes.append(subprocess.Popen(["rosrun", "se306Project1", "Run_RobotPicker.py"], shell=False))

    def test_robot_carrier_communication(self):
        self.print_function_name(inspect.stack()[0][3])

        rospy.sleep(5) # sleep for a while to let the robot picker start moving
        self.assertNotEqual(self.robot1.picker_robots[0], "0,0,0")
        print("Picker robot array")
        print(self.robot1.picker_robots)


if __name__ == '__main__':
    unittest.main()
