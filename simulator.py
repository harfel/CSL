import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap
from scipy.sparse import spdiags,linalg,eye
from time import sleep

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


import sys
model = __import__(sys.argv[1])

#import example as model
space = model.Space()
space.init()

x = np.linspace(space.size_x[0], space.size_x[1], space._mx)
y = np.linspace(space.size_y[0], space.size_y[1], space._my)

plt.ion()

while True :
	space.integrate(dt=space.resolution/2)

	if True :
		plt.clf()

		# chemical field
		U=space.fields[0].reshape((space._my,space._mx))
		plt.pcolormesh(x,y,U, norm=norm, cmap=cmap)
		plt.colorbar
		plt.axis('image')
		plt.title(str(space.t))
		
		# agents
		i = [a.pos[0] for a in space.agents]
		j = [a.pos[1] for a in space.agents]
		plt.scatter(i,j)
		plt.draw()

plt.ioff()


