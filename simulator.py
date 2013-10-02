"""Simulator of a Chemical Swarm System.

Run the simulator with

$ python simulator.py PROGRAM

where PROGRAM is a python module (without the traling .py) that can be
imported from the current directory. PROGRAM must provide exactly one
instance of a subclass of api.Space. The simulator must be stopped by
a KILL signal.

The simulator displays the time evolution of the system specified in
the program.
"""
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap
from scipy.sparse import spdiags,linalg,eye
import api

cmap = LinearSegmentedColormap('divergent', {
	'red':   [(0.,	0., 0.),
			  (0.5, 1., 1.),
			  (1.,	1., 1.)],
	'green': [(0.,	0., 0.),
			  (0.5, 1., 1.),
			  (1.,	0., 0.)],
	'blue':  [(0.,	1., 1.),
			  (0.5, 1., 1.),
			  (1.,	0., 0.)],
})
norm = Normalize(vmin=0., vmax=1., clip=True)


def integrate(space, dt) :
	"""Advance system time by dt"""

	# diffusion and decay
	def diffuse(u,it=iter(space.chemicals)) :
		c = it.next()
		return linalg.spsolve(space._II - dt*c.diffusion*space._A,u) - dt*c.decay*u
	space.fields = np.apply_along_axis(diffuse, -1, space.fields)

	# agent movement
	for agent in space.agents :
		dis = agent.displacement * dt**-0.5 * np.random.uniform(-1,1,2)
		for chem,speed in agent.ascent.items() :
			field = space.fields[space.chemicals.index(chem)]
			grad = space._gradient(field, agent.pos)
			if grad.any() :
				if isinstance(speed, property) :
					speed = speed.fget(agent)
				dis += dt * speed * grad/np.linalg.norm(grad)
		agent.pos += space._clip(agent.pos, dis)
		
	# reaction
	for agent in space.agents :
		i = space._pos_to_index(*agent.pos)
		dc = agent.reaction(space.fields[:,i])
		if type(dc) is not np.array : dc = np.array(dc)
		space.fields[:,i] += dt/space.resolution**2 * dc

		dc = agent.exchange(space.fields[:,i])
		if type(dc) is not np.array : dc = np.array(dc)
		space.fields[:,i] -= dt/space.resolution**2 * dc
		agent.reservoir += dt/space.resolution**2 * dc

	for agent in space.agents :
		# adhere to clock cycle
		if space.t % agent.clock > dt : continue

		# set agent sensors
		for sensor in agent.sensors.values() :
			i = space.chemicals.index(sensor.chemical)
			if isinstance(sensor, api.ReservoirSensor) :
				u = agent.reservoir[i]
			elif isinstance(sensor, api.Sensor) :
				u = space.fields[i,space._pos_to_index(*agent.pos)]
			sensor.value = u >= sensor.threshold

		# agent transitions
		if agent.transitions :
			inp = agent.state, tuple(s.value for s in agent.sensors.values())
			agent.state = agent.transitions[inp]

	space.t += dt
	return dt


if __name__ == '__main__' :
	import sys
	sys.path.append('.')
	model = __import__(sys.argv[1])

	#import example as model
	space = api.Space.__subclasses__()[0]()
	space.init()

	x = np.linspace(space.size_x[0], space.size_x[1], space._mx)
	y = np.linspace(space.size_y[0], space.size_y[1], space._my)

	plt.ion()

	while True :
		integrate(space, dt=space.resolution/2)

		if True :
			plt.clf()
	
			# chemical field
			U=space.fields[-1].reshape((space._my,space._mx))
			plt.pcolormesh(x,y,U, norm=norm, cmap=cmap)
			plt.colorbar
			plt.axis('image')
			plt.title(str(space.t))
			
			# agents
			i = [a.pos[0] for a in space.agents]
			j = [a.pos[1] for a in space.agents]
			plt.scatter(i,j)
			plt.draw()

			#print [a.reservoir[-1] for a in space.agents]
	plt.ioff()

