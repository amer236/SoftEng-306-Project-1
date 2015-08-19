#!/usr/bin/env python
import unittest
from TestModule import TestModule
import rospy
from se306Project1.src.GUI_overlay import GUI_overlay
import os
import threading

class Test_GUI_overlay_read_data(unittest.TestCase,TestModule):



    def test_picker_file(self):
        gui = GUI_overlay()



        #dir = os.path.abspath('./se306Project1/src/TESTpic.sta')
        # output_file = open(dir, "w")
        # output_file.write("robot_100\n")
        # output_file.write("Picker\n")
        # output_file.write("Picking fruit")
        # output_file.write("0.25\n")
        # output_file.write("0.55\n")
        # output_file.write("3.1415\n")
        # output_file.write("19/20\n")

        gui.update()

        for i in gui.robot_label_list:
            print("HERE:"+i.cget("text"))

        self.assertEquals(gui.robot_label_list[0].cget("text"), "robot_100\n")
        self.assertEquals(gui.robot_label_list[1].cget("text"), "Picker\n")
        self.assertEquals(gui.robot_label_list[2].cget("text"), "Picking fruit")
        self.assertEquals(gui.robot_label_list[3].cget("text"), "0.25\n")
        self.assertEquals(gui.robot_label_list[4].cget("text"), "3.1415\n")
        self.assertEquals(gui.robot_label_list[5].cget("text"), "19/20\n")


if __name__ == '__main__':
    unittest.main()