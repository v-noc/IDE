# Data Model and Schema Documentation

This document outlines the ArangoDB data model for the V-NOC project. The design uses a graph-based approach with distinct document and edge collections.

## High-Level Plan

The data model is designed to be a foundation for a user-centric application. The core entities are:

-   **Users**: The primary actors in the system.
-   **Posts**: Content created by users.
-   **Relationships**: Edges that define how entities are connected (e.g., a user follows another user).

This structure allows for flexible and powerful queries, such as "find all posts from users I follow" or "recommend users with similar followers."

## Base Models

All data models inherit from one of two base models to ensure consistency and provide audit trails.

-   `BaseDocument`: The foundation for all document collections.
    -   `_key`: The unique document key (optional, as it's assigned on creation).
    -   `created_at`: UTC timestamp of when the document was created.
    -   `updated_at`: UTC timestamp of the last update.
-   `BaseEdge`: The foundation for all edge collections. Inherits from `BaseDocument`.
    -   `_from`: The document ID of the source node.
    -   `_to`: The document ID of the destination node.

## Document Collections

### `users`

Stores user profile information.

-   **`username`** (string, required): The unique, user-provided identifier.
-   **`email`** (string, required): The user's unique email address. Used for notifications and account recovery.
-   **`display_name`** (string, optional): A public-facing name that can be changed by the user.
-   **`bio`** (string, optional): A short biography or description.
-   **`status`** (string, default: `"active"`): The account status (e.g., `active`, `inactive`, `banned`).

### `posts`

Stores content created by users.

-   **`author_key`** (string, required): The `_key` of the user document that created this post. This creates an implicit link to the author.
-   **`content`** (string, required): The main body of the post.

## Edge Collections

### `follows`

Represents a "follow" relationship between two users. This is a directed edge from the follower to the followee.

-   **`_from`**: `users/{follower_key}`
-   **`_to`**: `users/{followee_key}`
-   This edge currently has no additional properties, but could be extended to include things like notification settings.

---

This improved design provides a solid and scalable foundation for the application. As new features are added, you can create new models and collection managers and integrate them into the `DatabaseService`.
