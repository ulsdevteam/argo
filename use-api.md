---
layout: docs
title:  "How to Use the API"
---
## Access methods 
The API is public and available for GET requests at [https://api.rockarch.org](https://api.rockarch.org). 

Get started with your favorite API tool or script. We do not require an API key.

- Browse the API online at [https://api.rockarch.org](https://api.rockarch.org).
- If you are new to scripting or working with APIs, consider using a tool like [Hoppscotch](https://hoppscotch.io/) or [Postman](https://www.postman.com/).
- We provide an [API client](https://pypi.org/project/rac-api-client/) to simplify requests if you are writing Python scripts.

## Quick start 
The best way to learn what is available via the API is to start making API requests and exploring what comes back, whether in the [browsable API](https://api.rockarch.org) with URLs or using another interface. Data is accessed through GET requests using API endpoints. For a list of available endpoints, see the [endpoints and parameters](/argo/endpoints-parameters) section of this document.

This section includes some basic examples to show you how to construct queries and start exploring.

### Example 1: Get all collections
Use the `/collections` endpoint to get a list of all of our archival collections, which are intellectually significant groups of records:

```
GET https://api.rockarch.org/collections
```

### Example 2: Get a specific collection
Get data about one specific collection, replacing {id} with the collection's identifier (example id: `H45i6yf7MUHuaRwQVupvg5`). Collection identifiers can be found in the `/collections` or `/search` endpoints as the URI value of a collection. They can also be found in DIMES URLs, since DIMES uses the API. For example: `https://dimes.rockarch.org/collections/H45i6yf7MUHuaRwQVupvg5`: 

```
GET https://api.rockarch.org/collections/{id}
```
See what a response looks like in the browsable API by opening the link in your browser: [https://api.rockarch.org/collections/H45i6yf7MUHuaRwQVupvg5](https://api.rockarch.org/collections/H45i6yf7MUHuaRwQVupvg5).

### Example 3: Get objects that are available to view online
Use the `/objects` endpoint and `online` parameter to get data for all archival objects that have digital versions available. Objects are defined as intellectually significant groups of records in a collection that do not have children:

```
GET https://api.rockarch.org/objects?online=true
```

Note that `online` is a query parameter. By convention, these are included after a `?` in the URL. To add multiple query parameters, separate the parameters by `&`. For example, to use both the `online` and `start_date` query parameters:

```
https://api.rockarch.org/objects?online=true&start_date=1950
```

### Example 4: Search
Use the `/search` endpoint to return the number of search matches for the query term "agriculture" that are in collections and have been categorized as photographs with dates between 1940 and 1950:

```
https://api.rockarch.org/search?&query=agriculture&category=collection&genre=photographs&start_date__gte=1940&end_date__lte=1950
```

**Note**: As documented in the [parameters section](/argo/endpoints-parameters#parameters), appending `__gte` and `__lte` to the date parameters function as `greater than or equal to` and `less than or equal to`, allowing us to include any start and end dates in this decade instead of limiting ourselves to specific start and end dates.

### Example 5: Minimap
Use the `/minimap` endpoint to return collections and objects with search hits for the query term "agriculture" within the Ford Foundation records collection:

```
https://api.rockarch.org/collections/2HnhFZfibK6SVVu86skz3k/minimap?query=agriculture
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

## Using the API client with Python
Example Python scripts that uses the [RAC API client](https://pypi.org/project/rac-api-client/):

### Example 1: Size of collection
Find out the physical size (called extent) of the Social Science Research Council records collection in the archives.

```python
# import rac_api_client module
from rac_api_client import Client

# get the collection data about the Social Science Research Council 
# records using the collection id.
client = Client()
collection = client.get("/collections/iNo7dbyWw2GwSwKsC3nDj3")

# print collection title
print(collection["title"])

# print collection extent value and type to get size
for extent in collection["extents"]:
    print(extent["value"], extent["type"])
```

Result:

```
Social Science Research Council records
509.06 Cubic Feet
```

### Example 2: Collection creators
Identify the creators of collections that contain keyword search matches for "public television". The `/search` endpoint performs search queries across agents, collections, objects, and terms.

Creators are the people, organizations, or families responsible for creating the records. Terms are controlled values describing topics, geographic places, or record formats.

```python
# import rac_api_client module
from rac_api_client import Client

# create an empty set of creators (people or organization) of collections 
# that contain search matches for the query
creator_set = set()

# search across agents, collections, objects and terms for "public television"
# add the associated creators to the creator set
client = Client()
for records in client.get_paged("/search", params={"query": "public television"}):
  creator_set.add(*records["creators"])

# convert the set to a list of creators with no duplicated names
dedup_creator_list = list(creator_set)

# print deduplicated list of creators
print(dedup_creator_list)
```

Result:

```
['Rockefeller, David (1915-2017)', 'Knowles, John H. (1926-1979)', 'Ford Foundation', 'Reich, Cary', 'Rockefeller Foundation', 'John and Mary R. Markle Foundation', 'Rockefeller, Nelson A. (Nelson Aldrich)', 'Foundation for Child Development', 'Linden, Patricia', 'Asian Cultural Council', 'Rockefeller, John D., III (John Davison), 1906-1978', 'Rockefeller, Laurance Spelman', 'Arts in Education Program (U.S.)', 'National Committee on United States-China Relations', 'JDR 3rd Fund', 'Downtown Lower Manhattan Association', 'Henry Luce Foundation', 'Rockefeller, John D., Jr. (John Davison), 1874-1960', 'Grant, W. T. (William Thomas)', 'Knight Foundation', 'William T. Grant Foundation']
```
