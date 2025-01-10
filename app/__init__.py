from main import app
from database import init_db

# import subprocess
# import sys

# def run_docker_compose():
#     try:
#         subprocess.run(["docker-compose", "build"], check=True)
#         subprocess.run(["docker-compose", "up"], check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"Error running docker-compose: {e}")
#         sys.exit(1)


    

if __name__ == "__main__":
    # run_docker_compose()
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
