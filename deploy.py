"""
test_rag Agent Engine 배포 스크립트

강남대학교 Multi-Agent 시스템을 Vertex AI Agent Engine에 배포합니다.
"""

import os
import sys
import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from test_rag.agent import root_agent

FLAGS = flags.FLAGS

flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP staging bucket.")
flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID.")
flags.DEFINE_string("user_id", "test_user", "User ID for session operations.")
flags.DEFINE_string("session_id", None, "Session ID for operations.")
flags.DEFINE_bool("create", False, "Creates a new deployment.")
flags.DEFINE_bool("delete", False, "Deletes an existing deployment.")
flags.DEFINE_bool("list", False, "Lists all deployments.")
flags.DEFINE_bool("create_session", False, "Creates a new session.")
flags.DEFINE_bool("list_sessions", False, "Lists all sessions for a user.")
flags.DEFINE_bool("get_session", False, "Gets a specific session.")
flags.DEFINE_bool("send", False, "Sends a message to the deployed agent.")
flags.DEFINE_string(
    "message",
    "2024년 입학생 공과대학 졸업 요건 알려줘",
    "Message to send to the agent.",
)

flags.mark_bool_flags_as_mutual_exclusive(
    ["create", "delete", "list", "create_session", "list_sessions", "get_session", "send"]
)

def create() -> None:
    """Creates a new deployment."""
    print("🚀 Starting deployment...")
    print()
    
    # Root agent를 AdkApp으로 래핑
    adk_app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )
    
    print("📦 Packaging test_rag...")
    
    # Agent Engine으로 배포
    remote_app = agent_engines.create(
        agent_engine=adk_app,
        requirements=[
            "google-cloud-aiplatform[adk,agent_engines]",
            "requests",
            "beautifulsoup4",
            "python-dotenv",
        ],
        extra_packages=["./test_rag"],
    )
    
    print()
    print("=" * 70)
    print("✅ Deployment successful!")
    print("=" * 70)
    print()
    print(f"📝 Resource ID: {remote_app.resource_name}")
    print()
    print("💾 Save this ID for later use!")
    print()
    print("🔑 Next steps:")
    print("   1. Create a session:")
    print(f"      python deploy.py --create_session \\")
    print(f"        --resource_id=\"{remote_app.resource_name}\"")
    print()
    print("   2. Send a message:")
    print(f"      python deploy.py --send \\")
    print(f"        --resource_id=\"{remote_app.resource_name}\" \\")
    print(f"        --session_id=\"<SESSION_ID>\" \\")
    print(f"        --message=\"2024년 졸업 요건 알려줘\"")

def delete(resource_id: str) -> None:
    """Deletes an existing deployment."""
    print(f"🗑️  Deleting deployment: {resource_id}")
    remote_app = agent_engines.get(resource_id)
    remote_app.delete(force=True)
    print(f"✅ Deleted: {resource_id}")

def list_deployments() -> None:
    """Lists all deployments."""
    print("📋 Listing all deployments...")
    print()
    
    deployments = agent_engines.list()
    
    if not deployments:
        print("❌ No deployments found.")
        return
    
    print("Deployments:")
    for i, deployment in enumerate(deployments, 1):
        print(f"  {i}. {deployment.resource_name}")

def create_session(resource_id: str, user_id: str) -> None:
    """Creates a new session."""
    print(f"🔑 Creating session for user: {user_id}")
    
    remote_app = agent_engines.get(resource_id)
    remote_session = remote_app.create_session(user_id=user_id)
    
    print()
    print("=" * 70)
    print("✅ Session created!")
    print("=" * 70)
    print()
    print(f"  Session ID: {remote_session.get('id') or remote_session}")
    
    # 선택적 필드들 (있으면 출력)
    if 'user_id' in remote_session:
        print(f"  User ID: {remote_session['user_id']}")
    if 'app_name' in remote_session:
        print(f"  App name: {remote_session['app_name']}")
    if 'last_update_time' in remote_session:
        print(f"  Last update: {remote_session['last_update_time']}")
    
    print()
    print("💡 Use this session ID with --session_id when sending messages.")

