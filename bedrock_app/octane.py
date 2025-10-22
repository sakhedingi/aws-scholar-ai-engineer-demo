import requests
from requests.auth import HTTPBasicAuth
import json

def fetch_octane_requirements():
    url = "http://10.114.222.150:8080/api/shared_spaces/3001/workspaces/2001/requirements"
    params = {
        "fields": "project_name_udf,project_percentage_udf,new_project_status_udf,prj_comments_udf,author,id,last_modified,creation_time,description,review_status_udf,reviewer_udf",
        "offset": 0,
        "limit": 20000
    }
    auth = HTTPBasicAuth("DingiS", "Vodacom082")

    try:
        response = requests.get(url, params=params, auth=auth, timeout=30)
        response.raise_for_status()
        data = response.json().get("data", [])

        # Save to a .txt file
        with open("./knowledge_base/quirements_data.txt", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        
        print("Data successfully saved to requirements_data.txt")

    except Exception as e:
        print("Error:",e)