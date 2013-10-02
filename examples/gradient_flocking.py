from api import *

class Pheromone(Chemical) :
	diffusion = 1.
	decay = 0.01

class Flocker(Agent) :
	states = 'free',

	clock = .1

	ascent = {
		Pheromone : 0.5,
	}

	displacement = 1.0

	reaction = lambda agent, conc : 0.4

class Space(Space) :
	size_x = 0,100
	size_y = 0,100
	resolution = 1.

	chemicals = [Pheromone]
	swarms = 50*[Flocker]

