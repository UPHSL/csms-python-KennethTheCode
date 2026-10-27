"""Web routes for the CSMS user interface."""

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
from csms.repositories.resident_repository import ResidentRepository
from csms.services.resident_deactivation_service import ResidentDeactivationService
from csms.services.resident_query_service import ResidentQueryService
from csms.services.resident_registration_service import ResidentRegistrationService
from csms.services.resident_update_service import ResidentUpdateService
from csms.services.resident_validator import ResidentValidator

main_blueprint = Blueprint("main", __name__)


def get_resident_services():
    db_path = current_app.config.get("DATABASE_PATH", "csms.sqlite")
    repository = ResidentRepository(db_path)
    validator = ResidentValidator()

    return {
        "repository": repository,
        "query": ResidentQueryService(repository),
        "registration": ResidentRegistrationService(validator, repository),
        "update": ResidentUpdateService(validator, repository),
        "deactivation": ResidentDeactivationService(repository),
    }


@main_blueprint.get("/")
def index() -> str:
    """Display the Sprint 0 welcome page."""
    return render_template(
        "index.html",
        application_name=current_app.config["APP_NAME"],
        application_version=current_app.config["APP_VERSION"],
        current_sprint=current_app.config["CURRENT_SPRINT"],
    )


@main_blueprint.get("/health")
def health():
    """Return a simple application health response."""
    return jsonify(
        {
            "application": current_app.config["APP_NAME"],
            "status": "ok",
            "version": current_app.config["APP_VERSION"],
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