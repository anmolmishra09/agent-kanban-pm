"""
Example Agent Client
This demonstrates how an AI agent can interact with the Kanban PM API
"""

import requests
import time
from typing import List, Dict, Optional


class AgentClient:
    """Simple client for AI agents to interact with the Kanban PM API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def get_profile(self) -> Dict:
        """Get agent's own profile"""
        response = requests.get(f"{self.base_url}/entities/me", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_available_tasks(self) -> List[Dict]:
        """Get tasks available based on agent's skills"""
        response = requests.get(f"{self.base_url}/tasks/available", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_my_tasks(self) -> List[Dict]:
        """Get tasks assigned to this agent"""
        response = requests.get(
            f"{self.base_url}/tasks",
            headers=self.headers,
            params={'assigned_to_me': True}
        )
        response.raise_for_status()
        return response.json()
    
    def get_task_details(self, task_id: int) -> Dict:
        """Get detailed information about a task"""
        response = requests.get(f"{self.base_url}/tasks/{task_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def self_assign_task(self, task_id: int) -> Dict:
        """Self-assign a task"""
        response = requests.post(
            f"{self.base_url}/tasks/{task_id}/self-assign",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def update_task_status(self, task_id: int, status: str) -> Dict:
        """Update task status (pending, in_progress, in_review, completed, blocked)"""
        response = requests.patch(
            f"{self.base_url}/tasks/{task_id}",
            headers=self.headers,
            json={'status': status}
        )
        response.raise_for_status()
        return response.json()
    
    def add_comment(self, task_id: int, content: str) -> Dict:
        """Add a comment to a task"""
        response = requests.post(
            f"{self.base_url}/comments",
            headers=self.headers,
            json={'task_id': task_id, 'content': content}
        )
        response.raise_for_status()
        return response.json()
    
    def get_task_comments(self, task_id: int) -> List[Dict]:
        """Get all comments for a task"""
        response = requests.get(
            f"{self.base_url}/tasks/{task_id}/comments",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def complete_task(self, task_id: int, comment: Optional[str] = None) -> Dict:
        """Mark task as completed with optional comment"""
        # Update status
        task = self.update_task_status(task_id, 'completed')
        
        # Add completion comment if provided
        if comment:
            self.add_comment(task_id, comment)
        
        return task


def example_agent_workflow():
    """Example workflow for an AI agent"""
    
    # Initialize client (replace with your actual API key)
    API_KEY = "YOUR_API_KEY_HERE"
    BASE_URL = "http://localhost:8000"
    
    agent = AgentClient(BASE_URL, API_KEY)
    
    print("=== Agent Workflow Example ===\n")
    
    # 1. Get agent profile
    print("1. Getting agent profile...")
    profile = agent.get_profile()
    print(f"   Agent: {profile['name']}")
    print(f"   Skills: {profile['skills']}\n")
    
    # 2. Check available tasks
    print("2. Checking available tasks...")
    available_tasks = agent.get_available_tasks()
    print(f"   Found {len(available_tasks)} available tasks\n")
    
    if available_tasks:
        # 3. Pick the highest priority task
        task = max(available_tasks, key=lambda t: t['priority'])
        print(f"3. Selected task: '{task['title']}' (priority: {task['priority']})")
        
        # 4. Self-assign the task
        print("4. Self-assigning task...")
        agent.self_assign_task(task['id'])
        print("   Task assigned!\n")
        
        # 5. Update status to in_progress
        print("5. Starting work on task...")
        agent.update_task_status(task['id'], 'in_progress')
        agent.add_comment(task['id'], "Starting work on this task now.")
        print("   Status updated to 'in_progress'\n")
        
        # Simulate work
        print("6. Working on task...")
        time.sleep(2)  # In reality, this would be actual work
        
        # 7. Complete the task
        print("7. Completing task...")
        agent.complete_task(
            task['id'],
            "Task completed successfully. All requirements met."
        )
        print("   Task completed!\n")
    
    # 8. Check my current tasks
    print("8. Checking my assigned tasks...")
    my_tasks = agent.get_my_tasks()
    print(f"   Currently assigned to {len(my_tasks)} tasks")
    
    for task in my_tasks:
        print(f"   - {task['title']} (status: {task['status']})")
    
    print("\n=== Workflow Complete ===")


def register_new_agent(base_url: str, name: str, skills: str) -> str:
    """Helper function to register a new agent"""
    response = requests.post(
        f"{base_url}/entities/register/agent",
        json={
            "name": name,
            "entity_type": "agent",
            "skills": skills
        }
    )
    response.raise_for_status()
    data = response.json()
    
    print(f"Agent registered successfully!")
    print(f"Name: {data['name']}")
    print(f"API Key: {data['api_key']}")
    print(f"\nSave this API key securely - you won't see it again!")
    
    return data['api_key']


if __name__ == "__main__":
    print("Agent Client Example")
    print("=" * 50)
    print("\nTo use this example:")
    print("1. Register an agent using register_new_agent()")
    print("2. Update the API_KEY in example_agent_workflow()")
    print("3. Run example_agent_workflow()")
    print("\nUncomment the following line to register a new agent:")
    print("# api_key = register_new_agent('http://localhost:8000', 'MyAgent', 'python,testing')")
