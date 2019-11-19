#!/usr/bin/env python3

import argparse
import os
import sys
import csv

#TODO: add a way to deal with newlines and " in the tops

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

		#a flag variable to tell if any numeric values have been entered in the sums field
		self.nan_sums = {}

		#initialize minimums dict to NaNs
		if args.minimum:
			for m in args.minimum:
				self.minimums[m] = 'NaN'

		if args.maximum:
			for m in args.maximum:
				self.maximums[m] = 'NaN'

		#initialize sum dict
		if args.sums:
			for s in args.sums:
				self.sums[s] = 0
				self.nan_sums[s] = True

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
	parser = argparse.ArgumentParser(description="This is OLAP.py - for small data only")
	parser.add_argument('--input', dest='input_file', required=True)
	parser.add_argument('--group-by', dest='group_by', type=str.lower)
	parser.add_argument('--top', dest='top', nargs=2, action='append', type=str.lower)
	parser.add_argument('--min', dest='minimum', action='append', type=str.lower)
	parser.add_argument('--max', dest='maximum', action='append', type=str.lower)
	parser.add_argument('--mean', dest='mean', action='append', type=str.lower)
	parser.add_argument('--sum', dest='sums', action='append', type=str.lower)
	parser.add_argument('--count', dest='counter', action='store_true')
	return parser.parse_args()

