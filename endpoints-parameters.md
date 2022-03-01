---
layout: docs
title:  "Endpoints and Parameters"
---

Using the available endpoints and their parameters, you can construct queries to get data back from the API. 

See the full OpenAPI schema at [https://api.rockarch.org/schema](https://api.rockarch.org/schema) to see how our API is structured and understand the data.

## Endpoints

**Agents**: People, organizations or families.
**Collections**: Intellectually significant groups of records.
**Objects**: Intellectually significant groups of records that do not have children.
**Terms**: Controlled values describing topics, geographic places or record formats.

| Endpoint | Description |
|------|------|
|/agents|Returns a list of agents.|
|/agents/{id}|Returns data about an individual agent.|
|/collections|Returns a list of collections.|
|/collections/{id}|Returns data about an individual collection.|
|/collections/{id}/ancestors|Returns the ancestors of a collection.|
|/collections/{id}/children|Returns the children of a collection. Children of collections can be collections or objects.|
|/collections/{id}/minimap|Returns data about where search hits are located within a collection.|
|/objects|Returns a list of objects.|
|/objects/{id}|Returns data about an individual object.|
|/objects/{id}/ancestors|Returns the ancestors of an object.|
|/terms|Returns a list of terms.|
|/terms/{id}|Returns data about an individual term.|
|/search|Performs search queries across agents, collections, objects and terms.|
|/search/{id}|Performs search queries across a specific agent, collection, object or term.
|/schema/|Returns the OpenAPI schema for the RAC API.|

## Parameters
Use our [browsable API](https://api.rockarch.org) to see which parameters are available for which endpoints. For example, [https://api.rockarch.org/collections](https://api.rockarch.org/collections) lists the filter and sort fields, or parameters, that are available for that endpoint at the top of the webpage.

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

### Refining dates
Specify dates and date ranges by appending conditions to the start and end date parameters separated by a double underscore: `__`. For example, `start_date__gte=1940&end_date__lt=1950` includes all dates from 1940 to 1949.

| Parameter condition | Description |
|------|------|
|gt|greater than|
|lt|less than|
|gte|greater than or equal to|
|lte|less than or equal to|