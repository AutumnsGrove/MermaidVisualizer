# Sample Markdown Document with Mermaid Diagrams

This document contains various types of Mermaid diagrams for testing purposes.

## Introduction

This is a comprehensive test file that includes multiple diagram types, edge cases, and regular markdown content. It's designed to thoroughly test the MermaidVisualizer extraction and generation capabilities.

## Flowchart Diagram

Here's a simple flowchart showing a decision process:

```mermaid
flowchart TD
    Start([Start Process]) --> Input[/User Input/]
    Input --> Validate{Valid?}
    Validate -->|Yes| Process[Process Data]
    Validate -->|No| Error[Show Error]
    Error --> Input
    Process --> Save[(Save to DB)]
    Save --> Success[/Success Message/]
    Success --> End([End])
```

The flowchart demonstrates various node shapes and decision points.

## Sequence Diagram

This sequence diagram illustrates an authentication flow:

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant Server
    participant Database

    User->>Browser: Enter credentials
    Browser->>Server: POST /login
    activate Server
    Server->>Database: Query user
    activate Database
    Database-->>Server: User data
    deactivate Database
    Server->>Server: Verify password
    alt Authentication successful
        Server-->>Browser: JWT token
        Browser-->>User: Redirect to dashboard
    else Authentication failed
        Server-->>Browser: Error 401
        Browser-->>User: Show error message
    end
    deactivate Server
```

This demonstrates participant interactions and conditional flows.

## Gantt Chart

Project timeline visualization:

```mermaid
gantt
    title Project Development Timeline
    dateFormat YYYY-MM-DD
    section Planning
    Requirements Gathering    :done,    req1, 2024-01-01, 2024-01-15
    System Design            :done,    des1, 2024-01-16, 2024-01-30
    section Development
    Backend Development      :active,  dev1, 2024-02-01, 2024-03-15
    Frontend Development     :active,  dev2, 2024-02-15, 2024-03-30
    section Testing
    Unit Testing            :         test1, 2024-03-01, 2024-03-20
    Integration Testing     :         test2, 2024-03-21, 2024-04-05
    section Deployment
    UAT                     :         uat1, 2024-04-06, 2024-04-15
    Production Release      :         rel1, 2024-04-16, 2024-04-20
```

Gantt charts are useful for project management and timeline visualization.

## Class Diagram

Here's a class diagram for an e-commerce system:

```mermaid
classDiagram
    class Customer {
        +String customerId
        +String name
        +String email
        +List~Order~ orders
        +placeOrder(Order order)
        +viewOrderHistory()
    }

    class Order {
        +String orderId
        +Date orderDate
        +OrderStatus status
        +List~OrderItem~ items
        +Decimal totalAmount
        +calculateTotal()
        +updateStatus(OrderStatus status)
    }

    class OrderItem {
        +String itemId
        +Product product
        +int quantity
        +Decimal price
        +calculateSubtotal()
    }

    class Product {
        +String productId
        +String name
        +String description
        +Decimal price
        +int stockQuantity
        +updateStock(int quantity)
    }

    Customer "1" --> "*" Order : places
    Order "1" --> "*" OrderItem : contains
    OrderItem "*" --> "1" Product : references
```

## State Diagram

State machine for an order processing system:

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Validated : validate
    Validated --> Processing : process
    Processing --> Shipped : ship
    Processing --> Cancelled : cancel
    Shipped --> Delivered : deliver
    Delivered --> [*]
    Cancelled --> [*]

    Processing --> OnHold : payment_failed
    OnHold --> Processing : retry_payment
    OnHold --> Cancelled : max_retries_exceeded
```

## Entity Relationship Diagram

Database schema for a blog system:

