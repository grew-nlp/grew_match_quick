#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import requests

# swd = script working directory
swd = os.path.dirname(os.path.realpath(__file__))

def compile(force=False):
  # clean
  if force:
    subprocess.run(['grew', 'clean', '-i', f'{swd}/local_files/corpora/local.json'])
  # compile
  compile_args = ['-grew_match_server', f'{swd}/local_files/grew_match/meta', '-i', f'{swd}/local_files/corpora/local.json']
  if args.config == "sud":
    compile_args += ['-config', 'sud']
  subprocess.run(['grew', 'compile'] + compile_args)

parser = argparse.ArgumentParser(description="Start locally a grew_match instance")
parser.add_argument("data", help="The data to serve in the interface [see DOC...] TODO: more doc of this JSON https://grew.fr/usage/input/]")
parser.add_argument("--backend_port", help="PORT number for the backend server", type=int, default=8899)
parser.add_argument("--frontend_port", help="PORT number for the frontend server", type=int, default=8000)
parser.add_argument("--config", help='describe the type of corpus: can be "ud" or "sud"', default="ud")
parser.add_argument('--rtl', help="right_to_left script", action='store_true')
args = parser.parse_args()


cwd = os.getcwd()

# -------------------------------------------------------------------------------------------------
# Build a local folder for storage if needed
os.makedirs(f'{swd}/local_files', exist_ok=True)
os.makedirs(f'{swd}/local_files/corpora', exist_ok=True)
os.makedirs(f'{swd}/local_files/log', exist_ok=True)

# -------------------------------------------------------------------------------------------------
# clone or update "grew_match"
if os.path.isdir(f"{swd}/local_files/grew_match"):
  subprocess.run(['git', 'pull'], cwd=f"{swd}/local_files/grew_match")
else:
  subprocess.run(['git', 'clone', 'https://gitlab.inria.fr/grew/grew_match.git'], cwd=f"{swd}/local_files")
os.makedirs(f'{swd}/local_files/grew_match/meta', exist_ok=True)

# -------------------------------------------------------------------------------------------------
# clone or update "grew_match_back"
if os.path.isdir(f"{swd}/local_files/grew_match_back"):
  subprocess.run(['git', 'pull'], cwd=f"{swd}/local_files/grew_match_back")
else:
  subprocess.run(['git', 'clone', 'https://gitlab.inria.fr/grew/grew_match_back.git'], cwd=f"{swd}/local_files")
full_gmb = f"{swd}/local_files/grew_match_back"
os.makedirs(f'{swd}/local_files/grew_match_back/static/shorten', exist_ok=True)

# -------------------------------------------------------------------------------------------------
# Check the avaibility of the back port
pid_on_backend_port = subprocess.run(['lsof', '-t', '-i', f':{args.backend_port}'], stdout=subprocess.PIPE)
if len(pid_on_backend_port.stdout) > 0:
  raise ValueError (f'The port {args.backend_port} for backend is already used, you can change it with --backend_port option')

# -------------------------------------------------------------------------------------------------
# Check the avaibility of the front port
pid_on_frontend_port = subprocess.run(['lsof', '-t', '-i', f':{args.frontend_port}'], stdout=subprocess.PIPE)
if len(pid_on_frontend_port.stdout) > 0:
  raise ValueError (f'The port {args.frontend_port} for frontend is already used, you can change it with --frontend_port option')

# -------------------------------------------------------------------------------------------------
# load the data (corpus or corpora)
if os.path.isdir(args.data):
  # if the data is a folder: one corpus with folder name as id and config from CLI argument
  corpora_list = [{
    "id": os.path.basename(args.data),
    "config": args.config,
    "rtl": args.rtl,
    "directory": os.path.abspath(args.data)}]
else:
  with open(args.data, 'r') as f:
    json_data = json.load(f)
  if "corpora" in json_data:
    # the JSON file describes a set of corpora
    corpora_list = json_data["corpora"]
  else:
    # the JSON file describes one corpus
    corpora_list = [json_data]


gm_config = {
  'backend_server': f'http://localhost:{args.backend_port}/',
  'groups': [
    { 'id': 'local',
      'name': 'local',
      'style': 'single' if len(corpora_list) == 1 else 'dropdown',
      'corpora': corpora_list
  }]
}

with open(f'{swd}/local_files/grew_match/config.json', 'w') as outfile:
    json.dump(gm_config, outfile, indent=2)

with open(f'{swd}/local_files/corpora/local.json', 'w') as outfile:
  json.dump({ "corpora": corpora_list }, outfile, indent=2)


compile()

# build the file "gmb.conf.in" in the "grew_match_back" folder
with open(f"{full_gmb}/gmb.conf.in__TEMPLATE", "r", encoding="utf-8") as input_file:
  with open(f"{full_gmb}/gmb.conf.in", "w", encoding="utf-8") as output_file:
    for line in input_file:
      line = line.replace('__LOG__', f'{swd}/local_files/log')
      line = line.replace('__CONFIG__', f'{swd}/local_files/grew_match/config.json')
      line = line.replace('__CORPORA__', f'{swd}/local_files/corpora/')
      line = line.replace('__EXTERN__', f'{full_gmb}/static/')
      output_file.write(line)

# build the file "Makefile.options" in the "grew_match_back" folder
with open(f"{full_gmb}/Makefile.options__TEMPLATE", "r", encoding="utf-8") as input_file:
  with open(f"{full_gmb}/Makefile.options", "w", encoding="utf-8") as output_file:
    for line in input_file:
      line = line.replace('__PORT__', str(args.backend_port))
      output_file.write(line)

# start the backend server
with open(f"{swd}/local_files/log/backend.stdout", "w") as so:
  with open(f"{swd}/local_files/log/backend.stderr", "w") as se:
    p_back = subprocess.Popen(["make", "test.opt"], cwd=full_gmb, stdout=so, stderr=se)

# start the backend server
with open(f"{swd}/local_files/log/frontend.stdout", "w") as so:
  with open(f"{swd}/local_files/log/frontend.stderr", "w") as se:
    p_front = subprocess.Popen(["python", "-m", "http.server", str(args.frontend_port)], cwd=f"{swd}/local_files/grew_match", stdout=so, stderr=se)

print ("****************************************")
print (f" Grew_match is ready on http://localhost:{args.frontend_port}")
print ("****************************************")

while True:
  data = input('Enter: s: stop, r:recompile, f:force recompile. ')
  if data in ["s", "S"]:
    p_back.terminate()
    p_front.terminate()
    exit (0)
  elif data in ["r", "R"]:
    compile()
    requests.post(f'http://localhost:{args.backend_port}/refresh_all')
  elif data in ["f", "F"]:
    compile(True)
    requests.post(f'http://localhost:{args.backend_port}/refresh_all')
  else:
    print (f'unknown command "f{data}"')