def non_numeric_value_error(aggregrate_function, non_numeric_tracker, input_file, line_number, aggregrate_field, value):
	"""
	prints a non numeric value error all parameters are fairly straightforard from 
	the name and just for printing except for the non numeric tracker which checks 
	for the non numeric fields getting above 100 which would print an error then exit
	the program with error code 7
	"""
	print('Error: ' + input_file + ':' + str(line_number) + ": can't compute " + aggregrate_function + " on non-numeric value '" + str(value) + "'", file=sys.stderr)
	#in the case the error is raised more than once for example if sum and mean max were all called on the same value
	if line_number not in non_numeric_tracker['line_numbers']:
		non_numeric_tracker['field_counts'][aggregrate_field] += 1
		non_numeric_tracker['line_numbers'].append(line_number)
	if non_numeric_tracker['field_counts'][aggregrate_field] > 100:
		print("Error: " + input_file + ":more than 100 non-numeric values found in aggregate column '" + aggregrate_field + "'", file=sys.stderr)
		sys.exit(7)

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
		groups['_OTHER'] = Group(args)

	#flags to show whether or not something should be calculated
	find_count = True if len(sys.argv) == 3 or args.counter or args.mean or len(sys.argv) == 5 and args.group_by else False #goes off if their are no aggregrate arguments as well
	find_minimums = True if args.minimum else False
	find_maximums = True if args.maximum else False
	find_tops = True if args.top else False
	find_sums = True if args.sums or args.mean else False

	try:
		with open(args.input_file, 'r', encoding='UTF-8-SIG') as the_file:
			reader = csv.DictReader(the_file, delimiter=',')
			reader.fieldnames = [field.lower() for field in reader.fieldnames]
			non_numeric_tracker = {'field_counts': {k: 0 for k in reader.fieldnames}, 'line_numbers': []}

			#calculates all requested aggregrates in one pass by
			for line_number, row in enumerate(reader, start=1):
				#determines which group its reading
				current_group = '_OTHER' if not grouper else row[grouper]

				#creates the group if it doesnt already exist unless there are more then 20...
				if current_group not in groups:
					if len(groups) != 20:
						groups[current_group] = Group(args)
					else:
						groups['_OTHER'] = Group(args)
						print('​Error:' + args.input_file + ':' + grouper +  ' has been capped at 20 distinct values', file=sys.stderr)
						grouper = False
						current_group = '_OTHER'

				if find_count:
					groups[current_group].counter += 1
				
				if find_minimums:
					for m in args.minimum:
						try:
							num = float(row[m])
							if m in groups[current_group].minimums and groups[current_group].minimums[m] != 'NaN':
								if num < groups[current_group].minimums[m]:
									groups[current_group].minimums[m] = num
							else:
								groups[current_group].minimums[m] = num
						except ValueError:
							non_numeric_value_error('min', non_numeric_tracker, args.input_file, line_number, m, row[m])

				if find_maximums:
					for m in args.maximum:
						try:
							num = float(row[m])
							if m in groups[current_group].maximums and groups[current_group].maximums[m] != 'NaN': 
								if num > groups[current_group].maximums[m]:
									groups[current_group].maximums[m] = num
							else:
								groups[current_group].maximums[m] = num
						except ValueError:
							non_numeric_value_error('ax', non_numeric_tracker, args.input_file, line_number, m, row[m])

				if find_sums:
					for s in groups[current_group].sums.keys():
						try:
							groups[current_group].sums[s] += float(row[s])
							groups[current_group].nan_sums[s] = False
						except ValueError:
							if s in args.sums:
								non_numeric_value_error('sum', non_numeric_tracker, args.input_file, line_number, s, row[s])
							if s in args.mean:
								non_numeric_value_error('mean', non_numeric_tracker, args.input_file, line_number, s, row[s])

				if find_tops:
					for t in groups[current_group].tops.keys():
						if row[t] in groups[current_group].tops[t]['all']:
							groups[current_group].tops[t]['all'][row[t]] += 1
						else:
							groups[current_group].tops[t]['all'][row[t]] = 1

	except FileNotFoundError:
		print('Error:' + args.input_file + ':file not found', file=sys.stderr)
		sys.exit(6)

	#sets the NaNs for the sums if nothing was added to the 0
	if args.sums:
		for g in groups.keys():
			for s in args.sums:
				if groups[g].nan_sums[s]:
					groups[g].sums[s] = 'NaN'
	
	#finds the means
	if args.mean:
		for g in groups.keys():
			for m in args.mean:
				groups[g].means[m] = groups[g].sums[m] / groups[g].counter if groups[g].sums[s] != 'NaN' else 'NaN'

	#finds the k amount of tops
	if find_tops:
		for g in groups.keys():
			max_tops = {}
			for t in groups[g].tops.keys():
				#really went off with this next statement. if my style mark suffers so be it, but some might
				#say a snazzy one liner is the most stylish way ;) but forget that here's what it does:
				# first converts the dictionary of tops to a two dimensional list
				# then sorts the list using a key that only looks at the second value of the inner list
				# then isolates just the top k values
				k_maxes = sorted([[k, v] for k, v in groups[g].tops[t]['all'].items()], reverse=True, key=lambda top: top[1])[0: groups[g].tops[t]['k']]
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
	ordered_args = [s.lower() for s in sys.argv[1:]]
	fieldnames = []

	#creates the rows to prevent index out of bound errors
	rows = [{} for _ in range(len(groups.keys()))]

	#a flag for adding the count if there are no aggregrate arguments
	has_been_counted = False

	for i in range(len(ordered_args)):
		#makes sure it won't reach out of index
		if i != len(ordered_args) - 1:
			k = ordered_args[i+1]

		new_i = 0 #for changing i mid loop without affecting comparisons

		#adds every group's value to the rows for the current 
		for z, g in enumerate(sorted(groups.keys())):
			#a flag for adding the count in the case the file is being grouped-by but no aggregrate arguments were specified
			getting_grouped_by = False

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
					#doesnt append because group by should always be the first row
					fieldnames.insert(0, k)
					new_i = i + 1
				getting_grouped_by = True
				rows[z][k] = g

			#adds the count if no other aggregrate arguments were specified
			if len(sys.argv) == 3 and not has_been_counted or len(sys.argv) == 5 and getting_grouped_by:
				if z == 0:
					fieldnames.append('count')
					has_been_counted = True
				rows[z]['count'] = groups[g].counter
			
		i = new_i

	#outputs the csv to the stdout
	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
	writer.writeheader()
	writer.writerows(rows)

def main():
	print_file(get_values(get_args()))

if __name__ == '__main__':
	main()
