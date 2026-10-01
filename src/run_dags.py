import requests


res = requests.post("http://localhost:8080/api/v1/dags/process-energy/dagRuns")
print(res.ok)