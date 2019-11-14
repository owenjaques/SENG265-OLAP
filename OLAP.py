#!/usr/bin/env python3

import argparse
import os
import sys
import csv

def get_args():
	parser = argparse.ArgumentParser()
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

	#flag variables for the main loop to see what to find
	find_count = False
	find_minimums = False
	find_maximums = False
	find_means = False
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
		find_means = True
		find_count = True
		count = 0

	if args.sums or args.mean:
		sums = {} #all the things to sum
		display_sums = {} #the sums to display

		#initialize sum dict
		if args.sums:
			for s in args.sums:
				sums[s] = 0
				display_sums[s] = 0

		#add the means required to calculate as well
		if args.mean:
			for m in args.mean:
				sums[m] = 0
		
		find_sums = True

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
	if find_means:
		for m in args.mean:
			means[m] = sums[m] / count

	#add actually print flags

	#writes the file
	fieldnames = []
	row = {}
	if args.count:
		fieldnames.append('count')
		row['count'] = count

	if args.minimum:
		for m in args.minimum:
			fieldnames.append('min_' + m)
			row['min_' + m] = minimums[m]

	if args.maximum:
		for m in args.maximum:
			fieldnames.append('max_' + m)
			row['max_' + m] = maximums[m]
	
	if args.sums:
		for s in args.sums:
			fieldnames.append('sum_' + s)
			row['sum_' + s] = sums[s]

	if args.mean:
		for m in args.mean:
			fieldnames.append('mean_' + m)
			row['mean_' + m] = means[m]

	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
	writer.writeheader()
	writer.writerow(row)

if __name__ == '__main__':
	main()
