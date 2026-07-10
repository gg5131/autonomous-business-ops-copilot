# GraphRAG & Multi-Agent Interview Questions

Pre-prepared interview questions and answers.

## Q1: Why use GraphRAG over standard vector retrieval?
- **Answer**: Standard vector search matches chunks based on local semantic similarities but misses global connections. GraphRAG connects nodes (such as Policies, Products, and Departments) through defined relationships, providing a comprehensive context path for the reasoning model.

## Q2: How does LangGraph coordinate dynamic parallel executions?
- **Answer**: By defining task dependencies inside an `ExecutionPlan` JSON DAG, the coordinator node registers scheduled runs in state checkpointers and branches paths dynamically, handling fan-in joins via empty edge evaluations.

## Q3: How do you prevent graph deadlock scenarios?
- **Answer**: By comparing `scheduled_agents` list sizes against `executed_agents` list sizes. If unexecuted active agents remain but there are no in-flight branches, a deadlock is detected and the graph routes directly to evaluation gates.
