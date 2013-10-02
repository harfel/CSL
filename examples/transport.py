from api import *


class Pheromone_A(Chemical) :
	diffusion = 1.
	decay = 0.01

class Pheromone_B(Chemical) :
	diffusion = 1.
	decay = 0.01

class Material(Chemical) :
	diffusion = 0.01
	initial = 0.5

class Start(Agent) :
	clock = 1
	pos = 25,75

	reaction = lambda agent, conc : (10.0, 0.0, 0.0)

class Target(Agent) :
	clock = 1
	pos = 90,10

	reaction = lambda agent, conc : (0.0, 10.0, 0.0)

class Worker(Agent) :
	states = 'empty', 'free', 'transport', 'release'

	clock = 0.1

	sensors = {
		'at_start'  : Sensor(Pheromone_A, 0.5),
		'at_target' : Sensor(Pheromone_B, 0.5),
		'loaded'    : ReservoirSensor(Material, 0.1),
		'full'      : ReservoirSensor(Material, 10.0),
	}

	actuators = {
		'return'  : Actuator('empty'),
		'explore' : Actuator('free'),
		'move'    : Actuator('transport'),
		'dispose' : Actuator('release')
	}

	transitions = {
		('empty',      'loaded',  'full', '^at_start',  'at_target') : 'release',
		('empty',      'loaded',  'full',  'at_start', '^at_target') : 'transport',
		('empty',      'loaded',  'full', '^at_start', '^at_target') : 'transport',
		('empty',      'loaded', '^full', '^at_start',  'at_target') : 'empty',
		('empty',      'loaded', '^full',  'at_start', '^at_target') : 'free',
		('empty',      'loaded', '^full', '^at_start', '^at_target') : 'empty',
		('empty',     '^loaded', '^full', '^at_start',  'at_target') : 'empty',
		('empty',     '^loaded', '^full',  'at_start', '^at_target') : 'free',
		('empty',     '^loaded', '^full', '^at_start', '^at_target') : 'empty',
		('free',       'loaded',  'full', '^at_start',  'at_target') : 'release',
		('free',       'loaded',  'full',  'at_start', '^at_target') : 'transport',
		('free',       'loaded',  'full', '^at_start', '^at_target') : 'transport',
		('free',       'loaded', '^full', '^at_start',  'at_target') : 'release',
		('free',       'loaded', '^full',  'at_start', '^at_target') : 'free',
		('free',       'loaded', '^full', '^at_start', '^at_target') : 'free',
		('free',      '^loaded', '^full', '^at_start',  'at_target') : 'release',
		('free',      '^loaded', '^full',  'at_start', '^at_target') : 'free',
		('free',      '^loaded', '^full', '^at_start', '^at_target') : 'empty',
		('transport',  'loaded',  'full', '^at_start',  'at_target') : 'release',
		('transport',  'loaded',  'full',  'at_start', '^at_target') : 'transport',
		('transport',  'loaded',  'full', '^at_start', '^at_target') : 'transport',
		('transport',  'loaded', '^full', '^at_start',  'at_target') : 'empty',
		('transport',  'loaded', '^full',  'at_start', '^at_target') : 'free',
		('transport',  'loaded', '^full', '^at_start', '^at_target') : 'empty',
		('transport', '^loaded', '^full', '^at_start',  'at_target') : 'empty',
		('transport', '^loaded', '^full',  'at_start', '^at_target') : 'free',
		('transport', '^loaded', '^full', '^at_start', '^at_target') : 'empty',
		('release',    'loaded',  'full', '^at_start',  'at_target') : 'release',
		('release',    'loaded',  'full',  'at_start', '^at_target') : 'transport',
		('release',    'loaded',  'full', '^at_start', '^at_target') : 'transport',
		('release',    'loaded', '^full', '^at_start',  'at_target') : 'release',
		('release',    'loaded', '^full',  'at_start', '^at_target') : 'free',
		('release',    'loaded', '^full', '^at_start', '^at_target') : 'transport',
		('release',   '^loaded', '^full', '^at_start',  'at_target') : 'empty',
		('release',   '^loaded', '^full',  'at_start', '^at_target') : 'free',
		('release',   '^loaded', '^full', '^at_start', '^at_target') : 'empty',
	}

	ascent = {
		Pheromone_A : Agent.actuated('return', 2.0, 0.0),
		Pheromone_B : Agent.actuated('move', 2.0, 0.0),
	}

	displacement = Agent.actuated('move', 0.1, 1.0)

	r1 = Agent.actuated('explore', 1.0, 0.0)
	r2 = Agent.actuated('dispose', 0.1, 0.0)

	exchange = lambda agent, c : (0.0, 0.0, agent.r1*c[2]-agent.r2*agent.reservoir[2])

class SystemSpace(Space) :
	size_x = 0,100
	size_y = 0,100
	resolution = 1.

	chemicals = [Pheromone_A, Pheromone_B, Material]
	swarms = [Start] + [Target] + 50*[Worker]

