from api import *

class Pheromone(Chemical) :
	diffusion = 1.
	decay = 0.01

class Flocker(Agent) :
	states = 'free', 'docked'

	clock = .1

	sensors = {
		'pheromone' : Sensor(Pheromone, 0.5),
	}

	actuators = {
		'immobilize' : Actuator('docked'),
	}

	transitions = {
		('free', 'pheromone') : 'docked',
		('free', '^pheromone') : 'free',
		('docked', 'pheromone') : 'docked',
		('docked', '^pheromone') : 'free',
	}
	
	displacement = Agent.actuated('immobilize', 0.1, 1.)

	reaction = lambda agent, conc : 0.4

class Space(Space) :
	size_x = 0,100
	size_y = 0,100
	resolution = 1.

	chemicals = [Pheromone]
	swarms = 50*[Flocker]

