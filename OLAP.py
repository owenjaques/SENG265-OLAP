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
	#goes off if their are no aggregrate arguments
	find_count = False
	if len(sys.argv) == 3:
		find_count = True
	if args.count or find_count:
		count = 0
		find_count = True
	
	find_minimums = False
	if args.minimum:
		minimums = {}
		find_minimums = True

	find_maximums = False
	if args.maximum:
		maximums = {}
		find_maximums = True

	find_means = False
	if args.mean:
		means = {}
		#initialize mean dict
		for m in args.mean:
			means[m] = 0
		find_means = True

	find_sums = False
	if args.sums:
		sums = {}
		#initialize sum dict
		for s in args.sums:
			sums[s] = 0
		find_sums = True
		#add checking for not sums needed only add shared list

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
				for s in args.sums:
					sums[s] += float(row[s])

			#if time permits add optimization to use the sums if its in both
			if find_means:
				for m in args.mean:
					means[m] += float(row[m])

	#finds the means
	if find_means:
		means = {k:v/count for (k,v) in means.items()}

	#add actually print flags

	#writes the file
	fieldnames = []
	row = {}
	if find_count:
		fieldnames.append('count')
		row['count'] = count

	if find_minimums:
		for m in args.minimum:
			fieldnames.append('min_' + m)
			row['min_' + m] = minimums[m]

	if find_maximums:
		for m in args.maximum:
			fieldnames.append('max_' + m)
			row['max_' + m] = maximums[m]
	
	if find_sums:
		for s in args.sums:
			fieldnames.append('sum_' + s)
			row['sum_' + s] = sums[s]

	if find_means:
		for m in args.mean:
			fieldnames.append('mean_' + m)
			row['mean_' + m] = means[m]

	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
	writer.writeheader()
	writer.writerow(row)

if __name__ == '__main__':
	main()
