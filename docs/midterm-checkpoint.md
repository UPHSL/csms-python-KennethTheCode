# T10 Midterm Checkpoint - Manage Service Request Status

## 1. Developer Information

* **Name:** Paule Kenneth D. Dela rosa
* **GitHub Username:** Kenneth the code
* **Primary Technology Stack:** Python, SQLite
* **T10 Branch:** `feature/t10-service-request-status`

## 2. My T10 Implementation

For T10, I created a service that handles status updates for existing service requests. The service first checks if the service request exists using its ID. It then checks if the new status is supported and whether the status change follows the allowed transition rules.

The allowed changes are **Pending to In Progress or Cancelled**, and **In Progress to Completed or Cancelled**. Completed and Cancelled are final statuses, so they cannot be changed anymore.

If the request does not exist, the status is invalid, or the transition is not allowed, no changes are made to the database. If the transition is valid, only the status of the request is updated, and the updated request is returned.

## 3. My Transition Rules

The supported statuses are:

* Pending
* In Progress
* Completed
* Cancelled

The allowed transitions are:

* Pending → In Progress
* Pending → Cancelled
* In Progress → Completed
* In Progress → Cancelled

The following changes are not allowed:

* Pending → Completed
* In Progress → Pending
* Completed → any other status
* Cancelled → any other status
* Changing to the same status
* Unsupported statuses such as Approved, Rejected, Processing, or Done

## 4. Files I Changed

### `src/csms/repositories/service_request_repository.py`

Added the `update_status()` method to update only the status of an existing service request in the database.

### `src/csms/services/request_service.py`

Added the `ServiceRequestStatusService` to validate the supported statuses and allowed status transitions before updating a request.

### `tests/test_service_request_status.py`

Added 14 tests covering valid and invalid transitions, final statuses, unsupported statuses, missing IDs, data preservation, and status persistence.

### `docs/midterm-checkpoint.md`

Added documentation describing the T10 implementation, transition rules, tests, and development experience.

## 5. Problem I Encountered

During development, I encountered a formatting issue after running `git diff --check`. I reviewed the modified files and removed the extra whitespace.

I also had an issue with my Git configuration because my username and email were not set. I fixed this by using the `git config` command to set them. After fixing these problems, I continued working on the feature and confirmed that the tests were still passing.

## 6. My Student-Designed Test

### Test Name

`test_updated_status_is_persisted`

### What It Verifies

This test checks if a valid status update is properly saved to the database. The test first changes a request from Pending to In Progress. It then creates a new repository instance and retrieves the same request to verify that its status is still In Progress.

### Why I Added It

I added this test to make sure that the status update is actually stored in the database and not just changed temporarily in memory.

## 7. Tools and References Used

* Python
* Pytest
* SQLite
* Terminal
* Claude
* Git and GitHub
* VS Code
