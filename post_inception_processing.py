from pycaprio import Pycaprio
from pycaprio.mappings import InceptionFormat
client = Pycaprio("http://localhost:8081", authentication=("remote-api", "MDT2azx-qae0fbg*uhz"))

# List projects
projects = client.api.projects()

for project in projects:
    print(project.project_id)