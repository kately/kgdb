### kgdb

# Knowledge Graph with Streaming Update
This repository contains a passable solution to create a knowledge graph about companies and their relationship. 

The solution is driven with these usage scenario in mind:
1) Be able to support streaming to dynamically update the knowledge graph with new entities & relationships.
2) Be able to query for relationships (either UI, API, or other methods) and answer the "ask" questions.

Many applications today are data intensive as opposed to compute-intensive. The reality is it is not that simple. From data system perspective, the key is to understand the usage scenarios and what are being asked that the data could provide and to answer. This starts from "correctly" model the problem that is attempted to solve. What this model is highly depends on both the data and the application queries to support.

### Design choices and tradeoffs
Applications inevitably change and evolve over time. New features added and old features become obsolete or deprecated. Being able to adapt and accommodate to changes and address unexpected use cases, require maintainable and extensible code and reasonable ways to handle system growth and complexity. 

### What questions we want to be able to ask and answer from the model?
* What companies are *related* to *Microsoft*?
* What company *acquired* *Lynda*?
* Are there any *ex-LinkedIn employees* at *Microsoft*?
* Who is *currently* working at *Microsoft*?

#### Graph Model
<img width="550" alt="Screenshot 2023-11-23 at 5 08 34 AM" src="https://github.com/kately/kgdb/assets/9557623/d5bbb1df-be43-4c21-8f7f-b4bfc0abdc39">

### What design questions to consider and tradeoffs to make?
* Which is the better graph database to use that represent the data space: triple store vs property graph?
* What to expect of the data sources?
* What to expect of the data volume and traffic growth to support?
* What is the data workflow and data creation/change/activities?

#### Data Pipeline Overview
<img width="550" alt="Screenshot 2023-11-23 at 5 10 32 AM" src="https://github.com/kately/kgdb/assets/9557623/bdedd77c-652e-464b-8795-4eaf331c7b22">
