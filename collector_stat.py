import boto3
import sys
import csv
import os
import time
import filecmp

if __name__ == '__main__':
    args = sys.argv[1:]

    if len(args) < 2:
        print('%s bucket prefix' % sys.argv[0])
        sys.exit(-1)

    bucket_name = args[0]
    bucket_obj_prefix = args[1]

    if not bucket_obj_prefix.endswith('/'):
        bucket_obj_prefix += '/'

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    to_stat = []
    total_domains = 0
    for obj in bucket.objects.filter(Prefix=bucket_obj_prefix):
        if obj.key.endswith('domains.csv'):
            bucket.Object(obj.key).download_file('./domains.csv')
            rows = 0
            with open('./domains.csv', 'r') as temp_file:
                rows = len(list(csv.DictReader(temp_file)))
            total_domains += rows
            print("%s: %d, %d" % (obj.key, rows, total_domains))






