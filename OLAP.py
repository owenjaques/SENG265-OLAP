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

def main():
	args = get_args()

	#TODO: make a get data function, make a write file function

	#this next part initializes all variablea that should be initialized depending on what needs to be found
	find_count = False
	find_minimums = False
	find_maximums = False
	find_sums = False

	#goes off if their are no aggregrate arguments
	if len(sys.argv) == 3:
		find_count = True
	if args.count or find_count:
		count = 0
		find_count = True
	
	if args.minimum:
		minimums = {}
		find_minimums = True

	if args.maximum:
		maximums = {}
		find_maximums = True

	if args.mean:
		means = {}
		find_count = True
		count = 0

	#adds the means variables that must be found into the dictionary of sums as well
	if args.sums or args.mean:
		sums = {} #all the things to sum
		display_sums = {} #the sums to display
		find_sums = True

		#initialize sum dict
		if args.sums:
			for s in args.sums:
				sums[s] = 0
				display_sums[s] = 0

		#add the means required to calculate as well
		if args.mean:
			for m in args.mean:
				sums[m] = 0

	#could have modularised this bad boy but this works and does it in one pass through :)
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

	#finds the means
	if args.mean:
		for m in args.mean:
			means[m] = sums[m] / count

	#gets the arguments in order then prints the file
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

	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
	writer.writeheader()
	writer.writerow(row)

if __name__ == '__main__':
	main()
