from api import *


class Pheromone_A(Chemical) :
	diffusion = 1.
	decay = 0.01

class Pheromone_B(Chemical) :
	diffusion = 1.
	decay = 0.01

class Material(Chemical) :
	decay = 0.001


class Start(Agent) :
	clock = 1
	pos = 10,50

	reaction = lambda agent, conc : (1.0, 0.0, 0.0)

class Finish(Agent) :
	clock = 1
	pos = 90,50

	reaction = lambda agent, conc : (0.0, 1.0, 0.0)

class Worker(Agent) :
	states = 'free', 'ascending'

	clock = 0.1

	sensors = {
		'near_start'  : Sensor(Pheromone_A, 0.5),
		'near_finish' : Sensor(Pheromone_B, 0.5),
	}

	actuators = {
		'explore'  : Actuator('free'),
		'generate' : Actuator('ascending'),
	}

	transitions = {
		('free',      'near_start',  'near_finish' ) : 'free',
		('free',      'near_start',  '^near_finish') : 'ascending',
		('free',      '^near_start', 'near_finish' ) : 'free',
		('free',      '^near_start', '^near_finish') : 'free',
		('ascending', 'near_start',  'near_finish' ) : 'ascending',
		('ascending', 'near_start',  '^near_finish') : 'ascending',
		('ascending', '^near_start', 'near_finish' ) : 'free',
		('ascending', '^near_start', '^near_finish') : 'ascending',
	}

	ascent = {
		Pheromone_A : Agent.actuated('explore', 1.0, 0.0),
		Pheromone_B : Agent.actuated('generate', 1.0, 0.0),
	}

	displacement = 0.5

	r = Agent.actuated('generate', 0.1, 0.0)

	reaction = lambda agent, conc : (0.0, 0.0, agent.r)


class Space(Space) :
	size_x = 0,100
	size_y = 0,100
	resolution = 1.

	chemicals = [Pheromone_A, Pheromone_B, Material]
	swarms = [Start] + [Finish] + 48*[Worker]

