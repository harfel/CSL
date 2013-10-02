"""Chemical Swarm Programming Interface.

Chemical Swarm programs should start with the line

	from api import *

In a chemical swarm program, there has to be exactly one instance of a
subclass of Space. This subclass has to be either defined in the program
file, or imported from another module (see the examples package).
"""
import abc
import numpy as np
from scipy.sparse import spdiags,linalg,eye


class Space(object) :
	"""Simulation space base class.

	Subclasses need to implement the attributes size_x, size_y, and
	resolution. In addition they can (and usually do) implement the
	attributes chemicals and swarms.
	"""
	__metaclass__ = abc.ABCMeta

	@abc.abstractproperty
	def size_x(self) :
		"Tuple of real numbers defining left and right boundary coordinates."
		return None,None

	@abc.abstractproperty
	def size_y(self) :
		"Tuple of real numbers defining bottom and top boundary coordinates."
		return None,None

	@abc.abstractproperty
	def resolution(self) :
		"Numerical resolution of the finite difference PDE discretization."
		return None

	@property
	def chemicals(self) :
		"Sequence of api.Chemical types. Defaults to []."
		return []

	@property
	def swarms(self) :
		"Sequence of embedded api.Agent types. Defaults to []."
		return []

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
		"""Initialize system"""
		def random_pos() :
			b = np.array([self.size_x[1], self.size_y[1]])
			a = np.array([self.size_x[0], self.size_y[0]])
			return (b-a) * np.random.random(2) + a

		self.t = 0
		self.fields = np.array([
			c.initial * np.ones(self._mx*self._my) for c in self.chemicals
		])
		d = self.fields.shape[0]
		self.agents = [
			Agent(d,Agent.pos) if hasattr(Agent, 'pos') else Agent(d,random_pos())
			for Agent in self.swarms
		]


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
		bands = [-4*e,e2,e3,e,e]
		diags = [0,-1,1,-mx,mx]
		A = spdiags(bands,diags,mx*my,mx*my)
		A /= self.resolution**2
		return A

	def _gradient(self, field, (x,y)) :
		# approximate the gradient at position pos as the mean of the gradient
		# between the four nearest meshpoints
		c = self._pos_to_index(x,y)
		e = c+1
		w = c-1
		n = c+self._mx
		s = c-self._mx
		if x-self.size_x[0] < self.resolution :
			dx = 0
		elif self.size_x[1] - x < self.resolution :
			dx = 0
		else :
			dx = 0.5*(field[e]-field[w])/self.resolution
		if y-self.size_y[0] < self.resolution :
			dy = 0
		elif self.size_y[1] - y < self.resolution :
			dy = 0
		else :
			dy = 0.5*(field[n]-field[s])/self.resolution
		return np.array([dx,dy])


class Chemical(object) :
	"""Chemical species base class.
	
	Subclasses can override the attributes:
	- Chemical.diffusion (diffusion constant)
	- Chemical.decay     (decay constant)
	- Chemical.initial   (initial concentration)
	"""
	__metaclass__ = abc.ABCMeta

	diffusion = 0.
	decay = 0.
	initial = 0.


class Agent(object) :
	"""Agent base class.

	Agent instances have the attributes pos, state, and reservoir.
	Pos is a (real) vector within the bounds of Space, state an internal
	state (see below), and reservoir a vector of chemical species with
	the same order as Space.chemicals.

	Agents implement a finite state machine. Agent subclasses should define
	the attribute states as a sequence of state markers (usually strings or
	ints). Agent subclasses are required to implement the attribute clock,
	that determines the speed of state transitions.
	
	Agents interact with the environment by means of sensors and actuators.
	To define interactions, subclasses should define the attributes sensors
	and actuators as dictionaries of name/Sensor or name/Actuator pairs.

	The finite state machine transition matrix can be defined through the
	attribute transitions. This attribute has to be a dictionary whose keys
	are a tuple of internal states (first item) and combinations of sensor
	names. If a sensor name is prefixed with the character '^', the truth
	value of the sensor is inverted in this transition. The transition matrix
	has to define exactly one entry for each combination of internal states
	and sensor values.
	
	Agent subclasses can define the movement attributes displacement and
	ascent. Displacement is a positive number defining the amplitude in a
	Brownian random walk. Ascent is a dictionary of Chemical/real pairs
	that define the speed of the agent relative to the gradient of the
	respective Chemical in the environment.
	
	Agent subclasses can induce chemical reactions and/or exchange material
	with the environment. Agent.reactions and Agent.exchange are functions
	that return sequences (ideally numpy.arrays) of reaction/exchange rates,
	in the same order as Space.chemicals.
	"""
	__metaclass__ = abc.ABCMeta

	@abc.abstractproperty
	def clock(self) :
		"""Clock cycle of the internal state machine."""
		return None

	@property
	def states(self) :
		"Sequence of internal states."
		return (0,)

	@property
	def sensors(self) :
		"Dictionary of name/Sensor pairs."
		return {}

	@property
	def actuators(self) :
		"Dictionary of name/Actuator pairs."
		return {}

	transitions = {}
	
	@property
	def displacement(self) :
		"Random walk amplitude."
		return 0

	@property
	def ascent(self) :
		"Dictionary of Chemical/velocity pairs for gradient ascent."
		return {}

	def reaction(self, conc) :
		"Returns reaction rates for Space.chemicals."
		return 0
		
	def exchange(self, conc) :
		"Returns exchange rates from Space.chemicals to Agent.reservoir."
		return 0

	@classmethod
	def actuated(cls, actuator, true_val, false_val) :
		"""Agent actuations.
		
		Agent.actuated returns an Actuation object that evaluates to
		true_val if the agent.actuator with the name actuator is True
		in the current context, otherwise it evaluates to false_val.
		Example:
		
		class Agent(api.Agent) :
			displacement = Agent.actuated('moving', 1, 0)
		"""
		def when_active(agent) :
			active = agent.state in agent.actuators[actuator].active
			return true_val if active else false_val
		when_active.__doc__ = "%s if '%s' else %s" % (true_val, actuator, false_val)
		return property(when_active)

	def __init__(self, d, pos) :
		self.state = self.states[0]
		self.pos = pos

		self.reservoir = np.array(d*[0.])

		self.transitions = {
			(inp[0], tuple(s in inp[1:] for s in self.sensors)) : out
			for inp,out in self.transitions.items()
		}


class Sensor(object) :
	"""Agent environment sensor.
	
	To be used as values of the Agent.sensors dictionary.
	Sensor(Chemical, threshold) returns a sensor that evaluates to True
	if the concentration of Chemical at the position agent.pos exceeds the
	threshold value, otherwise it evaluates to False.
	"""
	def __init__(self, chemical, threshold) :
		self.chemical = chemical
		self.threshold = threshold
		self.value = False


class ReservoirSensor(Sensor) :
	"""Agent reservoir sensor.
	
	To be used as values of the Agent.sensors dictionary.
	ReservoirSensor(Chemical, threshold) returns a sensor that evaluates
	to True if the concentration of Chemical in agent.reservoir exceeds the
	threshold value, otherwise it evaluates to False.
	"""
	pass


class Actuator(object) :
	"""Actuator object.
	
	Maps a sequence of internal states onto an Actuation.
	Actuations can be used in the mathod Agent.actuated in order to
	determine some Agent properties from the internal Agent state."""
	def __init__(self, *active) :
		"active has to be a sequence and subset of Agent.states."
		self.active = active

