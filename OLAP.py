#!/usr/bin/env python3

import argparse
import os
import sys
import csv

def get_args():
	#gets the command line arguments
	parser = argparse.ArgumentParser(description="This is OLAP.py")
	parser.add_argument('--input', dest='input_file', required=True)
	parser.add_argument('--group-by', dest='group_by')
	parser.add_argument('--top', dest='top', nargs=2, action='append')
	parser.add_argument('--min', dest='minimum', action='append')
	parser.add_argument('--max', dest='maximum', action='append')
	parser.add_argument('--mean', dest='mean', action='append')
	parser.add_argument('--sum', dest='sums', action='append')
	parser.add_argument('--count', dest='count', action='store_true')
	return parser.parse_args()

def get_values(args):
	#this next part initializes all variablea that should be initialized depending on what needs to be found
	find_count = False
	find_minimums = False
	find_maximums = False
	find_sums = False
	find_tops = False

	#dictionaries of everything to calculate (and count)
	count = 0
	minimums = {}
	maximums = {}
	means = {}
	sums = {}
	tops = {}

	#goes off if their are no aggregrate arguments
	if len(sys.argv) == 3:
		find_count = True
	if args.count or find_count:
		find_count = True
	
	if args.minimum:
		find_minimums = True

	if args.maximum:
		find_maximums = True

	if args.mean:
		find_count = True
		count = 0

	#adds the means variables that must be found into the dictionary of sums as well
	if args.sums or args.mean:
		find_sums = True

		#initialize sum dict
		if args.sums:
			for s in args.sums:
				sums[s] = 0

		#add the means required to calculate as well
		if args.mean:
			for m in args.mean:
				sums[m] = 0

		if args.top:
			find_tops = True
			for t in args.top:
				tops[t[1]] = {'k': int(t[0]), 'all': {}}

	with open(args.input_file) as the_file:
		reader = csv.DictReader(the_file, delimiter=',')
		for row in reader:
			if find_count:
				count = count + 1
			
			if find_minimums:
				for m in args.minimum:
					num = float(row[m])
					if m in minimums:
						if num < minimums[m]:
							minimums[m] = num
					else:
						minimums[m] = num

			if find_maximums:
				for m in args.maximum:
					num = float(row[m])
					if m in maximums: 
						if num > maximums[m]:
							maximums[m] = num
					else:
						maximums[m] = num

			if find_sums:
				for s in sums.keys():
					sums[s] += float(row[s])

			if find_tops:
				for t in tops.keys():
					if row[t] in tops[t]['all']:
						tops[t]['all'][row[t]] += 1
					else:
						tops[t]['all'][row[t]] = 0

	#finds the means
	if args.mean:
		for m in args.mean:
			means[m] = sums[m] / count

	#finds the k amount of tops
	max_tops = {}
	for t in tops.keys():
		#first converts the dictionary of tops to a two dimensional list
		tops_but_as_a_list = [[k, v] for k, v in tops[t]['all'].items()]
		#then sorts the list using a key that only looks at the second value of the inner list
		sorted_values = sorted(tops_but_as_a_list, reverse=True, key=lambda top: top[1])
		#isolates just the top k values
		k_maxes = sorted_values[0: tops[t]['k']]
		#makes the string
		max_tops[t] = ""
		for i in range(len(k_maxes)):
			max_tops[t] += str(k_maxes[i][0]) + ': ' + str(k_maxes[i][1])
			if i != len(k_maxes) - 1:
				max_tops[t] += ', '

	return count, minimums, maximums, means, sums, max_tops

def print_file(count, minimums, maximums, means, sums, tops):
	"""
	prints the results of various arguments to the file in the order they were given in csv format
	accepts as parameters dictionaries of various calculated values and the count (int)
	"""
	ordered_args = sys.argv[1:]
	fieldnames = []
	row = {}
	for i in range(len(ordered_args)):
		#makes sure it won't reach out of index
		if i != len(ordered_args) - 1:
			k = ordered_args[i+1]

		if ordered_args[i] == '--count':
			fieldnames.append('count')
			row['count'] = count

		elif ordered_args[i] == '--min':
			fieldnames.append('min_' + k)
			row['min_' + k] = minimums[k]
			i += 1

		elif ordered_args[i] == '--max':
			fieldnames.append('max_' + k)
			row['max_' + k] = maximums[k]
			i += 1
		
		elif ordered_args[i] == '--sum':
			fieldnames.append('sum_' + k)
			row['sum_' + k] = sums[k]
			i += 1

		elif ordered_args[i] == '--mean':
			fieldnames.append('mean_' + k)
			row['mean_' + k] = means[k]
			i += 1

		elif ordered_args[i] == '--top':
			fieldnames.append('top' + k + '_' + ordered_args[i+2])
			row['top' + k + '_' + ordered_args[i+2]] = tops[ordered_args[i+2]]
			i += 2

	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
	writer.writeheader()
	writer.writerow(row)

def main():
	count, minimums, maximums, means, sums, tops = get_values(get_args())
	print_file(count, minimums, maximums, means, sums, tops)

if __name__ == '__main__':
	main()
