---
layout: docs
title:  "How to Use the API"
---

## Access methods 
The API is public and available for GET requests at [https://api.rockarch.org](https://api.rockarch.org). 

Get started with your favorite API tool or script. We do not require an API key.

If you are new to scripting or working with APIs, consider using a tool like [Hoppscotch](https://hoppscotch.io/) or [Postman](https://www.postman.com/).

- We provide an [API client](https://pypi.org/project/rac-api-client/) to simplify requests if you are writing Python scripts.
- Browse the API online at [https://api.rockarch.org](https://api.rockarch.org)


## Quick start 
Data is accessed through GET requests using API endpoints. For a list of available endpoints, see the [endpoints and parameters](#endpoints-and-parameters) section of this document.

Example 1:
Use the `/collections` endpoint to get a list of all of our archival collections, which are intellectually significant groups of records:
```
GET https://api.rockarch.org/collections
```

Example 2:
Get data about one specific collection, replacing {id} with the collection's identifier (example id: `H45i6yf7MUHuaRwQVupvg5`):

```
GET https://api.rockarch.org/collections/{id}
```
See what a response looks like in the browseable API by opening the link in your browser: [https://api.rockarch.org/collections/H45i6yf7MUHuaRwQVupvg5](https://api.rockarch.org/collections/H45i6yf7MUHuaRwQVupvg5).

Example 3:
Use the `/objects` endpoint and `online` parameter to get data for all archival objects that have digital versions available. Objects are defined as intellectually significant groups of records in a collection that do not have children:

```
GET https://api.rockarch.org/objects?online=true
```

Note that `online` is a query parameter. By convention, these are included after a `?` in the URL. To add multiple query parameters, separate the parameters by `&`. For example, to use both the `online` and `start_date` query parameters:

```
https://api.rockarch.org/objects?online=true&start_date=1950
```

## Understanding the data that comes back 
We provide [JSON](https://www.json.org/json-en.html)-formatted data.

Endpoints are paginated. We show 50 records per page by default. Pagination can be controlled via the following query parameters:
 - `limit` to set how many records each page will return
 - `offset` to request a specific page of results.

Example: get the **second** page of agent records consisting of **10** records:

```
GET https://api.rockarch.org/agents?limit=10&offset=10
```

## Endpoints and parameters

 Using the available endpoints and their parameters, you can construct queries to get data back from the API. 

See the full OpenAPI schema at [https://api.rockarch.org/schema](https://api.rockarch.org/schema) to see how our API is structured and understand the data.

### Endpoints

| Endpoint | Description |
|------|------|
|/agents|Returns a list of agents. Agents are people, organizations or families.|
|/agents/{id}|Returns data about an individual agent.|
|/collections|Returns a list of collections. Collections are intellectually significant groups of records.|
|/collections/{id}|Returns data about an individual collection.|
|/collections/{id}/ancestors|Returns the ancestors of a collection.|
|/collections/{id}/children|Returns the children of a collection.|
|/collections/{id}/minimap|Returns data about where search hits are located within a collection.|
|/objects|Returns a list of objects. Objects are intellectually significant groups of records that do not have children.|
|/objects/{id}|Returns data about an individual object.|
|/objects/{id}/ancestors|Returns the ancestors of an object.|
|/terms|Returns a list of terms. Terms are controlled values describing topics, geographic places or record formats.|
|/terms/{id}|Returns data about an individual term.|
|/search|Performs search queries across agents, collections, objects and terms.|
|/search/{id}|Performs search queries across a specific agent, collection, object or term.
|/schema/|Returns the OpenAPI schema for the RAC API.|

### Parameters
Use our [browseable API](https://api.rockarch.org) to see which parameters are available for which endpoints. For example, [https://api.rockarch.org/collections](https://api.rockarch.org/collections) lists the filter and sort fields, or parameters, that are available for that endpoint at the top of the webpage.

| Parameter | Description | Example |
|------|------|------|
|limit|Number of results to return per page.|limit=50|
|offset|Number of results to return per page.|offset=50|
|id|Unique identifier. The id is used in an endpoint path to point to a specific collection, object, agents, etc.|/collections/2HnhFZfibK6SVVu86skz3k|
|title|Filter or sort results by title.|title=world health organization|
|start_date|Filter results by start date.|start_date=1932|
|end_date|Filter results by start date.|end_date=1975|
|category|Filter results by category term, including `person`, `collection`, or `organization`|category=person|
|subject|Filter results by subject/topic term|subject=public health|
|creator|Filter results by creator. Creators are the people, organizations, and families responsible for creating the records.|creator=adams, lillian|
|online|Filter results by objects that are digital and available to view online.|online=true|
|genre|Filters results by genre/format term, including `documents`, `photographs`, `moving image`, and `audio`.|genre=moving image|
|query|Query for full-text search|query=yellow fever|
|sort|Sort results by title, start_date, end_date, or type. By default the named property will be sorted ascending. Descending order can be achieved by appending an en dash (`-`) to the start of the property.|sort=title|

## Example queries

### Using URLS

Example 1:
Use the `/search` endpoint to return the number of search matches for the query term "agriculture" that are in collections and have been categorized as photographs with dates between 1940 and 1950:

```
https://api.rockarch.org/search?&query=agriculture&category=collection&genre=photographs&start_date__gte=1940&end_date__lte=1950
```

**Note**: Appending `__gte` and `__lte` to the date parameters function as `greater than or equal to` and `less than or equal to`, allowing us to include any start and end dates in this decade instead of limiting ourselves to specific start and end dates. Similarly, `gt`= greater than and `lt`= less than.

Example 2:
Use the `/minimap` endpoint to return collections and objects with search hits for the query term "agriculture" within the Ford Foundation records collection:

```
https://api.rockarch.org/collections/2HnhFZfibK6SVVu86skz3k/minimap?query=agriculture
```

### Using the API client with Python
Example Python scripts that uses the [RAC API client](https://pypi.org/project/rac-api-client/):

Example 1:
Find out the physical size (called extent) of the Social Science Research Council records collection in the archives.

```python

# get the collection data about the Social Science Research Council records using the collection id.
client = Client()
response = client.get("/collections/iNo7dbyWw2GwSwKsC3nDj3")

# print collection title
print(response["title"])

#print collection extent value and type to get size
print(response["extents"][0]["value"], response["extents"][0]["type"])
```

Result:

```
Social Science Research Council records
509.06 Cubic Feet
```

Example 2:
Identify the creators of collections that contain keyword search matches for "public television". The `/search` endpoint performs search queries across agents, collections, objects, and terms.

Creators are the people, organizations, or families responsible for creating the records. Terms are controlled values describing topics, geographic places, or record formats.

```python

# import rac_api_client module
from rac_api_client import Client

# create an empty list of creators (people or organization) of collections that contain search matches for the query
creator_list = []

# search across agents, collections, objects and terms for "green revolution"
client = Client()
for response in client.get_paged("/search", params={"query": "public television"}):
  for creator in (response["creators"]):
    creator_list.append(creator)

# get a list of creators with no duplicated names
dedup_creator_list = list(set(creator_list))

# print deduplicated list of creators
print(dedup_creator_list)
```

Result:

```
['Rockefeller, David (1915-2017)', 'Knowles, John H. (1926-1979)', 'Ford Foundation', 'Reich, Cary', 'Rockefeller Foundation', 'John and Mary R. Markle Foundation', 'Rockefeller, Nelson A. (Nelson Aldrich)', 'Foundation for Child Development', 'Linden, Patricia', 'Asian Cultural Council', 'Rockefeller, John D., III (John Davison), 1906-1978', 'Rockefeller, Laurance Spelman', 'Arts in Education Program (U.S.)', 'National Committee on United States-China Relations', 'JDR 3rd Fund', 'Downtown Lower Manhattan Association', 'Henry Luce Foundation', 'Rockefeller, John D., Jr. (John Davison), 1874-1960', 'Grant, W. T. (William Thomas)', 'Knight Foundation', 'William T. Grant Foundation']
```

## Bulk download 
You can access [exports of our public collections data](https://github.com/RockefellerArchiveCenter/data) on GitHub. The data is generally exported on a bi-monthly basis.
