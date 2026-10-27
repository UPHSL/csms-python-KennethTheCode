"""Web routes for the CSMS user interface."""

from datetime import date
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository
from csms.services.request_service import ServiceRequestStatusService
from csms.services.resident_deactivation_service import ResidentDeactivationService
from csms.services.resident_query_service import ResidentQueryService
from csms.services.resident_registration_service import ResidentRegistrationService
from csms.services.resident_update_service import ResidentUpdateService
from csms.services.resident_validator import ResidentValidator
from csms.services.service_request_query_service import ServiceRequestQueryService
from csms.services.service_request_submission_service import (
    ServiceRequestSubmissionService,
)
from csms.services.service_request_validator import ServiceRequestValidator

main_blueprint = Blueprint("main", __name__)


def get_db_path():
    return current_app.config.get("DATABASE_PATH", "csms.sqlite")


def get_resident_services():
    db_path = get_db_path()
    repository = ResidentRepository(db_path)
    validator = ResidentValidator()

    return {
        "repository": repository,
        "query": ResidentQueryService(repository),
        "registration": ResidentRegistrationService(validator, repository),
        "update": ResidentUpdateService(validator, repository),
        "deactivation": ResidentDeactivationService(repository),
    }


def get_service_request_services():
    db_path = get_db_path()
    resident_repo = ResidentRepository(db_path)
    request_repo = ServiceRequestRepository(db_path)
    validator = ServiceRequestValidator()

    return {
        "repository": request_repo,
        "query": ServiceRequestQueryService(request_repo),
        "submission": ServiceRequestSubmissionService(
            validator, resident_repo, request_repo
        ),
        "status": ServiceRequestStatusService(request_repo),
    }


@main_blueprint.get("/")
def index() -> str:
    """Display the Sprint 0 welcome page."""
    return render_template(
        "index.html",
        application_name=current_app.config.get("APP_NAME", "CSMS"),
        application_version=current_app.config.get("APP_VERSION", "0.1.0"),
        current_sprint=current_app.config.get("CURRENT_SPRINT", "Sprint 4"),
    )


@main_blueprint.get("/health")
def health():
    """Return a simple application health response."""
    return jsonify(
        {
            "application": current_app.config.get("APP_NAME", "CSMS"),
            "status": "ok",
            "version": current_app.config.get("APP_VERSION", "0.1.0"),
        }
    )


# ---------- Resident Management Interface Routes ----------


@main_blueprint.get("/residents")
def list_residents():
    services = get_resident_services()
    search_term = request.args.get("search", "")

    if search_term and search_term.strip():
        residents = services["query"].search_residents(search_term)
    else:
        residents = services["query"].list_residents()

    return render_template(
        "residents/index.html", residents=residents, search_term=search_term
    )


@main_blueprint.get("/residents/register")
def show_register_form():
    return render_template("residents/register.html", resident={}, errors=[])


@main_blueprint.post("/residents/register")
def register_resident():
    services = get_resident_services()

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    address = request.form.get("address", "").strip()
    contact_number = request.form.get("contact_number", "").strip()
    email = request.form.get("email", "").strip()

    candidate = Resident(
        first_name=first_name,
        last_name=last_name,
        address=address,
        contact_number=contact_number,
        email=email,
    )

    result = services["registration"].register_resident(candidate)

    if result.success:
        flash("Resident registered successfully.", "success")
        return redirect(url_for("main.list_residents"))

    return (
        render_template(
            "residents/register.html",
            resident={
                "first_name": first_name,
                "last_name": last_name,
                "address": address,
                "contact_number": contact_number,
                "email": email,
            },
            errors=result.errors,
        ),
        400,
    )


@main_blueprint.get("/residents/<int:resident_id>/edit")
def show_edit_form(resident_id):
    services = get_resident_services()
    resident = services["repository"].find_by_id(resident_id)

    if resident is None:
        return render_template("404.html", message="Resident not found"), 404

    return render_template("residents/edit.html", resident=resident, errors=[])