def list_sessions(resource_id: str, user_id: str) -> None:
    """Lists all sessions."""
    remote_app = agent_engines.get(resource_id)
    sessions = remote_app.list_sessions(user_id=user_id)
    
    print(f"📋 Sessions for user '{user_id}':")
    for session in sessions:
        print(f"  - {session['id']}")

def get_session(resource_id: str, user_id: str, session_id: str) -> None:
    """Gets a specific session."""
    remote_app = agent_engines.get(resource_id)
    session = remote_app.get_session(user_id=user_id, session_id=session_id)
    
    print("Session details:")
    print(f"  ID: {session.get('id') or session_id}")
    
    # 선택적 필드들
    if 'user_id' in session:
        print(f"  User ID: {session['user_id']}")
    if 'app_name' in session:
        print(f"  App name: {session['app_name']}")
    if 'last_update_time' in session:
        print(f"  Last update: {session['last_update_time']}")

def send_message(resource_id: str, user_id: str, session_id: str, message: str) -> None:
    """Sends a message."""
    print(f"📤 Sending message to session {session_id}:")
    print(f"Message: {message}")
    print()
    print("🤖 Response:")
    print("-" * 70)
    
    remote_app = agent_engines.get(resource_id)
    
    for event in remote_app.stream_query(
        user_id=user_id,
        session_id=session_id,
        message=message,
    ):
        print(event)

def main(argv=None):
    """Main function."""
    if argv is None:
        argv = flags.FLAGS(sys.argv)
    else:
        argv = flags.FLAGS(argv)
    
    load_dotenv()
    
    project_id = FLAGS.project_id if FLAGS.project_id else os.getenv("GOOGLE_CLOUD_PROJECT")
    location = FLAGS.location if FLAGS.location else os.getenv("VERTEX_AI_LOCATION")
    bucket = FLAGS.bucket if FLAGS.bucket else os.getenv("GOOGLE_CLOUD_STAGING_BUCKET")
    user_id = FLAGS.user_id
    
    if not project_id:
        print("❌ Missing: GOOGLE_CLOUD_PROJECT")
        print("   Set via --project_id or .env file")
        return
    
    if not location:
        print("❌ Missing: VERTEX_AI_LOCATION")
        print("   Set via --location or .env file")
        return
    
    if not bucket:
        print("❌ Missing: GOOGLE_CLOUD_STAGING_BUCKET")
        print("   Run: python create_staging_bucket.py")
        return
    
    vertexai.init(project=project_id, location=location, staging_bucket=bucket)
    
    if FLAGS.create:
        create()
    elif FLAGS.delete:
        if not FLAGS.resource_id:
            print("❌ --resource_id required for delete")
            return
        delete(FLAGS.resource_id)
    elif FLAGS.list:
        list_deployments()
    elif FLAGS.create_session:
        if not FLAGS.resource_id:
            print("❌ --resource_id required")
            return
        create_session(FLAGS.resource_id, user_id)
    elif FLAGS.list_sessions:
        if not FLAGS.resource_id:
            print("❌ --resource_id required")
            return
        list_sessions(FLAGS.resource_id, user_id)
    elif FLAGS.get_session:
        if not FLAGS.resource_id or not FLAGS.session_id:
            print("❌ --resource_id and --session_id required")
            return
        get_session(FLAGS.resource_id, user_id, FLAGS.session_id)
    elif FLAGS.send:
        if not FLAGS.resource_id or not FLAGS.session_id:
            print("❌ --resource_id and --session_id required")
            return
        send_message(FLAGS.resource_id, user_id, FLAGS.session_id, FLAGS.message)
    else:
        print("Please specify: --create, --delete, --list, --create_session, --list_sessions, --get_session, or --send")

if __name__ == "__main__":
    app.run(main)

