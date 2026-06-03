from fastmcp import FastMCP
import firebase_admin
from firebase_admin import credentials, db
from uuid import uuid4
import os
import json
import sys
import traceback


# --- Firebase initialization (errors printed before MCP starts) ---
firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")

try:
    if firebase_creds_json:
        print("[firebase] Parsing FIREBASE_CREDENTIALS from environment...", flush=True)
        cred_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(cred_dict)
    else:
        print("[firebase] FIREBASE_CREDENTIALS not set, falling back to serviceAccountKey.json", flush=True)
        cred = credentials.Certificate("serviceAccountKey.json")

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://school-management-mcp-default-rtdb.firebaseio.com/"
        }
    )
    print("[firebase] Firebase initialized successfully.", flush=True)
except Exception as e:
    print(f"[firebase] ERROR: Firebase initialization failed: {e}", flush=True)
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()
    # Exit so Railway surfaces the failure clearly rather than running a broken server
    sys.exit(1)
# ------------------------------------------------------------------

mcp = FastMCP("SchoolManagementMCP")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Simple liveness probe — returns 200 OK so Railway (and you) can verify the server is up."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok"})


@mcp.tool
def add_student(
    name: str,
    student_class: str,
    roll_no: str,
    contact_number: str,
    address: str,
):
    """
    Add a new student.
    """

    student_id = str(uuid4())

    student_data = {
        "name": name,
        "class": student_class,
        "roll_no": roll_no,
        "contact_number": contact_number,
        "address": address,
        "fee_paid": False,
    }

    db.reference(f"students/{student_id}").set(student_data)

    return {
        "success": True,
        "student_id": student_id,
        "message": "Student added successfully",
    }


@mcp.tool
def get_student(student_id: str):
    """
    Get student details.
    """

    student = db.reference(f"students/{student_id}").get()

    if not student:
        return {"success": False, "message": "Student not found"}

    return student


@mcp.tool
def get_all_students():
    """
    Fetch all students.
    """

    students = db.reference("students").get()

    return students or {}


@mcp.tool
def update_student(
    student_id: str,
    name: str = None,
    student_class: str = None,
    roll_no: str = None,
    contact_number: str = None,
    address: str = None,
):
    """
    Update student information.
    """

    ref = db.reference(f"students/{student_id}")

    student = ref.get()

    if not student:
        return {"success": False, "message": "Student not found"}

    updates = {}

    if name:
        updates["name"] = name

    if student_class:
        updates["class"] = student_class

    if roll_no:
        updates["roll_no"] = roll_no

    if contact_number:
        updates["contact_number"] = contact_number

    if address:
        updates["address"] = address

    ref.update(updates)

    return {
        "success": True,
        "message": "Student updated successfully",
    }


@mcp.tool
def update_fee_status(student_id: str, fee_paid: bool):
    """
    Update fee payment status.
    """

    ref = db.reference(f"students/{student_id}")

    student = ref.get()

    if not student:
        return {"success": False, "message": "Student not found"}

    ref.update({"fee_paid": fee_paid})

    return {
        "success": True,
        "message": "Fee status updated",
    }


@mcp.tool
def get_contact_number(student_id: str):
    """
    Get student's contact number.
    """

    student = db.reference(f"students/{student_id}").get()

    if not student:
        return {"success": False, "message": "Student not found"}

    return {
        "student_name": student["name"],
        "contact_number": student["contact_number"],
    }


@mcp.tool
def delete_student(student_id: str):
    """
    Delete a student.
    """

    ref = db.reference(f"students/{student_id}")

    student = ref.get()

    if not student:
        return {"success": False, "message": "Student not found"}

    ref.delete()

    return {
        "success": True,
        "message": "Student deleted successfully",
    }


@mcp.tool
def search_student(name: str):
    """
    Search students by name.
    """

    students = db.reference("students").get()

    if not students:
        return []

    results = []

    for student_id, student in students.items():
        if name.lower() in student["name"].lower():
            results.append(
                {
                    "student_id": student_id,
                    **student,
                }
            )

    return results


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )