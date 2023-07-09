import argparse
import json
import os
import subprocess

parser = argparse.ArgumentParser(description="Start locally a grew_match instance")
parser.add_argument("data", help="The data to serve in the interface [see DOC...] TODO: more doc of this JSON https://grew.fr/usage/input/]")
parser.add_argument("--back_port", help="PORT number for the backend server", type=int, default=8899)
parser.add_argument("--front_port", help="PORT number for the frontend server", type=int, default=8000)
parser.add_argument("--grew_match_back", help="path to the grew_match_back code")
args = parser.parse_args()

cwd = os.getcwd()

# -------------------------------------------------------------------------------------------------
# Build a local folder for storage if needed
os.makedirs('local_files', exist_ok=True)
os.makedirs('local_files/corpora', exist_ok=True)
os.makedirs('local_files/log', exist_ok=True)

# -------------------------------------------------------------------------------------------------
# clone or update "grew_match"
if os.path.isdir("local_files/grew_match"):
  subprocess.run(['git', 'pull'], cwd="local_files/grew_match")
else:
  subprocess.run(['git', 'clone', 'https://gitlab.inria.fr/grew/grew_match.git'], cwd="local_files")

# -------------------------------------------------------------------------------------------------
# clone or update "grew_match_back"
if os.path.isdir("local_files/grew_match_back"):
  subprocess.run(['git', 'pull'], cwd="local_files/grew_match_back")
else:
  subprocess.run(['git', 'clone', 'https://gitlab.inria.fr/grew/grew_match_back.git'], cwd="local_files")
full_gmb = os.path.abspath("local_files/grew_match_back")

# -------------------------------------------------------------------------------------------------
# Check the avaibility of the back port
pid_on_back_port = subprocess.run(['lsof', '-t', '-i', f':{args.back_port}'], stdout=subprocess.PIPE)
if len(pid_on_back_port.stdout) > 0:
  raise ValueError (f'The port {args.back_port} for backend is already used, you can change if with --back_port option')

# -------------------------------------------------------------------------------------------------
# Check the avaibility of the front port
pid_on_front_port = subprocess.run(['lsof', '-t', '-i', f':{args.front_port}'], stdout=subprocess.PIPE)
if len(pid_on_front_port.stdout) > 0:
  raise ValueError (f'The port {args.front_port} for frontend is already used, you can change if with --front_port option')

# -------------------------------------------------------------------------------------------------
# load the data (corpus or corpora)
if os.path.isdir(args.data):
  config = {} # TODO
else:
  with open(args.data, 'r') as f:
    data = json.load(f)
  # build a local "config.json" file for front config
  config = {
    'backend_server': f'http://localhost:{args.back_port}/',
    'groups': [{ 'id': 'local', 'name': 'local', 'corpora': [data] }]
  }

with open('local_files/grew_match/config.json', 'w') as outfile:
    json.dump(config, outfile, indent=2)


with open('local_files/corpora/local.json', 'w') as outfile:
  json.dump({ "corpora": [data] }, outfile, indent=2)

# compile
compile_output = subprocess.run(['grew', 'compile', '-i', f'local_files/corpora/local.json'], stdout=subprocess.PIPE)

# build the file "gmb.conf.in" in the "grew_match_back" folder
with open(f"{full_gmb}/gmb.conf.in__TEMPLATE", "r", encoding="utf-8") as input_file:
  with open(f"{full_gmb}/gmb.conf.in", "w", encoding="utf-8") as output_file:
    for line in input_file:
      line = line.replace('__LOG__', f'{cwd}/local_files/log')
      line = line.replace('__CONFIG__', f'{cwd}/local_files/grew_match/config.json')
      line = line.replace('__CORPORA__', f'{cwd}/local_files/corpora/')
      line = line.replace('__EXTERN__', f'{full_gmb}/static/')
      output_file.write(line)

# build the file "Makefile.options" in the "grew_match_back" folder
with open(f"{full_gmb}/Makefile.options__TEMPLATE", "r", encoding="utf-8") as input_file:
  with open(f"{full_gmb}/Makefile.options", "w", encoding="utf-8") as output_file:
    for line in input_file:
      line = line.replace('__PORT__', str(args.back_port))
      output_file.write(line)

# start the backend server
with open("local_files/log/backend.stdout", "w") as so:
  with open("local_files/log/backend.stderr", "w") as se:
    p_back = subprocess.Popen(["make", "test.opt"], cwd=full_gmb, stdout=so, stderr=se)

# start the backend server
with open("local_files/log/frontend.stdout", "w") as so:
  with open("local_files/log/frontend.stderr", "w") as se:
    p_front = subprocess.Popen(["python", "-m", "http.server", str(args.front_port)], cwd="local_files/grew_match", stdout=so, stderr=se)

print ("****************************************")
print (f" Grew_match is ready on http://localhost:{args.front_port}")
print ("****************************************")

while True:
  data = input('Enter "stop" or `Ctrl-C` to stop the processes: ')
  if data == "stop":
    p_back.terminate()
    p_front.terminate()
    exit (0)