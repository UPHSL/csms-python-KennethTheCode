# CSMS v1.0.0 Release Notes

## 1. RELEASE
* **Application:** Community Services Management System
* **Short Name:** CSMS
* **Release:** v1.0.0
* **Release Type:** Final Course Release

---

## 2. RELEASE SUMMARY
CSMS v1.0.0 provides a comprehensive, production-ready community services platform for local barangay and municipal administration. The system enables community service staff to register and manage Resident profiles, process Service Requests through a controlled status workflow, and observe real-time aggregate operational metrics through a system dashboard.

---

## 3. RESIDENT MANAGEMENT CAPABILITIES
* **Registration & Persistence:** Register new Residents with complete contact information and initial Active status.
* **Validation & Data Integrity:** Strict validation on names, contact numbers, email formatting, and addresses.
* **Search & Retrieval:** Case-insensitive text search and partial name/address matching.
* **Information Updates:** Edit existing Resident profiles while protecting resident IDs and system status.
* **Soft Deactivation:** Soft deactivation changes status to Inactive without physical record deletion.

---

## 4. SERVICE REQUEST MANAGEMENT CAPABILITIES
* **Submission & Validation:** Submit service requests for Active Residents.
* **Eligibility Protection:** Automatic rejection of service requests submitted for missing or Inactive Residents.
* **Controlled Workflow:** Strict status transitions (`Pending` -> `In Progress` -> `Completed` / `Cancelled`). Terminal states (`Completed` and `Cancelled`) are immutable.
* **Querying & Filtering:** Filter requests by text search, status filters, and combined search-and-status criteria.

---

## 5. DASHBOARD CAPABILITIES
* **Real-time Aggregation:** Persistence-level SQL counting (`COUNT(*)`, `WHERE`) for Residents and Service Requests.
* **Derived Metrics:** Calculates `Open Service Requests` dynamically (`Pending + In Progress`).
* **Recent Activity:** Displays top 5 recent service requests ordered by `date_requested DESC, id DESC` with direct links to details.

---

## 6. QUALITY AND HARDENING
* **Defensive Input Handling:** Graceful handling of invalid URLs, malformed numeric IDs, and missing records (404/400).
* **HTTP Idempotency:** Guaranteed GET request read-only safety across all pages.
* **Regression Testing:** Passed 196 automated tests across full system regression testing.

---

## 7. FINAL VERIFICATION
* **Final Regression Run 1:** PASS (196 tests passed)
* **Final Regression Run 2:** PASS (196 tests passed)
* **Application Startup:** PASS
* **`/health` Endpoint:** PASS (`200 OK`, reports version 1.0.0)
* **Dashboard:** PASS
* **Resident Management:** PASS
* **Service Request Management:** PASS
* **Final Release Version:** 1.0.0

---

## 8. KNOWN LIMITATIONS
No known release-blocking limitations remain within the defined CSMS v1.0.0 scope.