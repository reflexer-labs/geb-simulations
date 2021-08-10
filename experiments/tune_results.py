import glob
import json
import sys
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('result_dir', help='directory of tune results')
parser.add_argument('-r', '--rank', help='rank results by score',
                    action='store_true')
args = parser.parse_args()

search_path = os.path.join(args.result_dir, '*', 'result.json')
result_files = glob.glob(''.join(search_path))

#print(f"{result_files=}")
config_scores = {}
for result_file in result_files:
    try:
        with open(result_file) as f:
            d = json.load(f)
    except Exception as e:
        continue
    config_scores[json.dumps(d['config'])] = d['score']

if args.rank:
    scores = sorted(config_scores.items(), key=lambda item: item[1])
else:
    scores = config_scores.items()

for s in scores:
    print(s)

sys.stdout.flush()
sys.stdout.close()
sys.stderr.flush()
sys.stderr.close()
