#!/usr/bin/env python
PKG = 'se306Project1'
NAME = "test_entity_laser_listener"
import roslib; roslib.load_manifest(PKG)  # This line is not needed with Catkin.
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))
import sys
import unittest
import rospy
from std_msgs.msg import *
import sensor_msgs.msg
import time
from src.RobotPicker import RobotPicker
import math
import logging
from TestModule import TestModule
import inspect
"""
@class

This is a test for the ability of the function turn to turn both right and left ( we only move in right angles, only turns needed)

"""
class Test_Robot_turn(unittest.TestCase,TestModule):

    #Not in 'setUp' because it will be called every time, and that will mean the node will restart its in instantiation
    #since we can't reset the stage, we have to work with the same robot.
    robot0 = RobotPicker("Node",0,-20,-28, math.pi/2,50)

    def test_turn_1right(self):

        moveAction = self.robot0.turn,["right"]

        self.run_robot(self.robot0,moveAction,5)

        self.assertEqual(self.robot0.get_current_direction(), "east")

    def test_turn_2left(self):

        moveAction = self.robot0.turn,["left"]

        self.run_robot(self.robot0,moveAction,5)

        self.assertEqual(self.robot0.get_current_direction(), "north")

if __name__ == '__main__':
    # unittest.main()
    import rostest
    rostest.rosrun('se306Project1', 'test_bare_bones', Test_Robot_turn)