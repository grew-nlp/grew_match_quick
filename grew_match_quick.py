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

def get_python_command():
  try:
    subprocess.run(['python3', '--version'], capture_output = True, text = True)
    return "python3"
  except:
    try:
      subprocess.run(['python', '--version'], capture_output = True, text = True)
      return "python"
    except:
      print ("ERROR: Cannot find then 'python' command")
      exit (1)

def compile(force=False):
  # clean
  if force:
    subprocess.run(['grew', 'clean', '-CORPUSBANK', f'{swd}/local_files/corpusbank'])
  # compile
  compile_args = [ '-CORPUSBANK', f'{swd}/local_files/corpusbank' ]
  if args.config == "sud":
    compile_args += ['-config', 'sud']
  subprocess.run(['grew', 'compile'] + compile_args)

# -------------------------------------------------------------------------------------------------
# Build local folders for storage if needed
os.makedirs(f'{swd}/local_files', exist_ok=True)
os.makedirs(f'{swd}/local_files/corpusbank', exist_ok=True)
os.makedirs(f'{swd}/local_files/log', exist_ok=True)

# -------------------------------------------------------------------------------------------------
# clone or update "grew_match"
if os.path.isdir(f"{swd}/local_files/grew_match"):
  subprocess.run(['git', 'pull'], cwd=f"{swd}/local_files/grew_match")
else:
  subprocess.run(['git', 'clone', 'https://gitlab.inria.fr/grew/grew_match.git'], cwd=f"{swd}/local_files")
os.makedirs(f'{swd}/local_files/grew_match/meta', exist_ok=True)


# -------------------------------------------------------------------------------------------------
# clone or update "grew_match_dream"
full_gmd = f"{swd}/local_files/grew_match_dream"

if os.path.isdir(f"{full_gmd}"):
  subprocess.run(['git', 'pull'], cwd=f"{full_gmd}")

else:
  subprocess.run(['git', 'clone', 'https://github.com/grew-nlp/grew_match_dream.git'], cwd=f"{swd}/local_files")
if args.hard:
  subprocess.run(['dune', 'clean'], cwd=f"{full_gmd}")

subprocess.run(['dune', 'build'], cwd=f"{full_gmd}")

os.makedirs(f'{full_gmd}/static/shorten', exist_ok=True)

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
elif os.path.isfile (args.data) and args.data.endswith(".json"):
  with open(args.data, 'r') as f:
    desc = json.load (f)
    if isinstance(desc, dict):
      corpora_list = [desc]
    else:
      corpora_list = desc
elif os.path.isfile (args.data) and (args.data.endswith(".conllu") or args.data.endswith(".conll")):
  abs = os.path.abspath(args.data)
  corpora_list = [{
    "id": os.path.basename(abs),
    "dynamic": True,
    "config": args.config,
    "rtl": args.rtl,
    "directory": os.path.dirname(abs),
    "files": [os.path.basename(abs)]
  }]
elif os.path.isfile (args.data):
  print (f"ERROR: Don't know what to do with the file '{args.data}'")
  exit (3)
else:
  print (f"ERROR: '{args.data}' is neither a file nor a folder")
  exit (3)

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


backend_config = {
  "port": args.backend_port,
  "prefix": "gmq",
  "corpusbank": f'{swd}/local_files/corpusbank/',
  "log": f'{swd}/local_files/log',
  "storage": f'{full_gmd}/static/'
}

with open(f'{full_gmd}/config.json', 'w') as outfile:
    json.dump(backend_config, outfile, indent=2)

# start the backend server
with open(f"{swd}/local_files/log/backend.stdout", "w") as so:
  with open(f"{swd}/local_files/log/backend.stderr", "w") as se:
    p_back = subprocess.Popen(["_build/default/src/main.exe", "config.json"], cwd=full_gmd, stdout=so, stderr=se)

# start the backend server
python_command = get_python_command()
with open(f"{swd}/local_files/log/frontend.stdout", "w") as so:
  with open(f"{swd}/local_files/log/frontend.stderr", "w") as se:
    p_front = subprocess.Popen([python_command, "-m", "http.server", str(args.frontend_port)], cwd=f"{swd}/local_files/grew_match", stdout=so, stderr=se)

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