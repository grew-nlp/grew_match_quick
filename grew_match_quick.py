#!/usr/bin/env python3

import argparse
import json
import time
import os
import subprocess
import requests

parser = argparse.ArgumentParser(description="Start locally a grew_match instance")
parser.add_argument("data", help="The data to serve in the interface (see https://github.com/grew-nlp/grew_match_quick#running-grew_match_quick for format)")
parser.add_argument("--backend_port", help="PORT number for the backend server", type=int, default=8899)
parser.add_argument("--frontend_port", help="PORT number for the frontend server", type=int, default=8000)
parser.add_argument("--config", help='describe the type of corpus: can be "ud" or "sud"', default="ud")
parser.add_argument('--rtl', help="right_to_left script", action='store_true')
parser.add_argument('--hard', help="hard restart (in case of problem)", action='store_true')
parser.add_argument("--RESOURCES", help='define env var if needed in data definition', default = os.getenv ("RESOURCES"))
parser.add_argument("--GRSROOT", help='define env var if needed in data definition', default = os.getenv ("GRSROOT"))
args = parser.parse_args()

# swd = script working directory
swd = os.path.dirname(os.path.realpath(__file__))

def compile(force=False):
  # clean
  if force:
    subprocess.run(['grew_dev', 'clean', '-corpusbank', f'{swd}/local_files/corpusbank'])
  # compile
  compile_args = [ '-corpusbank', f'{swd}/local_files/corpusbank' ]
  if args.config == "sud":
    compile_args += ['-config', 'sud']
  subprocess.run(['grew_dev', 'compile'] + compile_args)


# -------------------------------------------------------------------------------------------------
# Build local folders for storage if needed
os.makedirs(f'{swd}/local_files', exist_ok=True)
os.makedirs(f'{swd}/local_files/corpusbank', exist_ok=True)
os.makedirs(f'{swd}/local_files/log', exist_ok=True)

# -------------------------------------------------------------------------------------------------
# clone or update "grew_match"
if os.path.isdir(f"{swd}/local_files/grew_match"):
  subprocess.run(['git', 'pull'], cwd=f"{swd}/local_files/grew_match")
  subprocess.run(['git', 'checkout', 'corpusbank'], cwd=f"{swd}/local_files/grew_match")
else:
  subprocess.run(['git', 'clone', 'https://gitlab.inria.fr/grew/grew_match.git'], cwd=f"{swd}/local_files")
  subprocess.run(['git', 'checkout', 'corpusbank'], cwd=f"{swd}/local_files/grew_match")
os.makedirs(f'{swd}/local_files/grew_match/meta', exist_ok=True)


# -------------------------------------------------------------------------------------------------
# clone or update "grew_match_back"
full_gmb = f"{swd}/local_files/grew_match_back"

if os.path.isdir(f"{full_gmb}"):
  subprocess.run(['git', 'pull'], cwd=f"{full_gmb}")
  subprocess.run(['git', 'checkout', 'corpusbank'], cwd=f"{full_gmb}")

else:
  subprocess.run(['git', 'clone', 'https://gitlab.inria.fr/grew/grew_match_back.git'], cwd=f"{swd}/local_files")
  subprocess.run(['git', 'checkout', 'corpusbank'], cwd=f"{full_gmb}")
if args.hard:
  subprocess.run(['rm', '-rf', '_deps'], cwd=f"{full_gmb}")
  subprocess.run(['make', 'clean'], cwd=f"{full_gmb}")

os.makedirs(f'{full_gmb}/static/shorten', exist_ok=True)

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
    "dynamic": True,
    "config": args.config,
    "rtl": args.rtl,
    "directory": os.path.abspath(args.data)}]
else:
  with open(args.data, 'r') as f:
    desc = json.load (f)
    if isinstance(desc, dict):
      corpora_list = [desc]
    else:
      corpora_list = desc

with open(f'{swd}/local_files/corpusbank/gmq_corpora.json', 'w') as outfile:
    json.dump(corpora_list, outfile, indent=2)

instances = { 
  f"localhost:{args.frontend_port}": { 
    "backend": f"http://localhost:{args.backend_port}/",
    "instance": "gmq_instance.json"
  }
}
with open(f'{swd}/local_files/grew_match/instances.json', 'w') as outfile:
    json.dump(instances, outfile, indent=2)

if len (corpora_list) == 1:
  instance = [{
    "id": "Grew_match_quick",
    "mode": "syntax",
    "style": "single",
    "corpora": [ cd["id"] for cd in corpora_list]
  }]
else:
  instance = [{
    "id": f"{os.path.splitext(os.path.basename(args.data))[0]}",
    "mode": "syntax",
    "style": "dropdown",
    "corpora": [ cd["id"] for cd in corpora_list]
  }]

with open(f'{swd}/local_files/grew_match/instances/gmq_instance.json', 'w') as outfile:
    json.dump(instance, outfile, indent=2)

compile()

# build the file "gmb.conf.in" in the "grew_match_back" folder
with open(f"{full_gmb}/gmb.conf.in__TEMPLATE", "r", encoding="utf-8") as input_file:
  with open(f"{full_gmb}/gmb.conf.in", "w", encoding="utf-8") as output_file:
    for line in input_file:
      line = line.replace('__LOG__', f'{swd}/local_files/log')
      line = line.replace('__CORPUSBANK__', f'{swd}/local_files/corpusbank/')
      line = line.replace('__RESOURCES__', args.RESOURCES)
      line = line.replace('__GRSROOT__', args.GRSROOT)
      line = line.replace('__STORAGE__', f'{full_gmb}/static/')
      output_file.write(line)


# start the backend server
with open(f"{swd}/local_files/log/backend.stdout", "w") as so:
  with open(f"{swd}/local_files/log/backend.stderr", "w") as se:
    p_back = subprocess.Popen(["make", "test.opt", f"GMB_PORT={args.backend_port}"], cwd=full_gmb, stdout=so, stderr=se)

# start the backend server
with open(f"{swd}/local_files/log/frontend.stdout", "w") as so:
  with open(f"{swd}/local_files/log/frontend.stderr", "w") as se:
    p_front = subprocess.Popen(["python", "-m", "http.server", str(args.frontend_port)], cwd=f"{swd}/local_files/grew_match", stdout=so, stderr=se)

cpt=0
while True:
  try:
    cpt += 1
    time.sleep(2)
    print (f"[{cpt}] ping backend --> ", end='')
    x = requests.post(f'http://localhost:{args.backend_port}/ping')
    print ("OK", x)
    break
  except:
    if cpt < 15:
      print ("No response, wait…")
    else:
      print (f"ERROR: It seems that the backend cannot start properly, see error log in: {swd}/local_files/log/backend.stderr")
      exit (2)




print ("==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*")
print (f" Grew_match is ready on http://localhost:{args.frontend_port}")
print ("==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*==*")

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
    print (f'unknown command "{data}"')