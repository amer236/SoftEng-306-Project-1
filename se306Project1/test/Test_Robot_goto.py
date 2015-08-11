#!/usr/bin/env python
# PKG = 'se306Project1'
# NAME = "test_robot_go_to"
# import roslib; roslib.load_manifest(PKG)  # This line is not needed with Catkin.

import sys
import unittest
import rospy
from std_msgs.msg import *
import sensor_msgs.msg
import time
from se306Project1.src.RobotCarrier import RobotCarrier
import math
import logging
from TestModule import TestModule


class TestRobotGoTo(unittest.TestCase,TestModule):

    #Not in 'setUp' because it will be called every time, and that will mean the node will restart its in instantiation
    #since we can't reset the stage, we have to work with the same robot.
    robot0 = RobotCarrier(1,-10,-28, math.pi/2)


    def test_goto_move_right(self):

        end_x = -5
        end_y = -28

        moveAction = self.robot0.goto, [end_x,end_y]

        self.run_robot(self.robot0,moveAction,15)

        self.assertTrue(self.compare_values_with_threshold(self.robot0.px,end_x),"End X = Expected End X")
        self.assertTrue(self.compare_values_with_threshold(self.robot0.py,end_y),"End Y = Expected End Y")

    def test_goto_move_left(self):

        end_x = -15
        end_y = -28

        moveAction = self.robot0.goto, [end_x,end_y]

        self.run_robot(self.robot0,moveAction,15)

        self.assertTrue(self.compare_values_with_threshold(self.robot0.px,end_x),"End X = Expected End X")
        self.assertTrue(self.compare_values_with_threshold(self.robot0.py,end_y),"End Y = Expected End Y")

if __name__ == '__main__':
    unittest.main()
    # import rostest
    # rostest.rosrun(PKG, NAME, TestRobotGoTo)