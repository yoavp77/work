#!/bin/python3
from requests import get
from json import dumps
import datetime, traceback

token = get("http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",headers={"Metadata-Flavor":"Google"}).json()["access_token"]
headers = {"Authorization": "Bearer " + token}
metrics_url = "https://monitoring.googleapis.com/v3/projects/{name}/timeSeries"
end_date = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
start_date = (datetime.datetime.now() - datetime.timedelta(days=500)).strftime('%Y-%m-%dT%H:%M:%SZ')
for project in ["project1","project2"]:
  params = {"interval.endTime": end_date, "interval.startTime": start_date, "filter": 'metric.type="storage.googleapis.com/storage/total_bytes"'}
  try:
    resp = get(metrics_url.format(name=project),headers=headers,params=params)
    while True:
      for metric in resp.json()["timeSeries"]:
        try:
          bucket_name = metric["resource"]["labels"]["bucket_name"]
          for point in metric["points"]:
            print (dumps({"project": project, "bucket": bucket_name, "time": point["interval"]["endTime"], "size": point["value"]["doubleValue"]}))
        except:
          print (traceback.format_exc())
      if "nextPageToken" in resp.json():
        params["pageToken"] = resp.json()["nextPageToken"]
      else:
        break
      resp = get(metrics_url.format(name=project),headers=headers,params=params)
  except:
    print ("failed:",project)
