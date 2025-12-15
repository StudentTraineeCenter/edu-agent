# Mind Maps

Mind Maps are visual knowledge representations generated from project documents. They help students understand relationships between concepts and organize information visually.

## Mind Map Generation

### Process

1. User requests mind map creation (optionally with a topic and custom instructions).
2. System searches project documents for relevant content.
3. AI analyzes document content and identifies key concepts.
4. AI generates structured mind map data (nodes and edges).
5. Mind map is saved with title, description, and map data.

### Generation Parameters

- `topic`: Topic or central concept for the mind map.
- `custom_instructions`: Free-form instructions for how to structure the map (e.g., `"high-level only"`, `"deep dive into subtopics"`, `"focus on definitions and examples"`).
- `project_id`: Project containing source documents.

## Mind Map Structure

Each mind map contains:

- **Title**: Auto-generated or user-provided title.
- **Description**: Brief explanation of mind map content.
- **Map Data**: Structured JSON data containing:
  - Nodes: Concepts, topics, or ideas.
  - Edges: Relationships between nodes.
  - Hierarchical organization.
  - Visual layout information.

## Mind Map Features

- **Generate Mind Map**: Create a new mind map from documents.
- **List Mind Maps**: View all mind maps in a project.
- **Get Mind Map**: Retrieve mind map details and data.

## Topic Filtering

Mind maps are generated from specific topics by providing a `topic` (and optionally `custom_instructions`):

- The topic is used to search for relevant documents.
- Only matching document content is used for generation.
- Custom instructions refine level of detail, structure, and emphasis within that topic.

## Mind Map Quality

Generated mind maps follow these guidelines:

- Clear hierarchical structure.
- Logical relationships between concepts.
- Comprehensive coverage of key topics.
- Visual organization suitable for display.
- Focus on important educational content.


