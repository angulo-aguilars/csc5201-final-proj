Recipe Management System 
CSC5201 - Final Project
Sandra Angulo-Aguilar

This project implements a scalable recipe management system using a microservices architecture, contanerized with Docker, and orchestrated with Kubernetes. It features secure user authentication through JWT and recipe management with file upload capabilities.

Application Description:
User Service
- Uses Flask/Python
- Uses PostgreSQL for database
- Handles user registration, login, and issues secure JSON Web Tokens

Catalog Service
- Uses Flask/Python
- Uses MongoDB for database
- Handles CRUD operations for recipes, validates JWT for authorization, manages file uploads.

All services are exposed via Kubernetes services, with the User Service accessible on port 5001 and the Catalog Service accessible on port 5002 through local port forwarding.

Installation & Deployment 
The following steps help deploy the application locally using Docker and Kubernetes

Prerequisites:
- Docker Desktop with Kubernetes enabled or a running Minikube cluster
- kubectl command line tool
- Python 3.10+ and pip
- A Docker Hub account, or local registry, for pushing images

1. Build and Push Docker Images
Navigate into each service directory, build the image, and push it to your Docker registry.
2. Deploy to Kubernetes
Apply the Kubernetes YAML manifests to deploy the databases, Persistent Volume Claims and services.
3. Port Forwarding
The application services run inside the cluster but are exposed locally via port forwarding. You must run the port forward commands in separate terminal windows and keep them running while using the application

API Documentation & Use Cases 
The API is accessed via http://localhost:5001 for the User and http://localhost:5002 for the catalog. All recipe endpoints require a valid JWT through the Authorization: Bearer <token> header

Use Case 1: User Registration and Login
For registration:
- endpoint: /users/register
- method: POST
- Creates a new user in PostgreSQL
- Request Body: {"username": "testuser", "password": "securepassword"}

For login:
- endpoint: /users/login
- method: POST
- Authenticates the user and returns a JWT
- Request Body:  {"username": "testuser", "password": "securepassword"}

Example: Login to Obtain JWT
curl -X POST http://localhost:5001/users/login \
-H "Content-Type: application/json" \
-d '{"username": "sandra47", "password": "sandra1234"}'
Response will include: {"token":"eyJhbGciOiJIUzI1NiI..."}

Use Case 2: Create a recipe with Image Upload
This is a multipart/form-data request, which requires the -F flag for file and text fields
- endpoint: /recipes
- method: POST
- Creates a recipe, saved the image to PVC, and metadata to MongoDB
- Data fields: title(text), instructions(text), image(file)

Example: Create Recipe
curl -X POST http://localhost:5002/recipes \
-H "Authorization: Bearer [YOUR_JWT_TOKEN]" \
-F "title=Hashbrown Bites" \
-F "instructions=Bake for 15 minutes." \
-F "image=@/path/to/hashbrown-bites.jpg"
Response: {"id":"69351940d74351dddc2ec18d", "image_url": "/app/images/hashbrown-bites.jpg", "message": "Recipe created"}

Use Case 3: Retrieve all recipes for current user 
- endpoint: /recipes
- method: GET
- returns a list of recipes created by the authenticated user

Example: Get recipes
curl -X GET http://localhost:5002/recipes \
-H "Authorization: Bearer [YOUR_JWT_TOKEN]"
Response: [{"title": "Hashbrown Bites", "instructions": "...", "image_url": "/app/images/..."}]