@main_blueprint.post("/residents/<int:resident_id>/edit")
def update_resident(resident_id):
    services = get_resident_services()

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    address = request.form.get("address", "").strip()
    contact_number = request.form.get("contact_number", "").strip()
    email = request.form.get("email", "").strip()

    result = services["update"].update_resident(
        resident_id,
        first_name=first_name,
        last_name=last_name,
        address=address,
        contact_number=contact_number,
        email=email,
    )

    if result.success:
        flash("Resident information updated successfully.", "success")
        return redirect(url_for("main.list_residents"))

    if result.not_found:
        return render_template("404.html", message="Resident not found"), 404

    existing = services["repository"].find_by_id(resident_id)
    form_data = {
        "id": resident_id,
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "contact_number": contact_number,
        "email": email,
        "status": existing.status if existing else "Active",
    }

    return (
        render_template(
            "residents/edit.html", resident=form_data, errors=result.errors
        ),
        400,
    )


@main_blueprint.post("/residents/<int:resident_id>/deactivate")
def deactivate_resident(resident_id):
    services = get_resident_services()
    result = services["deactivation"].deactivate_resident(resident_id)

    if result.not_found:
        return render_template("404.html", message="Resident not found"), 404

    flash("Resident deactivated successfully.", "success")
    return redirect(url_for("main.list_residents"))


# ---------- Service Request Management Interface Routes ----------


@main_blueprint.get("/service-requests")
def list_service_requests():
    services = get_service_request_services()
    search_term = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    try:
        requests_list = services["query"].search_service_requests(
            search_term=search_term, status_filter=status_filter
        )
    except ValueError:
        requests_list = []

    return render_template(
        "service_requests/index.html",
        service_requests=requests_list,
        search_term=search_term,
        status_filter=status_filter,
    )


@main_blueprint.get("/service-requests/new")
def show_submit_service_request_form():
    initial_resident_id = request.args.get("resident_id", "")
    return render_template(
        "service_requests/new.html",
        service_request={"resident_id": initial_resident_id},
        errors=[],
        error_message=None,
    )


@main_blueprint.post("/service-requests/new")
def submit_service_request():
    services = get_service_request_services()

    raw_resident_id = request.form.get("resident_id", "").strip()
    service_type = request.form.get("service_type", "").strip()
    description = request.form.get("description", "").strip()
    raw_date = request.form.get("date_requested", "").strip()

    parsed_resident_id = None
    if raw_resident_id and raw_resident_id.isdigit():
        parsed_resident_id = int(raw_resident_id)

    parsed_date = None
    if raw_date:
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError:
            parsed_date = raw_date

    candidate = ServiceRequest(
        resident_id=parsed_resident_id if parsed_resident_id is not None else raw_resident_id,
        service_type=service_type,
        description=description,
        date_requested=parsed_date,
    )

    result = services["submission"].submit_service_request(candidate)

    if result.success:
        flash("Service Request submitted successfully.", "success")
        return redirect(url_for("main.list_service_requests"))

    error_msg = None
    if result.resident_not_found:
        error_msg = "Resident not found."
    elif result.resident_inactive:
        error_msg = "Inactive Residents cannot submit new Service Requests."

    return (
        render_template(
            "service_requests/new.html",
            service_request={
                "resident_id": raw_resident_id,
                "service_type": service_type,
                "description": description,
                "date_requested": raw_date,
            },
            errors=result.errors,
            error_message=error_msg,
        ),
        400,
    )


@main_blueprint.get("/service-requests/<int:request_id>")
def view_service_request(request_id):
    services = get_service_request_services()
    service_request = services["query"].view_service_request(request_id)

    if service_request is None:
        return render_template("404.html", message="Service Request not found"), 404

    return render_template(
        "service_requests/view.html", service_request=service_request
    )


@main_blueprint.post("/service-requests/<int:request_id>/status")
def change_service_request_status(request_id):
    services = get_service_request_services()
    target_status = request.form.get("target_status", "").strip()

    result = services["status"].change_status(request_id, target_status)

    if result.not_found:
        return render_template("404.html", message="Service Request not found"), 404

    if not result.success:
        flash(f"Invalid status transition to {target_status}.", "error")
        return redirect(url_for("main.view_service_request", request_id=request_id))

    flash(f"Service Request status changed to {target_status}.", "success")
    return redirect(url_for("main.view_service_request", request_id=request_id))