```mermaid
erDiagram
    USER ||--o{ POST : writes
    USER ||--o{ COMMENT : writes
    POST ||--o{ COMMENT : has
    POST }o--|| CATEGORY : belongs_to
    POST }o--o{ TAG : has

    USER {
        int user_id PK
        string username UK
        string email UK
        string password_hash
        datetime created_at
    }

    POST {
        int post_id PK
        int user_id FK
        int category_id FK
        string title
        text content
        datetime published_at
        boolean is_published
    }

    COMMENT {
        int comment_id PK
        int post_id FK
        int user_id FK
        text content
        datetime created_at
    }

    CATEGORY {
        int category_id PK
        string name UK
        string description
    }

    TAG {
        int tag_id PK
        string name UK
    }
```

## Pie Chart

Distribution of programming languages in a project:

```mermaid
pie title Programming Language Distribution
    "Python" : 45
    "JavaScript" : 30
    "HTML/CSS" : 15
    "Shell Scripts" : 7
    "Other" : 3
```

## Regular Code Block (Not Mermaid)

This is a regular Python code block that should NOT be extracted as a Mermaid diagram:

```python
def calculate_total(items):
    """Calculate total price of items."""
    total = sum(item.price * item.quantity for item in items)
    return total

# Example usage
items = [Item("Apple", 1.50, 3), Item("Orange", 2.00, 2)]
print(f"Total: ${calculate_total(items):.2f}")
```

## Another Regular Code Block (JavaScript)

```javascript
// Fetch user data from API
async function getUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching user:', error);
        throw error;
    }
}
```

## User Journey Diagram

Customer journey for an online shopping experience:

```mermaid
journey
    title Online Shopping Experience
    section Discovery
      Browse Products: 5: Customer
      Search for Item: 4: Customer
      View Details: 5: Customer
    section Decision
      Compare Prices: 3: Customer
      Read Reviews: 4: Customer
      Add to Cart: 5: Customer
    section Purchase
      Review Cart: 4: Customer
      Enter Payment: 3: Customer
      Confirm Order: 5: Customer
    section Post-Purchase
      Receive Confirmation: 5: Customer, System
      Track Shipment: 4: Customer, System
      Receive Product: 5: Customer
      Leave Review: 3: Customer
```

## Git Graph

Version control branching strategy:

```mermaid
gitGraph
    commit id: "Initial commit"
    commit id: "Add base structure"
    branch develop
    checkout develop
    commit id: "Setup dev environment"
    branch feature/login
    checkout feature/login
    commit id: "Implement login UI"
    commit id: "Add authentication"
    checkout develop
    merge feature/login
    branch feature/dashboard
    checkout feature/dashboard
    commit id: "Create dashboard layout"
    commit id: "Add widgets"
    checkout develop
    merge feature/dashboard
    checkout main
    merge develop tag: "v1.0.0"
    checkout develop
    commit id: "Continue development"
```

## Edge Case: Empty Mermaid Block

This is an edge case with an empty mermaid block:

```mermaid
```

The above block is empty and should be handled gracefully.

## Edge Case: Mermaid-like Content in Regular Text

Sometimes the word mermaid appears in regular text, like "The mermaid swam in the ocean."
This should not be confused with a mermaid code block.

## Complex Flowchart with Subgraphs

```mermaid
flowchart TB
    subgraph Frontend
        A[Web Browser]
        B[Mobile App]
    end

    subgraph "API Gateway"
        C[Load Balancer]
        D[API Server 1]
        E[API Server 2]
    end

    subgraph Backend
        F[(Database)]
        G[Cache]
        H[Queue]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    D --> F
    D --> G
    E --> F
    E --> G
    D --> H
    E --> H
```

## Conclusion

This document contains **10 valid Mermaid diagrams** of various types:
1. Flowchart (2 instances)
2. Sequence Diagram
3. Gantt Chart
4. Class Diagram
5. State Diagram
6. Entity Relationship Diagram
7. Pie Chart
8. User Journey
9. Git Graph

It also includes:
- Regular markdown text
- Non-Mermaid code blocks (Python, JavaScript)
- Edge cases (empty mermaid block)
- Special characters and Unicode
- Nested structures (subgraphs)

This comprehensive test file ensures that the MermaidVisualizer can handle real-world documentation scenarios.
