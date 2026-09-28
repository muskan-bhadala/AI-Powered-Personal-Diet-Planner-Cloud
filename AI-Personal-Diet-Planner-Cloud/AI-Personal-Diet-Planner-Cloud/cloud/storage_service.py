"""
cloud/storage_service.py

CLOUD OBJECT STORAGE SERVICE
------------------------------
Cloud databases store STRUCTURED rows (see database_service.py). Cloud
object storage stores FILES/BLOBS (images, PDFs, exports) addressed by a
path/key rather than by SQL columns — like AWS S3, Google Cloud Storage,
or Firebase Storage.

This module simulates that object storage using a local folder
("storage_bucket/"), so the project runs with zero cloud cost. Every
function here maps 1:1 onto a real cloud SDK call, which is noted in the
comments, so swapping in real cloud storage later only means rewriting
this one file.
"""

import os
import uuid

BUCKET_DIR = os.environ.get(
    "STORAGE_BUCKET_PATH",
    os.path.join(os.path.dirname(__file__), "..", "storage_bucket"),
)


def _ensure_bucket():
    os.makedirs(BUCKET_DIR, exist_ok=True)


def _user_dir(user_id):
    path = os.path.join(BUCKET_DIR, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def upload_file(user_id, filename, file_bytes):
    """
    Simulates: s3_client.put_object(...) / bucket.blob(path).upload_from_...()

    Stores bytes under storage_bucket/<user_id>/<uuid>_<filename> so two
    users can never collide, and returns the storage_path to save in the
    database (see database_service.save_file_record).
    """
    _ensure_bucket()
    safe_name = os.path.basename(filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    user_dir = _user_dir(user_id)
    full_path = os.path.join(user_dir, unique_name)
    with open(full_path, "wb") as f:
        f.write(file_bytes)
    # storage_path is what we persist in the DB — a "cloud key", not a raw
    # filesystem path, mirroring how you'd store an S3 object key.
    storage_path = f"{user_id}/{unique_name}"
    return storage_path


def download_file(storage_path):
    """Simulates: s3_client.get_object(...) / blob.download_as_bytes()"""
    full_path = os.path.join(BUCKET_DIR, storage_path)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "rb") as f:
        return f.read()


def delete_file(storage_path):
    """Simulates: s3_client.delete_object(...) / blob.delete()"""
    full_path = os.path.join(BUCKET_DIR, storage_path)
    if os.path.exists(full_path):
        os.remove(full_path)
        return True
    return False
