## Synopsis

A pythonic wrapper for the teamwork projects api. Inspired by https://github.com/jpaugh/agithub.

## Usage
Create instance of TeamWork class sending in your domain and api key.
Call methods on instance using the api endpoint.
- POST /projects.json -> instance.projects.post(body=body)
- GET /projects/{project_id}.json  -> instance.projects.id.get(id=id)

All requests assumed to be json. Also use method called id when id in endpoint and send as parameter. 

## Project Post Example

```
from teamworkapi import TeamWork
API_KEY = <>
DOMAIN = <>

teamwork = TeamWork(domain=DOMAIN, apikey=API_KEY)
body = {
'project': {"name": "project 1"}
}
status, data = teamwork.projects.post(body=body)

```


## Project Get Example

```
from teamworkapi import TeamWork
API_KEY = <>
DOMAIN = <>

teamwork = TeamWork(domain=DOMAIN, apikey=API_KEY)

id = ""
status, data = teamwork.projects.id.get(id=id)

```




## License

[MIT License](http://en.wikipedia.org/wiki/MIT_License)#### Install
