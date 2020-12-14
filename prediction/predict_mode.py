import numpy as np
import os
from os import path
import random
import matplotlib.pyplot as plt

import math

import sys
sys.path.append("/Users/anjianli/Desktop/robotics/project/optimized_dp")

from prediction.clustering import Clustering
from prediction.process_prediction import ProcessPrediction

import pandas as pd

class PredictMode(object):

    def __init__(self):

        self.to_plot_pred_mode = True

        self.to_save_pred_mode = False

        self.plot_probability = True

        # Which scenario to predict
        self.scenario_predict = "intersection"
        # self.scenario_predict = "roundabout"

        # Data directory
        # Remote desktop
        if '/Users/anjianli/anaconda3/envs/hcl-env/lib/python3.8' not in sys.path:
            if self.scenario_predict == "intersection":
                self.file_dir_predict = '/home/anjianl/Desktop/project/optimized_dp/data/intersection-data'
            elif self.scenario_predict == "roundabout":
                self.file_dir_predict = '/home/anjianl/Desktop/project/optimized_dp/data/roundabout-data'
        else:
        # My laptop
            if self.scenario_predict == "intersection":
                self.file_dir_predict = '/Users/anjianli/Desktop/robotics/project/optimized_dp/data/intersection-data'
            elif self.scenario_predict == "roundabout":
                self.file_dir_predict = '/Users/anjianli/Desktop/robotics/project/optimized_dp/data/roundabout-data'

        # File name
        if self.scenario_predict == "intersection":
            # self.file_name_predict = ['car_16_vid_09.csv']
            self.file_name_predict = ['car_16_vid_09.csv', 'car_20_vid_09.csv', 'car_29_vid_09.csv',
                                      'car_36_vid_11.csv', 'car_50_vid_03.csv', 'car_112_vid_11.csv',
                                      'car_122_vid_11.csv',
                                      'car_38_vid_02.csv', 'car_52_vid_07.csv', 'car_73_vid_02.csv',
                                      'car_118_vid_11.csv']
        elif self.scenario_predict == "roundabout":
            self.file_name_predict = ['car_27.csv', 'car_122.csv',
                                      'car_51.csv', 'car_52.csv', 'car_131.csv', 'car_155.csv',
                                      'car_15.csv', 'car_28.csv', 'car_34.csv', 'car_41.csv', 'car_50.csv',
                                      'car_61.csv', 'car_75.csv', 'car_80.csv']

        # Format of action_bound_mode is
        # [Mode name, acc_min, acc_max, omega_min, omega_max]
        # self.action_bound_mode = Clustering().get_clustering()
        # Based on previous clustering results, we can directly use here
        self.action_bound_mode = [['Mode 0', -2.1636535520436913, -0.513334427671972, -0.1837438265538242, 0.14882615871461266],
                                  ['Mode 1', -0.5555900044464422, 0.6368061679286323, -0.10672453116249359, 0.0937009227063485],
                                  ['Mode 2', 0.5675504765784698, 2.3678900486350067, -0.1821945586149165, 0.2148259198174678],
                                  ['Mode 3', -1.0193550912212208, 1.193433834690333, 0.06677024971223634, 0.2867006433643877],
                                  ['Mode 4', -0.7528328172149713, 1.4532616101602789, -0.3362774352874647, -0.07441345056922757],
                                  ['Mode 5', -1.3550939085936016, 1.8479464013576148, 0.23781317772082264, 0.5235987755982989]]
        # print(self.action_bound_mode)

    def predict_mode(self):

        for file in self.file_name_predict:
            # Get raw action data from traj file
            raw_acc_list, raw_omega_list = self.get_predict_traj(scenario=self.scenario_predict, traj_file_pred=file)

            # How to deal with outliers
            filter_acc_list, filter_omega_list = self.filter_action(raw_acc_list, raw_omega_list)

            # Get mode and plot
            for i in range(len(filter_acc_list)):
                filter_acc, filter_omega = filter_acc_list[i], filter_omega_list[i]

                mode_num_list, mode_probability_list = self.get_mode(filter_acc, filter_omega)

                if self.to_plot_pred_mode:
                    print("new prediction starts")
                    self.plot_mode(mode_num_list, mode_probability_list, filter_acc, filter_omega)

                if self.to_save_pred_mode:
                    if self.plot_probability:
                        if self.scenario_predict == "intersection":
                            figure_name = "intersection_" + file + "_plot{:d}".format(i) + "_probability.png"
                        elif self.scenario_predict == "roundabout":
                            figure_name = "roundabout_" + file + "_plot{:d}".format(i) + "_probability.png"
                    else:
                        if self.scenario_predict == "intersection":
                            figure_name = "intersection_" + file + "_plot{:d}".format(i) + ".png"
                        elif self.scenario_predict == "roundabout":
                            figure_name = "roundabout_" + file + "_plot{:d}".format(i) + ".png"
                    # Configure file path
                    file_path = "/Users/anjianli/Desktop/robotics/project/prediction-reachability/prediction/0915/"
                    figure_path_name = file_path + figure_name
                    # print(figure_path_name)
                    if not os.path.exists(file_path):
                        os.mkdir(file_path)
                    plt.savefig(figure_path_name)

    def get_predict_traj(self, scenario, traj_file_pred=None):

        if traj_file_pred is None:
            # If not specified, then randomly pick a file
            random.seed(13)
            index = random.randint(0, len(self.file_name_predict) - 1)
            traj_file_name = self.file_dir_predict + '/' + self.file_name_predict[index]
            # print("the traj file to predict is", traj_file_name)

            traj_file = ProcessPrediction().read_prediction(file_name=traj_file_name)
        else:
            traj_file_name = self.file_dir_predict + '/' + traj_file_pred
            # print("the traj file to predict is", traj_file_name)

            traj_file = ProcessPrediction().read_prediction(file_name=traj_file_name)

        raw_traj = ProcessPrediction().extract_traj(traj_file)

        # Fit polynomial for x, y position: x(t), y(t)
        poly_traj = ProcessPrediction().fit_polynomial_traj(raw_traj)

        if ProcessPrediction().use_velocity:
            # Get the acc from velocity profile provided
            raw_acc_list, raw_omega_list = ProcessPrediction().get_action_v_profile(raw_traj, poly_traj)
        else:
            # Get raw actions from poly_traj, here acc and omega are extracted from both poly_traj
            raw_acc_list, raw_omega_list = ProcessPrediction().get_action_poly(poly_traj)

        return raw_acc_list, raw_omega_list

    def filter_action(self, raw_acc_list, raw_omega_list):

        filter_acc_list = []
        filter_omega_list = []

        for i in range(len(raw_acc_list)):
            if np.shape(raw_acc_list[i])[0] < ProcessPrediction().mode_time_span:
                print("not qualified", np.shape(raw_acc_list[i])[0])
                continue
            # print("raw omega", raw_omega_list[i])
            acc_interpolate, omega_interpolate = ProcessPrediction().to_interpolate(raw_acc_list[i], raw_omega_list[i], mode="prediction")
            # print("acc size", np.shape(acc_interpolate)[0])
            # print("filter omega", omega_interpolate)
            filter_acc_list.append(acc_interpolate)
            filter_omega_list.append(omega_interpolate)


        return filter_acc_list, filter_omega_list

    def get_mode(self, raw_acc, raw_omega):

        mode_num_list = []
        mode_probability_list = []
        for i in range(np.shape(raw_acc)[0]):
            if i + ProcessPrediction().mode_time_span <= np.shape(raw_acc)[0]:
                curr_mode_num, curr_mode_probability = self.decide_mode(raw_acc[i:i + ProcessPrediction().mode_time_span],
                                                                raw_omega[i:i + ProcessPrediction().mode_time_span])
                # print(curr_mode_str)
                mode_num_list.append(curr_mode_num)
                mode_probability_list.append(curr_mode_probability)
            else:
                mode_num_list.append(curr_mode_num)
                mode_probability_list.append(curr_mode_probability)

        return np.asarray(mode_num_list), mode_probability_list

    def decide_mode(self, acc, omega):
        """
        Major update after predict_mode_v3:

        Because the action bound has some overlap, we will assign probability to the driving mode if the data is in the overlap

        Here, we will compute the shortest distance to the boundary
        """

        if (np.shape(acc)[0] != ProcessPrediction().mode_time_span) or (np.shape(omega)[0] != ProcessPrediction().mode_time_span):
            print("prediction dimension is wrong")
            return 0

        acc_mean = np.mean(acc)
        omega_mean = np.mean(omega)

        mode_probability = [0] * Clustering().clustering_num
        for i in range(Clustering().clustering_num):
            if (self.action_bound_mode[i][1] <= acc_mean <= self.action_bound_mode[i][2]) and (self.action_bound_mode[i][3] <= omega_mean <= self.action_bound_mode[i][4]):
                # Assign the shortest distance to the boundary to
                shortest_dist = np.min([np.abs(acc_mean - self.action_bound_mode[i][1]),
                                        np.abs(acc_mean - self.action_bound_mode[i][2]),
                                        np.abs(omega_mean - self.action_bound_mode[i][3]),
                                        np.abs(omega_mean - self.action_bound_mode[i][4])])
                if shortest_dist == 0:
                    mode_probability[i] = 1
                    for j in range(i+1, Clustering().clustering_num):
                        mode_probability[j] = 0
                    return i, mode_probability
                else:
                    mode_probability[i] = 1 / shortest_dist
            else:
                mode_probability[i] = 0

        if max(mode_probability) == 0:
            return -1, mode_probability

        num_sum = sum(mode_probability)
        for i in range(len(mode_probability)):
            mode_probability[i] = mode_probability[i] / num_sum

        # print(mode_probability)
        # print(np.max(mode_probability))

        # Currently, choose mode as the maximum probability
        mode = mode_probability.index(max(mode_probability))
        return mode, mode_probability

    def plot_mode(self, mode_num_list, mode_probability_list, acc, omega):

        fig = plt.figure()
        ax1 = fig.add_subplot(311)

        time_index = np.linspace(0, np.shape(mode_num_list)[0], num=np.shape(mode_num_list)[0])
        # print(mode_num_seq)
        # print(time_index)

        # Plot mode prediction
        ax1.plot(time_index, mode_num_list, 'o-')
        ax1.grid()
        ax1.set_ylabel('mode')
        ax1.set_xlabel('timestep')
        ax1.set_title('0: decelerate, 1: stable, 2: accelerate, 3: left turn, 4: right turn, 5: curve path, -1: other')

        locs, labels = plt.xticks()
        plt.xticks(np.arange(0, np.shape(mode_num_list)[0], step=ProcessPrediction().mode_time_span))
        plt.yticks(np.arange(-1, Clustering().clustering_num, step=1))

        # Plot acceleration raw data
        ax2 = fig.add_subplot(312, sharex=ax1)
        ax2.plot(time_index, acc, 'o-')
        ax2.set_ylabel('acceleration')
        ax2.set_xlabel('physical bound [-5, 3]')

        # Plot angular speed raw data
        ax3 = fig.add_subplot(313, sharex=ax1)
        ax3.plot(time_index, omega, 'o-', label="angular speed")
        ax3.set_ylabel('angular speed')
        label_name = "bound: acc:[-5, 3], ang_v: [-pi/6, pi/6]" + str(ProcessPrediction().mode_time_span) + "time span"
        ax3.set_xlabel(label_name)

        # Plot mode prediction proability
        if self.plot_probability:
            mode_probability_numpy = np.asarray(mode_probability_list)
            df = pd.DataFrame(dict(
                mode0=mode_probability_numpy[:, 0],
                mode1=mode_probability_numpy[:, 1],
                mode2=mode_probability_numpy[:, 2],
                mode3=mode_probability_numpy[:, 3],
                mode4=mode_probability_numpy[:, 4],
                mode5=mode_probability_numpy[:, 5]
            ))
            df.plot.bar(stacked=True)

        if not self.to_save_pred_mode:
            plt.show()


if __name__ == "__main__":
    PredictMode().predict_mode()
