from itertools import izip
import numpy as np
from scipy.sparse import spdiags,linalg,eye


class Space(object) :
	chemicals = []
	swarms = []

	def __init__(self) :
		mx = (self.size_x[1]-self.size_x[0])/self.resolution
		my = (self.size_y[1]-self.size_y[0])/self.resolution
		assert abs(int(round(mx))-mx) < 1e-8
		assert abs(int(round(my))-my) < 1e-8

		self._mx = int(round(mx)+1)
		self._my = int(round(my)+1)

		self._II = eye(self._mx*self._my,self._mx*self._my)
		self._A = self._five_pt_laplacian_sparse();


	def init(self) :
		"""initialize system"""
		def random_pos() :
			b = np.array([self.size_x[1], self.size_y[1]])
			a = np.array([self.size_x[0], self.size_y[0]])
			return (b-a) * np.random.random(2) + a

		self.t = 0
		self.fields = np.array([
			np.zeros(self._mx*self._my) for _ in self.chemicals
			# np.random.randn(self._mx*self._my) for _ in self.chemicals
		])
		self.agents = [Agent(random_pos()) for Agent in self.swarms ]


	def integrate(self, dt) :
		"""Advance system time by dt"""
		
		# diffusion and decay
		def diffuse(f,it=iter(self.chemicals)) :
			c = it.next()
			return linalg.spsolve(self._II - dt*c.diffusion*self._A,f) - dt*c.decay*f
		self.fields = np.apply_along_axis(diffuse, -1, self.fields)

		# agent movement
		for agent in self.agents :
			# XXX gradient ascent
			dis = agent.displacement * dt**-0.5 * np.random.uniform(-1,1,2)
			agent.pos += self._clip(agent.pos, dis)
		
		# reaction
		for agent in self.agents :
			i = self._pos_to_index(*agent.pos)
			self.fields[:,i] += dt/self.resolution**2 * agent.reaction(self.fields[:,i]) 

		# XXX agent uptake/release

		for agent in self.agents :
			# adhere to clock cycle
			if self.t % agent.clock > agent.clock : continue

			# set agent sensors
			for sensor in agent.sensors.values() :
				i = self.chemicals.index(sensor.chemical)
				c = self.fields[i,self._pos_to_index(*agent.pos)]
				sensor.value = c >= sensor.threshold

			# agent transitions
			inp = agent.state, tuple(s.value for s in agent.sensors.values())
			agent.state = agent.transitions[inp]


		self.t += dt
		return dt


	def _clip(self, pos, dis, border=1e-5) :
		npos = pos+dis
		if npos[0] < self.size_x[0] :
			dis *= -(pos[0]-self.size_x[0])/dis[0]
		elif npos[0] >= self.size_x[1] :
			dis *= (self.size_x[1]-pos[0]-border)/dis[0]
		npos = pos+dis
		if npos[1] < self.size_y[0] :
			dis *= -(pos[1]-self.size_y[0])/dis[1]
		elif npos[1] >= self.size_y[1] :
			dis *= (self.size_y[1]-pos[1]-border)/dis[1]
		return dis


	def _pos_to_index(self, x,y) :
		a = 1.*self.size_x[0]; b = 1.*self.size_x[1]; m = self._mx-1
		ind = int((x-a)/(b-a)*m)
		a = 1.*self.size_y[0]; b = 1.*self.size_y[1]; m = self._my-1
		ind += int((y-a)/(b-a)*m)*(self._mx)
		if ind < 0 or ind >= (self._mx)*(self._my-1) :
			raise ValueError('pos outside bounds: (%.2f,%.2f)' % (x,y))
		return ind


	def _five_pt_laplacian_sparse(self) :
		"Construct a sparse matrix that applies the 5-point laplacian discretization"
		# XXX different boundary conditions
		# http://www.scientificpython.net/1/post/2013/01/neumann-conditions-for-finite-differences-three-different-ways.html
		mx = self._mx; my = self._my
		e = np.ones(mx*my)
		e2 = ([1]*(mx-1)+[0])*my
		e3 = ([0]+[1]*(mx-1))*my
		A = spdiags([-4*e,e2,e3,e,e],[0,-1,1,-mx,mx],mx*my,mx*my)
		A /= self.resolution**2
		return A


class Chemical(object) :
	diffusion = 0.
	decay = 0.


class Agent(object) :
	sensors = {}
	actuators = {}
	transitions = {}
	
	reaction = lambda agent, conc : 0

	displacement = 0

	def __init__(self, pos) :
		self.state = self.states[0]
		self.pos = pos

		self.transitions = {
			(inp[0], tuple(s in inp[1:] for s in self.sensors)) : out
			for inp,out in self.transitions.items()
		}


	@classmethod
	def when_active(cls, actuator, true_val, false_val) :
		def when_active(agent) :
			return true_val if agent.is_active(actuator) else false_val
		when_active.__doc__ = "%s if '%s' else %s" % (true_val, actuator, false_val)
		return property(when_active)

	def is_active(self, actuator) :
		return self.state in self.actuators[actuator].active


class Sensor(object) :
	def __init__(self, chemical, threshold) :
		self.chemical = chemical
		self.threshold = threshold
		self.value = False


class Actuator(object) :
	def __init__(self, active) :
		self.active = active

