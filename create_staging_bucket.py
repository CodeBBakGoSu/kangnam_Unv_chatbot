"""
GCP Staging Bucket 생성 스크립트

Agent Engine 배포를 위한 staging bucket을 us-east4 리전에 생성합니다.
"""

import subprocess
import sys
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "kangnam-backend")
BUCKET_NAME = f"{PROJECT_ID}-agent-staging"
LOCATION = "us-east4"

def run_command(cmd):
    """명령어 실행 및 결과 반환"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_bucket_exists():
    """버킷 존재 여부 확인"""
    cmd = f"gsutil ls gs://{BUCKET_NAME}"
    success, output = run_command(cmd)
    return success

def create_bucket():
    """Staging bucket 생성"""
    print(f"🪣 Creating staging bucket: gs://{BUCKET_NAME}")
    print(f"📍 Location: {LOCATION}")
    print(f"🏷️  Project: {PROJECT_ID}")
    print()
    
    # 버킷 존재 여부 확인
    if check_bucket_exists():
        print(f"✅ Bucket gs://{BUCKET_NAME} already exists!")
        print()
        print("📝 Add this to your .env file:")
        print(f"GOOGLE_CLOUD_STAGING_BUCKET=gs://{BUCKET_NAME}")
        return True
    
    # 버킷 생성
    cmd = f"gsutil mb -p {PROJECT_ID} -l {LOCATION} -c STANDARD gs://{BUCKET_NAME}"
    
    print("🚀 Creating bucket...")
    success, output = run_command(cmd)
    
    if success:
        print(f"✅ Successfully created: gs://{BUCKET_NAME}")
        print()
        print("📝 Add this to your .env file:")
        print(f"GOOGLE_CLOUD_STAGING_BUCKET=gs://{BUCKET_NAME}")
        print()
        print("💡 Next steps:")
        print(f"   1. Add the line above to your .env file")
        print(f"   2. Run: python deploy.py --create")
        return True
    else:
        print(f"❌ Failed to create bucket:")
        print(output)
        print()
        print("💡 Troubleshooting:")
        print("   1. Check if you have permission: gcloud auth list")
        print("   2. Check if project exists: gcloud projects list")
        print("   3. Enable Storage API: gcloud services enable storage.googleapis.com")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("  GCP Staging Bucket Creator")
    print("=" * 70)
    print()
    
    create_bucket()

