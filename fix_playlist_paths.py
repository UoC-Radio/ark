import os

orig_root_path = '/storage/raid/'
my_root_path = '/mnt/rastapank/'

filepath = '/mnt/rastapank/Repository/Zones/Punky_Reggae_Party/Punky_Reggae_Party.pls'
with open(filepath, 'r') as f:
    lines = f.readlines()

lines = lines[2:]
for l in lines:
    _, path = l[:-1].split('=')
    path = path.replace(orig_root_path, my_root_path)
    print(os.path.exists(path))