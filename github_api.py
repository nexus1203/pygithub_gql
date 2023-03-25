import requests
import json
from string import Template


class GitHub:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com/graphql"
        self.headers = {"Content-Type": "application/json", 
                            "Accept": "application/json",
                            "Authorization": "token " + self.token,
                            "GraphQL-Features": "projects_next_graphql" }
    def run_query(self, query):
        request = requests.post(self.base_url, 
                                json={"query": query}, 
                                headers=self.headers)
        if request.status_code == 200:
            return request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        
    def get_project_id(self, username, project_number):
        p_query = Template("""{
                                user(login: "$username") 
                                {
                                    projectNext(number: $project_number) 
                                    {
                                        id
                                        title
                                    }
                                }
                            }""").safe_substitute(username=username, project_number=project_number)
                           
        return self.run_query(p_query.replace(" ",""))
    
    
    def get_project_items(self, project_id):
        c_query = Template("""{
                              node(id: "$project_id") {
                                ... on ProjectNext {
                                  title
                                  url
                                  items(first: 100) {
                                    nodes {
                                      title
                                      id
                                      fieldValues(first: 100) {
                                        nodes {
                                          createdAt
                                          creator {
                                            login
                                          }
                                          databaseId
                                          id
                                          projectField {
                                            name
                                            settings
                                          }
                                          value
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }""").safe_substitute(project_id=project_id)
        return self.run_query(c_query)
    

class Project:
    def __init__(self, data):
        self.data = data
        self.details = self.get_project_details()
        self.items = self.parse_data()
        
    def get_project_details(self):
        project_name = self.data['data']['node']['title']
        project_url = self.data['data']['node']['url']
        return project_name, project_url
    
    def get_items(self):
        return self.data['data']['node']['items']['nodes']
    
    def parse_data(self,):
        items = self.get_items()
        return [self._parse_item(item) for item in items]
    
    def _parse_item(self, item):
        title = self.get_Title_from_ProjectField(item)
        status = self.get_Status_from_ProjectField(item)
        creation = self.get_creation_date(item)
        deadline = self.get_deadline_from_ProjectField(item)
        priority = self.get_Priority_from_ProjectField(item)
        members = self.get_Members_from_ProjectField(item)
        notes = self.get_Notes_from_ProjectField(item)
        return {'Created': creation, 'Title': title, 'Status': status, 'Deadline': deadline, 'Priority': priority, 'Members': members, 'Notes': notes}
    
    def get_item_by_name(self, item_name):
        for item in self.get_items():
            if item['title'] == item_name:
                return item
    
    def get_item_by_field_name(self, field_name):
        for item in self.get_items():
            for field in item['fieldValues']['nodes']:
                if field['projectField']['name'] == field_name:
                    return item
    
    def get_Title_from_ProjectField(self, item):
        for field in item['fieldValues']['nodes']:
            if field['projectField']['name'] == 'Title':
                title = field['value']
                return title
    
    def get_Status_from_ProjectField(self, item):
        for field in item['fieldValues']['nodes']:
            if field['projectField']['name'] == 'Status':
                status = field['value']
                options = json.loads(field['projectField']['settings']).get('options')
                for option in options:
                    if option['id'] == status:
                        return option['name']
    
    def get_deadline_from_ProjectField(self, item):
        for field in item['fieldValues']['nodes']:
            if field['projectField']['name'] == 'Deadline':
                deadline = field['value']
                date = deadline.split('T')[0]
                time = deadline.split('T')[1].split('+')[0]
                return date
    
    def get_Priority_from_ProjectField(self, item):
        for field in item['fieldValues']['nodes']:
            if field['projectField']['name'] == 'Priority':
                priority = field['value']
                options = json.loads(field['projectField']['settings']).get('options')
                for option in options:
                    if option['id'] == priority:
                        return option['name']
    
    def get_Status_from_ProjectField(self, item):
        for field in item['fieldValues']['nodes']:
            if field['projectField']['name'] == 'Status':
                status = field['value']
                options = json.loads(field['projectField']['settings']).get('options')
                for option in options:
                    if option['id'] == status:
                        return option['name']
    
    def get_Members_from_ProjectField(self, item):
        for field in item['fieldValues']['nodes']:
            if field['projectField']['name'] == 'Members':
                members = field['value']
                return members
    
    def get_Notes_from_ProjectField(self, item):
        for field in item['fieldValues']['nodes']:
            if field['projectField']['name'] == 'Notes':
                notes = field['value']
                return notes
    
    def get_creation_date(self, item):
        for field in item['fieldValues']['nodes']:
            
            date = field['createdAt']
            date = date.replace('T', ' ').replace('Z', '')
            return date
        

def fetch_latest_project_items(key:str, username:str, project_number:int) -> dict:
    """
    Get latest update information of a project.

    Args:
        key (str): The API key .txt path.
        username (str): username of which the projects (Beta) is to be searched
        project_number (int): project number of from the project board (check the project url)

    Returns:
        dict: dictionary contains details of the project and items.
    """
    with open(key) as f:
        token = f.read().strip()
    git = GitHub(token=token)
    data = git.get_project_id(username, project_number)
    
    project_id, title = data['data']['user']['projectNext']['id'], data['data']['user']['projectNext']['title']
    project_data = git.get_project_items(project_id)
    project = Project(project_data)
    return {'details':project.details, 'items':project.items}

if __name__ == "__main__":
  # # Usage
  project = fetch_latest_project_items("API_key.txt', 'abcd', 1)
  print(project['details'])
