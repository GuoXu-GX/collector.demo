import boto3
import sys
import csv
import os
import time
import filecmp

if __name__ == '__main__':
    args = sys.argv[1:]

    if len(args) < 3:
        print('%s bucket prefix [domain]' % sys.argv[0])
        sys.exit(-1)

    bucket_name = args[0]
    bucket_obj_prefix = args[1]
    if not bucket_obj_prefix.endswith('/'):
        bucket_obj_prefix += '/'
    domains = args[2:]
    print('s3 bucket: ', bucket_name)
    print('s3 obj prefix: ', bucket_obj_prefix)
    print('domains to process: ', domains)

    s3 = boto3.resource('s3')

    bucket = s3.Bucket(bucket_name)

    print('\nclean %s/%s:' % (bucket_name, bucket_obj_prefix))
    to_del = []
    for obj in bucket.objects.filter(Prefix=bucket_obj_prefix):
        to_del.append(obj)

    if len(to_del) > 0:
        print('there are %d objects with prefix %s' % (len(to_del), bucket_obj_prefix))
        print('\t', ['%s' % obj.key.replace(bucket_obj_prefix, '', 1) for obj in to_del])
        bucket.delete_objects(
            Delete={
                'Objects': [{'Key': obj.key} for obj in to_del]
            }
        )

    print('\nmake domains input file:')
    temp_path = 'temp-%s.csv' % time.time()
    temp_file = open(temp_path, 'w')
    with temp_file:
        writer = csv.DictWriter(temp_file, fieldnames=['Domain'])
        writer.writeheader()
        for domain in domains:
            writer.writerow({'Domain': domain})

    print('\nupload domains input file:')
    bucket.upload_file(temp_path, '%sinput/domains.csv' % bucket_obj_prefix)

    print('\ndownload domains file to verify:')
    bucket.download_file('%sinput/domains.csv' % bucket_obj_prefix, temp_path + '.1')
    print('\tlocal/s3 files are equal: ', filecmp.cmp(temp_path, temp_path + '.1'))

    print('\ndelete temp file:')
    #os.remove(temp_path)
    os.remove(temp_path + '.1')
