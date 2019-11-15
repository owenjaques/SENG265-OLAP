#!/usr/bin/env python3

import argparse
import os
import sys
import csv

class Group:
	"""
	just a little helper class to hold each group's variables
	must be initialized with the parsed arguments from the argparse function
	"""
	def __init__(self, args):
		self.counter = 0
		self.minimums = {}
		self.maximums = {}
		self.means = {}
		self.sums = {}
		self.tops = {}

		#initialize sum dict
		if args.sums:
			for s in args.sums:
				self.sums[s] = 0

		#add the means required to calculate as well
		if args.mean:
			for m in args.mean:
				self.sums[m] = 0

		if args.top:
			for t in args.top:
				self.tops[t[1]] = {'k': int(t[0]), 'all': {}}

def get_args():
	"""
	gets the command line arguments then returns them in a parsed format
	"""
	parser = argparse.ArgumentParser(description="This is OLAP.py")
	parser.add_argument('--input', dest='input_file', required=True)
	parser.add_argument('--group-by', dest='group_by')
	parser.add_argument('--top', dest='top', nargs=2, action='append')
	parser.add_argument('--min', dest='minimum', action='append')
	parser.add_argument('--max', dest='maximum', action='append')
	parser.add_argument('--mean', dest='mean', action='append')
	parser.add_argument('--sum', dest='sums', action='append')
	parser.add_argument('--count', dest='counter', action='store_true')
	return parser.parse_args()

def get_values(args):
	"""
	computes all the values requested from the parsed arguments 
	param: the parsed arguments from get_args()
	returns: a list of group objects with all the requested data inside each, if no 
	group data was requested it will serve the reqested data of the entire input file
	"""

	groups = {} #holds all the groups
	#sets the grouper variable which tells the program where to place the things being calculated
	if args.group_by:
		grouper = args.group_by
	else:
		grouper = False
		groups['All'] = Group(args)

	#flags to show whether or not something should be calculated
	find_count = True if len(sys.argv) == 3 or args.counter else False #goes off if their are no aggregrate arguments as well
	find_minimums = True if args.minimum else False
	find_maximums = True if args.maximum else False
	find_count = True if args.mean else False
	find_tops = True if args.top else False
	find_sums = True if args.sums or args.mean else False

	with open(args.input_file) as the_file:
		reader = csv.DictReader(the_file, delimiter=',')
		for row in reader:
			#determines which group its reading
			current_group = 'All' if not grouper else row[grouper]

			#creates the group if it doesnt already exist
			if current_group not in groups:
				groups[current_group] = Group(args)

			if find_count:
				groups[current_group].counter += 1
			
			if find_minimums:
				for m in args.minimum:
					num = float(row[m])
					if m in groups[current_group].minimums:
						if num < groups[current_group].minimums[m]:
							groups[current_group].minimums[m] = num
					else:
						groups[current_group].minimums[m] = num

			if find_maximums:
				for m in args.maximum:
					num = float(row[m])
					if m in groups[current_group].maximums: 
						if num > groups[current_group].maximums[m]:
							groups[current_group].maximums[m] = num
					else:
						groups[current_group].maximums[m] = num

			if find_sums:
				for s in groups[current_group].sums.keys():
					groups[current_group].sums[s] += float(row[s])

			if find_tops:
				for t in groups[current_group].tops.keys():
					if row[t] in groups[current_group].tops[t]['all']:
						groups[current_group].tops[t]['all'][row[t]] += 1
					else:
						groups[current_group].tops[t]['all'][row[t]] = 1

	#finds the means
	if args.mean:
		for g in groups.keys():
			for m in args.mean:
				groups[g].means[m] = groups[g].sums[m] / groups[g].counter

	#finds the k amount of tops
	if find_tops:
		for g in groups.keys():
			max_tops = {}
			for t in groups[g].tops.keys():
				#first converts the dictionary of tops to a two dimensional list
				tops_but_as_a_list = [[k, v] for k, v in groups[g].tops[t]['all'].items()]
				#then sorts the list using a key that only looks at the second value of the inner list
				sorted_values = sorted(tops_but_as_a_list, reverse=True, key=lambda top: top[1])
				#isolates just the top k values
				k_maxes = sorted_values[0: groups[g].tops[t]['k']]
				#makes the string
				max_tops[t] = ""
				for i in range(len(k_maxes)):
					max_tops[t] += str(k_maxes[i][0]) + ': ' + str(k_maxes[i][1])
					if i != len(k_maxes) - 1:
						max_tops[t] += ', '
			groups[g].tops = max_tops

	return groups

def print_file(groups):
	"""
	prints the results of the requested arguments to the file in the order they were given in csv format
	accepts as parameters dictionaries of various calculated values and the count (int)
	"""
	ordered_args = sys.argv[1:]
	fieldnames = []

	#creates the rows to prevent index out of bound errors
	rows = [{} for _ in range(len(groups.keys()))]

	for i in range(len(ordered_args)):
		#makes sure it won't reach out of index
		if i != len(ordered_args) - 1:
			k = ordered_args[i+1]

		new_i = 0 #for changing i mid loop without affecting comparisons

		#adds every group's value to the rows for the current fieldname
		for z, g in enumerate(groups.keys()):
			if ordered_args[i] == '--count':
				if z == 0:
					fieldnames.append('count')
				rows[z]['count'] = groups[g].counter

			elif ordered_args[i] == '--min':
				if z == 0:
					fieldnames.append('min_' + k)
					new_i = i + 1
				rows[z]['min_' + k] = groups[g].minimums[k]

			elif ordered_args[i] == '--max':
				if z == 0:
					fieldnames.append('max_' + k)
					new_i = i + 1
				rows[z]['max_' + k] = groups[g].maximums[k]
			
			elif ordered_args[i] == '--sum':
				if z == 0:
					fieldnames.append('sum_' + k)
					new_i = i + 1
				rows[z]['sum_' + k] = groups[g].sums[k]

			elif ordered_args[i] == '--mean':
				if z == 0:
					fieldnames.append('mean_' + k)
					new_i = i + 1
				rows[z]['mean_' + k] = groups[g].means[k]

			elif ordered_args[i] == '--top':
				if z == 0:
					fieldnames.append('top' + k + '_' + ordered_args[i+2])
					new_i = i + 2
				rows[z]['top' + k + '_' + ordered_args[i+2]] = groups[g].tops[ordered_args[i+2]]

			elif ordered_args[i] == '--group-by':
				if z == 0:
					fieldnames.append(k)
					new_i = i + 1
				rows[z][k] = g
		
		i = new_i

	#outputs the csv to the stdout
	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
	writer.writeheader()
	writer.writerows(rows)

def main():
	print_file(get_values(get_args()))

if __name__ == '__main__':
	main()
