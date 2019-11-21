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
				try:
					self.tops[t[1]] = {'k': int(t[0]), 'all': {}}
				except ValueError:
					print('Error: ' + args.input_file + ':unable to compute top ‘' + t[0] + '’' + ' values', file=sys.stderr)
					sys.exit(6)

def get_args():
	"""
	gets the command line arguments then returns them in a parsed format
	"""
	parser = argparse.ArgumentParser(description="This is OLAP.py defaults to count")
	parser.add_argument('--input', dest='input_file', required=True, help='The input file to be processed (csv)')
	parser.add_argument('--group-by', dest='group_by', type=str.lower, help='For grouping the results of aggregate functions by a categorical field')
	parser.add_argument('--top', dest='top', nargs=2, action='append', type=str.lower, help='For finding the top reacurring values in categorical fields')
	parser.add_argument('--min', dest='minimum', nargs='*', action='append', type=str.lower, help='For finding the minimum value in a numerical field')
	parser.add_argument('--max', dest='maximum', nargs='*', action='append', type=str.lower, help='For finding the maximum value in a numerical field')
	parser.add_argument('--mean', dest='mean', nargs='*', action='append', type=str.lower, help='For finding the mean average of a numerical field')
	parser.add_argument('--sum', dest='sums', nargs='*', action='append', type=str.lower, help='For finding the sum of a numerical field')
	parser.add_argument('--count', dest='counter', action='store_true', help='For finding the amount of entries in the file or the group if --group-by is called')

	#change the lists of lists into lists to deal with cases of people putting in multiple arguments per aggregrate
	args = parser.parse_args()
	if args.minimum:
		args.minimum = [x for y in args.minimum for x in y]

	if args.maximum:
		args.maximum = [x for y in args.maximum for x in y]

	if args.mean:
		args.mean = [x for y in args.mean for x in y]
	
	if args.sums:
		args.sums = [x for y in args.sums for x in y]

	return args

def non_numeric_value_error(aggregrate_function, non_numeric_tracker, input_file, line_number, aggregrate_field, value):
	"""
	prints a non numeric value error all parameters are fairly straightforard from 
	the name and just for printing except for the non numeric tracker which checks 
	for the non numeric fields getting above 100 which would print an error then exit
	the program with error code 7
	"""
	print('Error: ' + input_file + ':' + str(line_number) + ": can't compute " + aggregrate_function + " on non-numeric value '" + str(value) + "'", file=sys.stderr)
	#in the case the error is raised more than once for example if sum and mean max were all called on the same value
	if line_number not in non_numeric_tracker[aggregrate_field]:
		non_numeric_tracker[aggregrate_field].append(line_number)
	if len(non_numeric_tracker[aggregrate_field]) > 100:
		print("Error: " + input_file + ":more than 100 non-numeric values found in aggregate column ‘" + aggregrate_field + "’", file=sys.stderr)
		sys.exit(7)

