__author__ = 'AivanF'
__copyright__ = 'Copyright 2018, AivanF'
__contact__ = 'projects@aivanf.com'
__license__ = """License:
 This software is provided 'as-is', without any express or implied warranty.
 You may not hold the author liable.

 Permission is granted to anyone to use this software for any purpose,
 including commercial applications, and to alter it and redistribute it freely,
 subject to the following restrictions:

 The origin of this software must not be misrepresented. You must not claim
 that you wrote the original software. When use the software, you must give
 appropriate credit, provide a link to the original file, and indicate if changes were made.
 This notice may not be removed or altered from any source distribution."""

from .utils import iscollection, list_of_lists
from .processing import aggfuns
from .table import Table


class Grouped(object):
	def __init__(self, keys, columns, column_indices):
		self.keys = keys
		self.count = len(keys)
		# {'target_column_name': {'new_column_name': function}}
		self.fun = None

		# Indices of key columns in original table
		self.gun = []
		for el in keys:
			self.gun.append(column_indices[el])

		# Columns names of aggregating rows
		self.columns = {}
		# Whether old columns should be saved
		self.column_indices = []
		step = 0
		for cur in columns:
			if cur not in keys:
				self.column_indices.append(True)
				self.columns[cur] = step
				step += 1
			else:
				self.column_indices.append(False)

		# Dict of dict of ... of list with a list of columns
		if self.count > 0:
			self.values = {}
		else:
			self.values = list_of_lists(len(self.columns))

	def add(self, row):
		vals = self.values
		for i in range(self.count):
			last = i == self.count - 1
			ind = self.gun[i]
			cur = row[ind]
			if cur not in vals:
				if last:
					# store columns independently
					vals[cur] = list_of_lists(len(self.columns))
				else:
					# add one more dict layer
					vals[cur] = {}
			vals = vals[cur]

		# Save values with appropriate indices only - not key columns
		step = 0
		for i in range(len(row)):
			if self.column_indices[i]:
				# Columns-first structure
				vals[step].append(row[i])
				step += 1

	def _agglist(self, keys, cols):
		"""Applies aggregation functions on given group."""
		res = keys
		for target_name in self.fun:
			cur_col = cols[self.columns[target_name]]
			for new_name in self.fun[target_name]:
				task = self.fun[target_name][new_name]
				if isinstance(task, str):
					if task in aggfuns:
						# print('Grouped {} -> {} Agg with {}'.format(target_name, new_name, task))
						res.append(aggfuns[task](cur_col))
					else:
						raise ValueError('Aggregation function "{}" does not exist!'.format(task))
				else:
					if callable(task):
						res.append(task(cur_col))
					else:
						raise ValueError('Aggregation function must be a callable!')
		return res

	def _recurs(self, task, vals=None, keys=None):
		"""Recursive method to move through grouping keys.
		Task takes list of keys values and list of columns."""
		vals = self.values if vals is None else vals
		keys = [] if keys is None else keys
		res = []
		if isinstance(vals, dict):
			for key in vals:
				res.extend(self._recurs(task, vals[key], keys + [key]))
		elif iscollection(vals):
			v = task(keys, vals)
			if v is not None:
				res.append(v)
		return res

	def agg(self, fun, default_fun=None):
		"""Returns new Table object from aggregated groups.
		The argument must be a dictionary which keys are old columns names,
		and the values are other dictionaries where keys are new columns names,
		and the values are strings with aggregation functions names or function or lambdas.
		The last argument allows to aggregate all the rows with single or multiple functions.
		"""

		if default_fun is not None:
			for target_name in self.columns:
				if target_name not in fun:
					fun[target_name] = {}
				if isinstance(default_fun, dict):
					for key in default_fun:
						fun[target_name]['{}_{}'.format(target_name, key)] = default_fun[key]
				elif iscollection(default_fun):
					for task in default_fun:
						if not isinstance(task, str):
							raise ValueError('Default functions in a list must be string names!')
						fun[target_name]['{}_{}'.format(target_name, task)] = task
				else:
					fun[target_name][target_name] = default_fun

		for target_name in fun:
			if not isinstance(fun[target_name], dict):
				fun[target_name] = {target_name: fun[target_name]}

		self.fun = fun
		cols = self.keys
		for target_name in fun:
			for new_name in fun[target_name]:
				cols.append(new_name)
		rows = self._recurs(self._agglist)
		return Table(cols, rows, 'Aggregated')

	def _make_group(self, keys, cols, add_keys, pairs):
		t = 'Group '
		for i in range(len(self.keys)):
			t += '{}={} '.format(self.keys[i], keys[i])
		res = Table([], [], t[:-1])
		if add_keys:
			for i in range(len(self.keys)):
				res[self.keys[i]] = [keys[i]] * len(cols[0])
		for el in self.columns:
			res[el] = cols[self.columns[el]]
		if pairs:
			return dict(zip(self.keys, keys)), res
		else:
			return res

	def split(self, add_keys=True, pairs=False):
		"""Returns a list with new Table objects - different groups."""
		return self._recurs(lambda keys, cols: self._make_group(keys, cols, add_keys, pairs))

	def get_group(self, search_keys, add_keys=True):
		"""Returns None or new Table objects as a group with specified keys."""
		search_keys = search_keys if iscollection(search_keys) else [search_keys]
		def findTable(keys, cols):
			well = True
			for i in range(len(keys)):
				if keys[i] != search_keys[i]:
					well = False
					break
			if well:
				return self._make_group(keys, cols, add_keys, pairs=False)
		res = self._recurs(findTable)
		if len(res) > 0:
			return res[0]
		else:
			return None

	def counts(self):
		"""Returns new Table object with counts of the groups."""
		rows = []
		todo = lambda x, y: rows.append(x + [len(y[0])])
		self._recurs(todo)
		return Table(self.keys + ['rows'], rows, 'Groups')

	def _repr_html_(self):
		res = '<b>Grouped</b> object, keys: {}, old columns: {}.<br>\n'.format(
			self.keys, list(self.columns.keys())
		)
		res += self.counts().html()
		return res

	def __repr__(self):
		return '- Grouped object, keys: {}, old columns: {}.'.format(
			self.keys, list(self.columns.keys())
		)
