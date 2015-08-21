#!/usr/bin/env python

import rospy
from std_msgs.msg import*
from geometry_msgs.msg import*
from nav_msgs.msg import*
from sensor_msgs.msg import*
from tf.transformations import *
import math
import random
import numpy.testing
from Human import Human
import ActionInterruptException
import os
import time

"""
@class

Worker class. Inherits from the abstract Human class. The behaviour of this entity will consist
of patrolling up and down empty orchard rows, and will leave a orchard if a robot enters its current
row.

This entity subsribes to topics generated by the Picker and Carrier class, then stores coordinates of
Picker and Carrier entities into a dictionary. This information is used to determine if an orchard row is
empty or not, and also allows the worker entity to detect if a robot enters the row it is currently in.
"""

class Worker(Human):

    def enum(**enums):
        return type('Enum', (), enums)

    WorkerState = enum(PATROLLING_ORCHARD="Moving up and down row",
                        GOING_TO_EMPTY_ORCHARD="Navigating to empty orchard",
                        AVOIDING_ROBOT="Detected robot, leaving row",
                       WAITING_FOR_EMPTY_ROW="Waiting for row to become empty")

    def __init__(self, r_id, x_off, y_off, theta_offset):
        Human.__init__(self, r_id, x_off, y_off, theta_offset)


        #Initialise worker state to empty string
        self.worker_state = ""

        #Initialise dictionary of various robot coordinates
        self.robot_locations = {}

        #Array that stores coordinate information corresponding to orchard row gaps
        self.orchard_row_gaps = []

        #This will hold the dictionary of properties defined in the config.properties file
        self.config = {}

        #Generate the coordinates for the orchard row gaps
        self.define_orchard_row_gaps()

        #This is the current orchard row gap that the worker will be travelling to, or is currently patrolling
        self.empty_row_target = [0, 0]

        #Create subscribers to the positions for both picker and carrier
        self.sub_to_picker_positions = rospy.Subscriber("pickerPosition", String, self.Robot_Locations_Callback)
        self.sub_to_carrier_positions = rospy.Subscriber("carrierPosition", String, self.Robot_Locations_Callback)

        #Define the actions to be used for the action stack
        self._actions_ = {
            0: self.move_forward,
            1: self.goto_yx,
            2: self.goto_xy,
            3: self.turn,
            4: self.stop,
            5: self.go_to_empty_orchard_row,
            6: self.patrol_orchard,
            7: self.avoid_robot
         }

    """
    @function

    Call back function to update position values. Also will write current state information to a wor.sta file which
    is to be used by the GUI
    """
    def StageOdom_callback(self, msg):
        #Update the px and py values
        self.update_position(msg.pose.pose.position.x, msg.pose.pose.position.y)

        #Find the yaw from the quaternion values
        (roll, pitch, yaw) = euler_from_quaternion((msg.pose.pose.orientation.x, msg.pose.pose.orientation.y, msg.pose.pose.orientation.z, msg.pose.pose.orientation.w))

        #Update the theta value
        self.update_theta(yaw)

        #Write current state information to wor.sta file
        fn = os.path.join(os.path.dirname(__file__), str(self.robot_id)+"wor.sta")
        output_file = open(fn, "w")
        output_file.write(str(self)+str(self.robot_id)+ "\n")
        output_file.write("Worker\n")
        output_file.write(self.worker_state + "\n")
        output_file.write(str(round(self.px,2)) + "\n")
        output_file.write(str(round(self.py,2)) + "\n")
        output_file.write(str(round(self.theta,2)) + "\n")
        output_file.close()

    """
    @function

    Call back function for the laser messages. When this entity detects a object in front of it,
    it will stop current action, then turn right and move forward.
    """
    def StageLaser_callback(self, msg):
        #Check for a degree range between 60 and 120 degrees
        for i in range(60, 120):
            #If object within 4m and not already turning then perform collision avoidance
            if (msg.ranges[i] < 4 and self.disableLaser == False):

                #Stop current action
                self._stopCurrentAction_ = True

                #Create actions to turn right and move forward
                move1 = self._actions_[0], [3]
                turn2 = self._actions_[3], ["right"]

                #Append actions to stack
                self._actionsStack_.append(move1)
                self._actionsStack_.append(turn2)

                return

    """
    @function

    Call back function that will store the current positions of the robots in the stage in a dictionary
    """
    def Robot_Locations_Callback(self, message):

        #Obtain the individual message values from the message data
        msg = message.data
        msg_values = msg.split(",")

        #Set robot id
        r_id = msg_values[0]

        #Set coordinate values
        r_px = float(msg_values[1])
        r_py = float(msg_values[2])

        r_coord = [r_px, r_py]

        #Add the coordinate to the robot locations dictionary, using the robot id as the key
        self.robot_locations[r_id] = r_coord

        #Check if any action needs to be performed based on current location of robots
        self.check_robot_locations()

    """
    @function

    This function is called when initliasing the worker entity. It will read from the config.properties
    in order to determine the number of orchard rows to be generated. It will then use this information
    to generate a set of coordinates that correspond to orchard row gaps throughout the stage world.
    """
    def define_orchard_row_gaps(self):

        #Set the path to the config.properties file
        path_to_config = os.path.dirname(os.path.abspath(os.pardir)) + "/config.properties"

        #Store each property in a dictionary
        with open(path_to_config, "r") as f:
            for line in f:
                property = line.split('=')
                self.config[property[0]] = property[1]

        #get number of orchard rows
        rows = int(self.config.get('orchard.number'))

        WORLD_WIDTH = 80

        #max number of orchards is 10
        if rows > 10:
            rows = 10
        elif rows < 1:
            rows = 1

        #Set the width between the rows
        width_between_rows = WORLD_WIDTH/(rows)

        #Loop until all gap coordinates are generated
        for x in range(-WORLD_WIDTH/2 + width_between_rows/2,WORLD_WIDTH/2 - width_between_rows/2, width_between_rows):

            #Set left x coordinate to be just the x value
            x_left = x

            #Set right x coordinate to be the x value plus the width of the row
            x_right = x + width_between_rows

            #Add coordinate to array of orchard row gaps
            self.orchard_row_gaps.append([x_left, x_right])

    """
    @function

    This will use the orchard_row_gaps array and the current locations of the robots stores in the robot_locations
    dictionary to determine which orchard row gaps are unoccupied. It will then append actions to the stack
    that will cause the worker to travel to the first empty orchard gap.
    """
    def go_to_empty_orchard_row(self):

        #Set current state to reflect that worker is going to empty orhcard gap
        self.worker_state = self.WorkerState.GOING_TO_EMPTY_ORCHARD

        #Initialise array that store x coordinates of the empty orhcard gap
        empty_orchard_row_x = []

        #Initialise a boolean variable that will change based on whether a empty orchard gap exists or not
        found_row = False

        for g in self.orchard_row_gaps:
            #For each gap in the orchard_row_gaps, initially set unpopulated boolean variable to True
            unpopulated = True
            #Then iterate through each robot coordinate stores in the robot_locations dictionary
            for r_coord in self.robot_locations.itervalues():
                #Check if x coordinate of robot is within orchard row gap
                if [0] <= r_coord[0] <= g[1]:
                    #If true then set unpopulated to false
                    unpopulated = False

            #If unpopulated remained true, then empty orhcard row gap was found
            if unpopulated:
                #Set empty orchard row x coordinates to the founded gap
                empty_orchard_row_x = g
                #Set empty orhcard row target
                self.empty_row_target = g
                #Set found_row to True
                found_row = True
                break

        if found_row == False:
            #If empty row not found, then wait 10 seconds then try again
            self.worker_state = self.WorkerState.WAITING_FOR_EMPTY_ROW
            rospy.sleep(10)
            return self.go_to_empty_orchard_row

        #Set the x coordinate that the worker will traverse to, to be a random value inbetween the left and right x
        #coordinate of the founded orchard gap
        x_target = random.randint(empty_orchard_row_x[0] + 3, empty_orchard_row_x[1] - 3)

        #Create actions to traverse to orchard row, as well as the action to patrol the row up and down
        goto_x_action = self._actions_[1], [x_target, self.py]
        goto_y_action = self._actions_[1], [x_target, -10]
        patrol_action = self._actions_[6], []

        #Append actions to stack
        self._actionsStack_.append(patrol_action)
        self._actionsStack_.append(goto_y_action)
        self._actionsStack_.append(goto_x_action)

        return 0

    """
    @function

    This function will be called once the worker has reached an empty orchard row gap. This function then
    appends two actions to the stack, that will move the worker up and down the row.
    """
    def patrol_orchard(self):
        #Set state to PATROLLING_ORCHARD
        self.worker_state = self.WorkerState.PATROLLING_ORCHARD

        #Create actions to move north then south
        go_north = self._actions_[1], [self.px, 48]
        go_south = self._actions_[1], [self.px, -10]

        #Append actions to stack
        self._actionsStack_.append(go_south)
        self._actionsStack_.append(go_north)

        return 0


    """
    @function
    This function is called when a robot enters the row that the worker is currently in. It will create
    and append actions in order to move the worker out of the row.
    """
    def avoid_robot(self, robot_py):
        #Set state to AVOIDING_ROBOT
        self.worker_state = Worker.WorkerState.AVOIDING_ROBOT

        if robot_py < self.py:
            #Create action to leave the row by going  then head east
            leave_row = self._actions_[1], [self.px, -20]
            go_east = self._actions_[1], [30, -20]
        else:
            #Create action to leave the row by going north then head east
            leave_row = self._actions_[1], [self.px, 48]
            go_east = self._actions_[1], [30, 48]

        #Append actions
        self._actionsStack_.append(go_east)
        self._actionsStack_.append(leave_row)

        #Set stopCurrentAction to false
        self._stopCurrentAction_ = False

        return 0

    """
    @function
    This function is called each time a robot position is updated in the robot_locations dictionary.
    This will check if a robot has entered the current row, then it will append the avoid_action to the action
    stack.
    """
    def check_robot_locations(self):
        #Check positions of all robots in stage
        for r_coord in self.robot_locations.itervalues():

            #Initiliase the coordinate values
            r_px = r_coord[0]
            r_py = r_coord[1]

            #Check if the x coordinate is within the current orchard row
            if self.empty_row_target[0] <= r_px <= self.empty_row_target[1]:
                #Check if the robot has actually entered the orchard row as well
                if -10 <= r_py <= 39:

                    #Stop current action
                    self._stopCurrentAction_ = True

                    #Set and append avoid action
                    avoid_action = self._actions_[7], [r_py]
                    self._actionsStack_.append(avoid_action)

                    return

    """
    @function
    This function is called by the Run_Worker script in the main while loop
    """
    def worker_specific_function(self):
        #If there are currently no actions on the stack, then the initial would be to find an empty orchard row
        if len(self._actionsStack_) == 0:
            init_action = self._actions_[5], []
            self._actionsStack_.append(init_action)

        #While there are actions on the stack and no action is currently running
        while (len(self._actionsStack_) > 0 and not self._actionRunning_):

            #get top action on stack
            action = self._actionsStack_[-1]

            if (action == 0):
                #Clear action stack and then break out of loop
                del self._actionsStack_[:]
                break

            try:
                self._actionRunning_ = True

                #run aciton with paremeter
                result = action[0](*action[1])

                #Remove the last currently ran action from the stack
                del self._actionsStack_[self._actionsStack_.index(action)]

                self._actionRunning_ = False

                #If there are no actions on the stack and the Worker is currently patrolling an orhcard row,
                #then add the patrol orchard row action to the stack
                if len(self._actionsStack_) == 0 and self.worker_state == self.WorkerState.PATROLLING_ORCHARD:
                    patrol_action = self._actions_[6], []
                    self._actionsStack_.append(patrol_action)

            #Catch the exception that will be raised when the stopCurrentAction is set to True, though do not
            #perform any actions
            except ActionInterruptException.ActionInterruptException as e:
                print(str(e))