def missing_field_error(input_file, missing_field):
	"""
	prints a missing field error then exits with error code 8
	takes the input file and the missing field as strings
	"""
	print('Error: '+ input_file + ':no field with name ‘' + missing_field + '’ found', file=sys.stderr)
	sys.exit(8)

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

			#two trackers for tracking the occurances of non numeric values and distinct k values for error checking for each column
			non_numeric_tracker = {k: [] for k in reader.fieldnames}
			top_k_tracker = {k: [] for k in reader.fieldnames}

			#calculates all requested aggregrates in one pass by of the file
			for line_number, row in enumerate(reader, start=1):
				#determines which group its reading and throw an error if that group does not exist
				try:
					current_group = '_OTHER' if not grouper else row[grouper]
				except KeyError:
					print('Error: ' + args.input_file + ':no group-by argument with name ‘' + grouper + '’ found', file=sys.stderr)
					sys.exit(9)

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
						except KeyError:
							missing_field_error(args.input_file, m)

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
							non_numeric_value_error('max', non_numeric_tracker, args.input_file, line_number, m, row[m])
						except KeyError:
							missing_field_error(args.input_file, m)

				if find_sums:
					for s in groups[current_group].sums.keys():
						try:
							groups[current_group].sums[s] += float(row[s])
							groups[current_group].nan_sums[s] = False
						except ValueError:
							if s in args.sums:
								non_numeric_value_error('sum', non_numeric_tracker, args.input_file, line_number, s, row[s])
							if args.mean and s in args.mean:
								non_numeric_value_error('mean', non_numeric_tracker, args.input_file, line_number, s, row[s])
						except KeyError:
							missing_field_error(args.input_file, s)

				if find_tops:
					for t in groups[current_group].tops.keys():
						#checks if it should cap the top k values
						if len(top_k_tracker[t]) == 20:
							if 'capped' not in groups[current_group].tops[t]:
								print('Error: ' + args.input_file + ': ' + t + ' has been capped at 20 distinct values', file=sys.stderr)
								groups[current_group].tops[t]['capped'] = True
						else:
							try:
								if row[t] in groups[current_group].tops[t]['all']:
									groups[current_group].tops[t]['all'][row[t]] += 1
								else:
									groups[current_group].tops[t]['all'][row[t]] = 1

								#for the capping
								if row[t] not in top_k_tracker[t]:
									top_k_tracker[t].append(row[t])
							except KeyError:
								missing_field_error(args.input_file, t)
							

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
				#figured it would be better to have one huge statement isntead of tons of temp variables it:
				# first converts the dictionary of tops to a two dimensional list
				# then sorts the list using a key that only looks at the second value of the inner list
				# then isolates just the top k values
				k_maxes = sorted([[k, v] for k, v in groups[g].tops[t]['all'].items()], reverse=True, key=lambda top: top[1])[0: groups[g].tops[t]['k']]
				#makes the string
				max_tops[t] = {'string': "", 'capped': True if 'capped' in groups[g].tops[t] else False}
				for i in range(len(k_maxes)):
					max_tops[t]['string'] += str(k_maxes[i][0]) + ': ' + str(k_maxes[i][1])
					if i != len(k_maxes) - 1:
						max_tops[t]['string'] += ', '
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

	#creates the group list then moves _OTHER if it exits to the back
	group_list = sorted(groups.keys())
	if '_OTHER' in group_list:
		group_list.remove('_OTHER')
		group_list.append('_OTHER')


	for i in range(len(ordered_args)):
		#adds every group's value to the rows for the current 
		for z, g in enumerate(group_list):
			#a flag for adding the count in the case the file is being grouped-by but no aggregrate arguments were specified
			getting_grouped_by = False

			if ordered_args[i] == '--count':
				if z == 0:
					fieldnames.append('count')
				rows[z]['count'] = groups[g].counter

			elif ordered_args[i] == '--min':
				j = 1
				#adds all the extra arguments as well ex: --min field1 field2 ...
				while i + j < len(ordered_args) and ordered_args[i+j][0:2] != '--':
					if z == 0:
						fieldnames.append('min_' + ordered_args[i+j])
					rows[z]['min_' + ordered_args[i+j]] = groups[g].minimums[ordered_args[i+j]]
					j += 1

			elif ordered_args[i] == '--max':
				j = 1
				while i + j < len(ordered_args) and ordered_args[i+j][0:2] != '--':
					if z == 0:
						fieldnames.append('max_' + ordered_args[i+j])
					rows[z]['max_' + ordered_args[i+j]] = groups[g].maximums[ordered_args[i+j]]
					j += 1
			
			elif ordered_args[i] == '--sum':
				j = 1
				while i + j < len(ordered_args) and ordered_args[i+j][0:2] != '--':
					if z == 0:
						fieldnames.append('sum_' + ordered_args[i+j])
					rows[z]['sum_' + ordered_args[i+j]] = groups[g].sums[ordered_args[i+j]]
					j += 1

			elif ordered_args[i] == '--mean':
				j = 1
				while i + j < len(ordered_args) and ordered_args[i+j][0:2] != '--':
					if z == 0:
						fieldnames.append('mean_' + ordered_args[i+j])
					rows[z]['mean_' + ordered_args[i+j]] = groups[g].means[ordered_args[i+j]]
					j += 1

			elif ordered_args[i] == '--top':
				fieldname = 'top' + ordered_args[i+1] + '_' + ordered_args[i+2]
				if groups[g].tops[ordered_args[i+2]]['capped']:
					fieldname += '_capped'
				if z == 0:
						fieldnames.append(fieldname)
				rows[z][fieldname] = groups[g].tops[ordered_args[i+2]]['string']

			elif ordered_args[i] == '--group-by':
				if z == 0:
					#doesnt append because group by should always be the first row
					fieldnames.insert(0, ordered_args[i+1])
				getting_grouped_by = True
				rows[z][ordered_args[i+1]] = g

			#adds the count if no other aggregrate arguments were specified
			if len(sys.argv) == 3 and not has_been_counted or len(sys.argv) == 5 and getting_grouped_by:
				if z == 0:
					fieldnames.append('count')
					has_been_counted = True
				rows[z]['count'] = groups[g].counter

	#outputs the csv to the stdout
	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
	writer.writeheader()
	writer.writerows(rows)

def main():
	print_file(get_values(get_args()))

if __name__ == '__main__':
	main()
