'''
MIT License
Copyright (c) 2019 Fanjin Zeng
This work is licensed under the terms of the MIT license, see <https://opensource.org/licenses/MIT>.  
'''

import numpy as np
from random import random
import matplotlib.pyplot as plt
from matplotlib import collections  as mc
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from collections import deque

class Line():
  ''' Define line '''
  def __init__(self, p0, p1):
        self.p = np.array(p0)
        self.dirn = np.array(p1) - np.array(p0)
        self.dist = np.linalg.norm(self.dirn)
        self.dirn /= self.dist # normalize

  def path(self, t):
        return self.p + t * self.dirn


def Intersection(line, center, radius):
	''' Check line-sphere (circle) intersection '''
	a = np.dot(line.dirn, line.dirn)
	b = 2 * np.dot(line.dirn, line.p - center)
	c = np.dot(line.p - center, line.p - center) - radius * radius

	discriminant = b * b - 4 * a * c
	if discriminant < 0:
		return False

	t1 = (-b + np.sqrt(discriminant)) / (2 * a);
	t2 = (-b - np.sqrt(discriminant)) / (2 * a);

	if (t1 < 0 and t2 < 0) or (t1 > line.dist and t2 > line.dist):
		return False

	return True



def distance(x, y):
	# print(x)
	# print(y)
	return np.linalg.norm(np.array(x) - np.array(y))


def isInObstacle(vex, obstacles, radius):
	for obs in obstacles:
		if distance(obs, vex) < radius:
			return True
	return False


def isThruObstacle(line, obstacles, radius):
	for obs in obstacles:
		if Intersection(line, obs, radius):
			return True
	return False


def nearest(G, vex, obstacles, radius):
	Nvex = None
	Nidx = None
	minDist = float("inf")

	for idx, v in enumerate(G.vertices):
		line = Line(v, vex)
		if isThruObstacle(line, obstacles, radius):
			continue

		dist = distance(v, vex)
		if dist < minDist:
			minDist = dist
			Nidx = idx
			Nvex = v

	return Nvex, Nidx


def newVertex(randvex, nearvex, stepSize):
	dirn = np.array(randvex) - np.array(nearvex)
	length = np.linalg.norm(dirn)
	dirn = (dirn / length) * min (stepSize, length)

	newvex = (nearvex[0]+dirn[0], nearvex[1]+dirn[1], nearvex[2]+dirn[2])
	return newvex


def window(startpos, endpos):
	''' Define seach window - 2 times of start to end rectangle'''
	width = endpos[0] - startpos[0]
	height = endpos[1] - startpos[1]
	length = endpos[2] - startpos[2]
	winx = startpos[0] - (width / 2.)
	winy = startpos[1] - (height / 2.)
	winz = startpos[1] - (length / 2.)
	return winx, winy, winz, width, height, length


def isInWindow(pos, winx, winy, winz, width, height, length):
	''' Restrict new vertex insides search window'''
	if winx < pos[0] < winx+width and \
		winy < pos[1] < winy+height and \
		winz < pos[2] < winz+length:
		return True
	else:
		return False


class Graph:
	''' Define graph '''
	def __init__(self, startpos, endpos):
		self.startpos = startpos
		self.endpos = endpos

		self.vertices = [startpos]
		self.edges = []
		self.success = False

		self.vex2idx = {startpos:0}
		self.neighbors = {0:[]}
		self.distances = {0:0.}

		self.sx = endpos[0] - startpos[0]
		self.sy = endpos[1] - startpos[1]
		self.sz = endpos[2] - startpos[2]

	def add_vex(self, pos):
		try:
			idx = self.vex2idx[pos]
		except:
			idx = len(self.vertices)
			self.vertices.append(pos)
			self.vex2idx[pos] = idx
			self.neighbors[idx] = []
		return idx

	def add_edge(self, idx1, idx2, cost):
		self.edges.append((idx1, idx2))
		self.neighbors[idx1].append((idx2, cost))
		self.neighbors[idx2].append((idx1, cost))


	def randomPosition(self):
		rx = random()
		ry = random()
		rz = random()

		posx = self.startpos[0] - (self.sx / 2.) + rx * self.sx * 2
		posy = self.startpos[1] - (self.sy / 2.) + ry * self.sy * 2
		posz = self.startpos[2] - (self.sz / 2.) + rz * self.sz * 2
		return posx, posy, posz


def RRT(startpos, endpos, obstacles, n_iter, radius, stepSize):
	''' RRT algorithm '''
	G = Graph(startpos, endpos)

	for _ in range(n_iter):
		randvex = G.randomPosition()
		if isInObstacle(randvex, obstacles, radius):
			continue

		nearvex, nearidx = nearest(G, randvex, obstacles, radius)
		if nearvex is None:
			continue

		newvex = newVertex(randvex, nearvex, stepSize)

		newidx = G.add_vex(newvex)
		dist = distance(newvex, nearvex)
		G.add_edge(newidx, nearidx, dist)

		dist = distance(newvex, G.endpos)
		if dist < 2 * radius:
			endidx = G.add_vex(G.endpos)
			G.add_edge(newidx, endidx, dist)
			G.success = True
			#print('success')
			# break
	return G


