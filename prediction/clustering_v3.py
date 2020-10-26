import sys
import os
import pickle
sys.path.append("/Users/anjianli/Desktop/robotics/project/optimized_dp")

import numpy as np
import math
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler

from prediction.process_prediction_v3 import *

class ClusteringV3(object):
    """
    Given cleaned data, we first normalize the acc and omega

    Then we set several default driving mode, and then cluster the variance

    """

    def __init__(self):

        self.to_plot = True
        # self.to_save = True

        # self.to_plot = False
        self.to_save = False

        self.clustering_num = 6

        # Clustering feature selection
        # self.clustering_feature_type = "5_default_deviation"
        self.clustering_feature_type = "6_default_distance"
        # self.clustering_feature_type = "only_mean"
        # self.clustering_feature_type = "mean_and_variance"

        self.personalize_initialization = False
        # self.personalize_initialization = True

        # TODO：Hand-tune the mode, DIFFERENT when runing on mac / remote desktop
        self.to_corretify_pred = True
        # self.to_corretify_pred = False


        # Default driving mode
        # Decelerate
        self.default_m1_acc = -1.5
        self.default_m1_omega = 0
        # Maintain
        self.default_m2_acc = 0
        self.default_m2_omega = 0
        # Turn Left
        self.default_m3_acc = 0
        self.default_m3_omega = 0.2
        # Turn right
        self.default_m4_acc = 0
        self.default_m4_omega = - 0.25
        # Accelerate
        self.default_m5_acc = 1.5
        self.default_m5_omega = 0
        # Curve path left
        self.default_m6_acc = 0
        self.default_m6_omega = 0.4
        # # Curve path right
        # self.default_m7_acc = 0.7
        # self.default_m7_omega = - 0.1

        self.time_span = ProcessPredictionV3().mode_time_span

        # For plot comparison
        if ProcessPredictionV3().scenario_to_use == ["intersection", "roundabout"]:
            self.scenario_name = "intersection+roundabout"
        elif ProcessPredictionV3().scenario_to_use == ["intersection"]:
            self.scenario_name = "intersection"
        elif ProcessPredictionV3().scenario_to_use == ["roundabout"]:
            self.scenario_name = "roundabout"

        if ProcessPredictionV3().use_velocity:
            self.use_velocity = "use velocity"
        else:
            self.use_velocity = "only poly"

    def get_clustering(self):

        # The action feature vector is [acc_mean, acc_variance, omega_mean, omega_variance, scenario]
        action_feature = self.get_action_feature()

        # If without scenario, the raw_action_feature is [acc_mean, acc_variance, omega_mean, omega_variance]
        raw_action_feature = np.asarray([[num[0], num[1], num[2], num[3]] for num in action_feature])

        # Form clustering feature from action feature
        clustering_feature = self.get_clustering_feature(raw_action_feature)

        # Kmeans on clustering feature
        prediction = self.kmeans_clustering(clustering_feature)

        # Visualization
        self.plot_clustering(action_feature, raw_action_feature, clustering_feature, prediction)

        # Find the action bound for each mode
        mode_action_bound = self.get_action_bound_for_mode(prediction, raw_action_feature)

        return mode_action_bound

    def get_action_feature(self):

        filename_action_feature_list = ProcessPredictionV3().collect_action_from_group()

        # Concatenate all the actions feature in a big list
        action_feature_list = []

        num_action_feature = 0
        for action_feature in filename_action_feature_list:
            for i in range(np.shape(action_feature[1])[0]):
                # The action feature vector is [acc_mean, acc_variance, omega_mean, omega_variance, scenario]
                action_feature_list.append([action_feature[1][i], action_feature[2][i], action_feature[3][i], action_feature[4][i], action_feature[0]])
                # print([action_feature[1][i], action_feature[2][i], action_feature[3][i], action_feature[4][i], action_feature[0]])
                num_action_feature += 1

        # action_feature_list = np.asarray(action_feature_list)
        print("total number of action feature is ", num_action_feature)

        return action_feature_list

    def get_clustering_feature(self, raw_action_feature):

        # action_feature = [acc_mean, acc_variance, omega_mean, omega_variance]
        if self.clustering_feature_type == "5_default_deviation":
            clustering_feature = np.transpose(np.asarray([raw_action_feature[:, 0], raw_action_feature[:, 2]]))
            normalized_clustering_feature = MinMaxScaler().fit_transform(clustering_feature)

            acc_min = np.min(clustering_feature[:, 0])
            acc_max = np.max(clustering_feature[:, 0])
            omega_min = np.min(clustering_feature[:, 1])
            omega_max = np.max(clustering_feature[:, 1])

            certroid_1 = [(self.default_m1_acc - acc_min) / (acc_max - acc_min), (self.default_m1_omega - omega_min) / (omega_max - omega_min)]
            certroid_2 = [(self.default_m2_acc - acc_min) / (acc_max - acc_min), (self.default_m2_omega - omega_min) / (omega_max - omega_min)]
            certroid_3 = [(self.default_m3_acc - acc_min) / (acc_max - acc_min), (self.default_m3_omega - omega_min) / (omega_max - omega_min)]
            certroid_4 = [(self.default_m4_acc - acc_min) / (acc_max - acc_min), (self.default_m4_omega - omega_min) / (omega_max - omega_min)]
            certroid_5 = [(self.default_m5_acc - acc_min) / (acc_max - acc_min), (self.default_m5_omega - omega_min) / (omega_max - omega_min)]

            normalized_clustering_feature = np.transpose(np.asarray([
                normalized_clustering_feature[:, 0] - certroid_1[0], normalized_clustering_feature[:, 0] - certroid_2[0],
                normalized_clustering_feature[:, 0] - certroid_3[0], normalized_clustering_feature[:, 0] - certroid_4[0],
                normalized_clustering_feature[:, 0] - certroid_5[0],
                normalized_clustering_feature[:, 1] - certroid_1[1], normalized_clustering_feature[:, 1] - certroid_2[1],
                normalized_clustering_feature[:, 1] - certroid_3[1], normalized_clustering_feature[:, 1] - certroid_4[1],
                normalized_clustering_feature[:, 1] - certroid_5[1]
            ]))
        elif self.clustering_feature_type == "6_default_distance":

            clustering_feature = np.transpose(np.asarray([raw_action_feature[:, 0], raw_action_feature[:, 2]]))
            normalized_clustering_feature = MinMaxScaler().fit_transform(clustering_feature)

            acc_min = np.min(clustering_feature[:, 0])
            acc_max = np.max(clustering_feature[:, 0])
            omega_min = np.min(clustering_feature[:, 1])
            omega_max = np.max(clustering_feature[:, 1])

            certroid_1 = [(self.default_m1_acc - acc_min) / (acc_max - acc_min), (self.default_m1_omega - omega_min) / (omega_max - omega_min)]
            certroid_2 = [(self.default_m2_acc - acc_min) / (acc_max - acc_min), (self.default_m2_omega - omega_min) / (omega_max - omega_min)]
            certroid_3 = [(self.default_m3_acc - acc_min) / (acc_max - acc_min), (self.default_m3_omega - omega_min) / (omega_max - omega_min)]
            certroid_4 = [(self.default_m4_acc - acc_min) / (acc_max - acc_min), (self.default_m4_omega - omega_min) / (omega_max - omega_min)]
            certroid_5 = [(self.default_m5_acc - acc_min) / (acc_max - acc_min), (self.default_m5_omega - omega_min) / (omega_max - omega_min)]
            certroid_6 = [(self.default_m6_acc - acc_min) / (acc_max - acc_min), (self.default_m6_omega - omega_min) / (omega_max - omega_min)]

            normalized_clustering_feature = np.transpose(np.asarray([
                np.sqrt((normalized_clustering_feature[:, 0] - certroid_1[0]) ** 2 + (
                            normalized_clustering_feature[:, 1] - certroid_1[1]) ** 2),
                np.sqrt((normalized_clustering_feature[:, 0] - certroid_2[0]) ** 2 + (
                            normalized_clustering_feature[:, 1] - certroid_2[1]) ** 2),
                np.sqrt((normalized_clustering_feature[:, 0] - certroid_3[0]) ** 2 + (
                            normalized_clustering_feature[:, 1] - certroid_3[1]) ** 2),
                np.sqrt((normalized_clustering_feature[:, 0] - certroid_4[0]) ** 2 + (
                            normalized_clustering_feature[:, 1] - certroid_4[1]) ** 2),
                np.sqrt((normalized_clustering_feature[:, 0] - certroid_5[0]) ** 2 + (
                            normalized_clustering_feature[:, 1] - certroid_5[1]) ** 2),
                np.sqrt((normalized_clustering_feature[:, 0] - certroid_6[0]) ** 2 + (
                        normalized_clustering_feature[:, 1] - certroid_6[1]) ** 2)
            ]))
        elif self.clustering_feature_type == "only_mean":
            clustering_feature = np.transpose(np.asarray([raw_action_feature[:, 0], raw_action_feature[:, 2]]))
            normalized_clustering_feature = MinMaxScaler().fit_transform(clustering_feature)
        elif self.clustering_feature_type == "mean_and_variance":
            clustering_feature = np.transpose(np.asarray([raw_action_feature[:, 0], raw_action_feature[:, 2],
                                                          raw_action_feature[:, 1], raw_action_feature[:, 3]]))
            normalized_clustering_feature = MinMaxScaler().fit_transform(clustering_feature)

        # normalized_clustering_feature = MinMaxScaler().fit_transform(clustering_feature)

        return normalized_clustering_feature

    def kmeans_clustering(self, clustering_feature):

        default_centroid = np.asarray([[self.default_m1_acc, self.default_m1_omega],
                                       [self.default_m2_acc, self.default_m2_omega],
                                       [self.default_m3_acc, self.default_m3_omega],
                                       [self.default_m4_acc, self.default_m4_omega],
                                       [self.default_m5_acc, self.default_m5_omega]
                                       ])
        if self.personalize_initialization:
            kmeans_action = KMeans(n_clusters=self.clustering_num, init=default_centroid, n_init=10, max_iter=300).fit(clustering_feature)
        else:
            kmeans_action = KMeans(n_clusters=self.clustering_num, random_state=0).fit(clustering_feature)
        pred = kmeans_action.predict(clustering_feature)

        if self.to_corretify_pred:
            # Unify the mode: 0: decelerate, 1: stable, 2: accelerate, 3: left turn, 4: right turn, 5: curve path
            # TODO: everytime when the clustering changes, we should hand-modify the cluster num
            corrected_pred = np.ones((np.shape(pred)[0]))

            acc_center = kmeans_action.cluster_centers_[:, 0]
            omega_center = kmeans_action.cluster_centers_[:, 1]
            new_mode = np.ones((self.clustering_num)) * 100

            # Hand-design the new mode, the mapping is based on the clustering plot on REMOTE DESKTOP
            # mode: 0: decelerate, 1: stable, 2: accelerate, 3: left turn, 4: right turn, 5: curve path
            # TODO: in remote desktop
            if '/Users/anjianli/anaconda3/envs/hcl-env/lib/python3.8' not in sys.path:
                print("correct mode on remote desktop")
                new_mode[0] = 0
                new_mode[1] = 2
                new_mode[2] = 1
                new_mode[3] = 5
                new_mode[4] = 4
                new_mode[5] = 3
            else:
                # TODO: in my laptop
                print("correct mode on laptop")
                new_mode[0] = 1
                new_mode[1] = 2
                new_mode[2] = 0
                new_mode[3] = 3
                new_mode[4] = 5
                new_mode[5] = 4

            for i in range(self.clustering_num):
                corrected_pred[pred == new_mode[i]] = i

            return np.asarray(corrected_pred, 'i')

        else:
            return pred

    def plot_clustering(self, original_data, raw_data, clustering_data, prediction):

        # First form a list to represent scenario
        scenario = [num[4] for num in original_data]
        # print(len(scenario))
        # print(len(prediction))

        # print(original_data)
        fig, ax = plt.subplots()

        color = ["b", "g", "r", "c", "m", "y"]
        for i in range(self.clustering_num):
            # print(prediction == i)
            intersection_index = [sce == "intersection" for sce in scenario]
            roundabout_index = [sce == "roundabout" for sce in scenario]
            intersection_prediction_index = np.logical_and(prediction == [i], intersection_index)
            roundabout_prediction_index = np.logical_and(prediction == [i], roundabout_index)
            ax.scatter(raw_data[:, 0][intersection_prediction_index], raw_data[:, 2][intersection_prediction_index], label='M%d, i' % i, marker="o", color=color[i], alpha=0.2)
            ax.scatter(raw_data[:, 0][roundabout_prediction_index], raw_data[:, 2][roundabout_prediction_index], label='M%d, r' % i, marker="+", color=color[i])


        ax.set_xlabel('acceleration (m/s^2)')
        ax.set_ylabel('angular speed (rad/s)')
        title = self.use_velocity + ", " + self.scenario_name + ", " + self.clustering_feature_type + ", " + str(self.time_span) + " " + "time-span " + "poly" + str(ProcessPredictionV3().degree)
        # ax.set_title(title)
        ax.legend(fontsize=8)
        if self.to_plot:
            plt.show()

        # figure_name = "kmeans.png"
        # figure_name = "kmeans-initialization.png"
        # figure_name = "kmeans-initialization-7.png"
        # figure_name = "kmeans-no-interpolation.png"
        figure_name = "kmeans-5_default.png"

        file_path = "/Users/anjianli/Desktop/robotics/project/optimized_dp/result/poly_{:d}/{:d}_timesteps/".format(
            ProcessPredictionV3().degree, ProcessPredictionV3().mode_time_span)
        figure_path_name = file_path + figure_name

        if self.to_save:
            # if not os.path.exists(file_path):
            #     os.mkdir(file_path)
            # plt.savefig(figure_path_name)
            plt.savefig("/home/anjianl/Desktop/project/optimized_dp/result/clustering/clustering.png")

        # pickle.dump(kmeans_action, open("/home/anjianl/Desktop/project/optimized_dp/model/kmeans_action_intersection"
        #                                 ".pkl", "wb"))

    def get_action_bound_for_mode(self, prediction, raw_action_feature):

        mode_num = np.max(prediction) + 1
        action_num = np.shape(prediction)[0]

        mode_action_bound = []

        for mode in range(mode_num):
            acc_min = np.min(raw_action_feature[prediction == mode, 0])
            acc_max = np.max(raw_action_feature[prediction == mode, 0])
            omega_min = np.min(raw_action_feature[prediction == mode, 2])
            omega_max = np.max(raw_action_feature[prediction == mode, 2])

            # print("Mode {:d}: acc is in [{:.2f}, {:.2f}], omega is in [{:.2f}, {:.2f}]".format(mode, acc_min, acc_max, omega_min, omega_max))
            mode = "Mode " + str(mode)
            mode_action_bound.append([mode, acc_min, acc_max, omega_min, omega_max])

        return mode_action_bound

if __name__ == "__main__":
    ClusteringV3().get_clustering()
