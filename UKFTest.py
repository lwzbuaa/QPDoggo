import numpy as np
from StateEstimator import UKFStateEstimator
from WooferConfig import WOOFER_CONFIG
import pdb
import quaternion

L = 13

x0 = np.zeros(L)
x0[2] = 0.34
x0[3:7] = np.array([1, 0, 0, 0])

ukf_state_est = UKFStateEstimator(x0, 0.001)

data = np.load('woofer_numpy_log.npz')

n = np.shape(data['state_history'])[1]

n = 1400

state_est = np.zeros((L, n))

state_est[:,0] = x0

for i in range(1, n):
	# accel_meas = data['accelerometer_history'][:, i]

	# accel_u_w_est = -1/WOOFER_CONFIG.MASS * (data['force_sensor_hist'][0:3, i] + data['force_sensor_hist'][3:6, i] + data['force_sensor_hist'][6:9, i] + data['force_sensor_hist'][9:12, i])
	accel_u_w_est = -1/7.166 * (data['force_sensor_hist'][0:3, i] + data['force_sensor_hist'][3:6, i] + data['force_sensor_hist'][6:9, i] + data['force_sensor_hist'][9:12, i])
	accel_meas = quaternion.vectorRotation(quaternion.inv(data['state_history'][3:7,i]), quaternion.fromVector(accel_u_w_est))[1:4]

	print("Force in world frame ", accel_u_w_est)
	# print("Predicted accelerometer measurement: ", accel_meas)

	# gyro_meas = data['gyro_history'][:, i]
	gyro_meas = data['state_history'][10:13,i]

	joint_pos_meas = data['joint_pos_sensor_hist'][:, i]
	joint_vel_meas = data['joint_vel_sensor_hist'][:, i]

	# z_meas = np.concatenate([accel_meas, gyro_meas, joint_pos_meas, joint_vel_meas])
	z_meas = np.concatenate([accel_meas, gyro_meas])

	# u = np.zeros(12)

	u = data['force_history'][:, i-1]
	# u = -data['force_sensor_hist'][:, i-1]

	contacts = data['contacts_history'][:,i]

	u_active = contacts[[0,0,0,1,1,1,2,2,2,3,3,3]] * u
	#
	# if i>30:
	# 	pdb.set_trace()

	# z_meas = np.zeros(6)
	# z_meas[2] = 9.81
	# u_active = np.zeros(12)
	# u_active[2] = WOOFER_CONFIG.MASS * 9.81/4
	# u_active[5] = WOOFER_CONFIG.MASS * 9.81/4
	# u_active[8] = WOOFER_CONFIG.MASS * 9.81/4
	# u_active[11] = WOOFER_CONFIG.MASS * 9.81/4
	#
	state_i = ukf_state_est.update(z_meas, u, contacts)

	state_est[0:3, i] = state_i['p']
	state_est[3:7, i] = state_i['q']
	state_est[7:10, i] = state_i['p_d']
	state_est[10:13, i] = state_i['w']
	state_est[13:16, i] = state_i['b_a']
	state_est[16:19, i] = state_i['b_g']

	# q_true = np.array([1.0, 0.0, 0.0, 0.0])

	q_true = data['state_history'][3:7, i]
	q_est = state_est[3:7,i]

	q_d = quaternion.prod(quaternion.inv(q_est), q_true)
	phi = np.linalg.norm(quaternion.log(q_d))
	phi = np.abs((phi + np.pi) % (2 * np.pi) - np.pi)

	print("Error: ", phi)


np.savez('woofer_state_est_log', state_est)