def RRT_star(startpos, endpos, obstacles, n_iter, radius, stepSize):
	''' RRT star algorithm '''
	G = Graph(startpos, endpos)

	for _ in range(n_iter):
		randvex = G.randomPosition()
		if isInObstacle(randvex, obstacles, radius):
			continue

		nearvex, nearidx = nearest(G, randvex, obstacles, radius)
		if nearvex is None:
			continue

		newvex = newVertex(randvex, nearvex, stepSize)

		newidx = G.add_vex(newvex)
		dist = distance(newvex, nearvex)
		G.add_edge(newidx, nearidx, dist)
		G.distances[newidx] = G.distances[nearidx] + dist

		# update nearby vertices distance (if shorter)
		for vex in G.vertices:
			if vex == newvex:
				continue

			dist = distance(vex, newvex)
			if dist > radius:
				continue

			line = Line(vex, newvex)
			if isThruObstacle(line, obstacles, radius):
				continue

			idx = G.vex2idx[vex]
			if G.distances[newidx] + dist < G.distances[idx]:
				G.add_edge(idx, newidx, dist)
				G.distances[idx] = G.distances[newidx] + dist

		dist = distance(newvex, G.endpos)
		if dist < 2 * radius:
			endidx = G.add_vex(G.endpos)
			G.add_edge(newidx, endidx, dist)
			try:
				G.distances[endidx] = min(G.distances[endidx], G.distances[newidx]+dist)
			except:
				G.distances[endidx] = G.distances[newidx]+dist

			G.success = True
			#print('success')
			# break
	return G



def dijkstra(G):
	'''
	Dijkstra algorithm for finding shortest path from start position to end.
	'''
	srcIdx = G.vex2idx[G.startpos]
	dstIdx = G.vex2idx[G.endpos]

	# build dijkstra
	nodes = list(G.neighbors.keys())
	dist = {node: float('inf') for node in nodes}
	prev = {node: None for node in nodes}
	dist[srcIdx] = 0

	while nodes:
		curNode = min(nodes, key=lambda node: dist[node])
		nodes.remove(curNode)
		if dist[curNode] == float('inf'):
			break

		for neighbor, cost in G.neighbors[curNode]:
			newCost = dist[curNode] + cost
			if newCost < dist[neighbor]:
				dist[neighbor] = newCost
				prev[neighbor] = curNode

	# retrieve path
	path = deque()
	curNode = dstIdx
	while prev[curNode] is not None:
		path.appendleft(G.vertices[curNode])
		curNode = prev[curNode]
	path.appendleft(G.vertices[curNode])
	return list(path)



def plot(G, obstacles, radius, path=None):
	'''
	Plot RRT, obstacles and shortest path
	'''
	px = [x for x, y, z in G.vertices]
	py = [y for x, y, z in G.vertices]
	pz = [z for x, y, z in G.vertices]
	ax = plt.axes(projection='3d')

	for obs in obstacles:
		# circle = plt.Circle(obs, radius, color='red')
		# ax.add_artist(circle)

		u, v = np.mgrid[0:2*np.pi:10j, 0:np.pi:10j]
		x = obs[0] + radius*np.cos(u)*np.sin(v)
		y = obs[1] + radius*np.sin(u)*np.sin(v)
		z = obs[2] + radius*np.cos(v)
		ax.plot_wireframe(x, y, z, color="r")

	ax.scatter(px, py, pz, c='cyan')
	ax.scatter(G.startpos[0], G.startpos[1], G.startpos[2], c='black')
	ax.scatter(G.endpos[0], G.endpos[1], G.endpos[2], c='black')

	lines = [(G.vertices[edge[0]], G.vertices[edge[1]]) for edge in G.edges]
	lc = Line3DCollection(lines, colors='green', linewidths=2)
	ax.add_collection(lc)

	if path is not None:
		paths = [(path[i], path[i+1]) for i in range(len(path)-1)]
		lc2 = Line3DCollection(paths, colors='blue', linewidths=4)
		ax.add_collection(lc2)

	ax.autoscale()
	ax.margins(0.1)
	ax.set_xlabel('x')
	ax.set_ylabel('y')
	ax.set_zlabel('z')
	plt.show()


def pathSearch(startpos, endpos, obstacles, n_iter, radius, stepSize):
	G = RRT_star(startpos, endpos, obstacles, n_iter, radius, stepSize)
	if G.success:
		path = dijkstra(G)
		# plot(G, obstacles, radius, path)
		return path


if __name__ == '__main__':
	startpos = (0., 0., 0.)
	endpos = (5., 5., 5.)
	obstacles = [(1., 1., 1.), (2., 2., 2.), (4., 4., 4.), (4., 2., 2.), (2., 4., 2.), (2., 2., 4.)]
	n_iter = 400
	radius = 0.8
	stepSize = 0.5

	G = RRT_star(startpos, endpos, obstacles, n_iter, radius, stepSize)
	# G = RRT(startpos, endpos, obstacles, n_iter, radius, stepSize)

	if G.success:
		path = dijkstra(G)
		print(path)
		plot(G, obstacles, radius, path)
	else:
		plot(G, obstacles, radius)