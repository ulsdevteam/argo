---
layout: docs
title:  "Endpoints and Parameters"
---

Using the available endpoints and their parameters, you can construct queries to get data back from the API. 

See the full OpenAPI schema at [https://api.rockarch.org/schema](https://api.rockarch.org/schema) to see how our API is structured and understand the data.

## Endpoints

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