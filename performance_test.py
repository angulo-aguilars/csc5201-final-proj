import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
CATALOG_URL = 'http://localhost:5002/recipes'
LOGIN_URL = 'http://localhost:5001/users/login'

# Use a valid token for testing 
TEST_TOKEN ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NjU2MDUzMzB9.W4InAY2bEi3KdbRryziRne4jyi27n13KtI-QJyXRekE"
# Create a small dummy file for upload testing
with open('dummy_image.txt', 'w') as f:
    f.write("This is a dummy file for performance testing.")

def send_request():
    """Simulates a recipe creation request with form data."""
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}"
    }
    
    # Use files/data structure similar to curl -F
    files = {
        'image': ('dummy_image.txt', open('dummy_image.txt', 'rb'), 'text/plain')
    }
    data = {
        'title': f"Load Test Recipe {time.time()}",
        'instructions': 'Run instructions for a load test.'
    }

    start_time = time.time()
    try:
        response = requests.post(CATALOG_URL, headers=headers, data=data, files=files, timeout=5)
        # Check for success
        if response.status_code != 201:
            return None 
    except requests.exceptions.RequestException:
        # Request failed (timeout or connection error)
        return None
    finally:
        # Close the file handle used in the post request
        files['image'][1].close()

    end_time = time.time()
    return (end_time - start_time) * 1000 # Return latency in milliseconds


def run_load_test(num_workers, num_requests):
    """Runs the load test with specified concurrency and total requests."""
    print(f"\n--- Running Test: {num_requests} requests with {num_workers} workers ---")
    latencies = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all requests to the executor
        future_to_request = [executor.submit(send_request) for _ in range(num_requests)]
        
        # Collect results as they complete
        for future in future_to_request:
            result = future.result()
            if result is not None:
                latencies.append(result)

    if not latencies:
        print("Test failed: No successful responses recorded.")
        return 0, 0
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"Total Successful Requests: {len(latencies)} / {num_requests}")
    print(f"Average Latency: {avg_latency:.2f} ms")
    return avg_latency, len(latencies)

# --- EXECUTION ---
if __name__ == "__main__":
    # --- STEP 1: TEST SCENARIO 1 (Baseline: 1 Catalog Pod) ---
    # Manually ensure your Kubernetes deployment has 1 replica:
    # kubectl scale deployment catalog-service-deployment --replicas=1

    print("Scaling Catalog Service to 1 Pod (Manual Step Required)")
    time.sleep(3) 

    # Run tests for 1, 5, and 10 concurrent users
    run_load_test(num_workers=1, num_requests=50)
    run_load_test(num_workers=5, num_requests=50)
    run_load_test(num_workers=10, num_requests=50)


    # --- STEP 2: TEST SCENARIO 2 (Scaled: 4 Catalog Pods) ---
    # Manually scale up the deployment:
    # kubectl scale deployment catalog-service-deployment --replicas=4

    print("\nScaling Catalog Service to 4 Pods (Manual Step Required)")
    time.sleep(15) # Give Kubernetes time to spin up new pods

    # Run the same tests again
    run_load_test(num_workers=1, num_requests=50)
    run_load_test(num_workers=5, num_requests=50)
    run_load_test(num_workers=10, num_requests=50)
