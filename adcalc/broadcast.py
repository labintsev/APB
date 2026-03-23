import logging
from logging import log

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from .models import db, Organisation, Region, Broadcast
from .utils import calculate_cost
from werkzeug.utils import secure_filename
import pandas as pd
import io
from functools import wraps
from flask import session


def login_required(f):
    """Decorator to require login for a route"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


broadcast_bp = Blueprint("broadcast", __name__, url_prefix="/broadcast")


@broadcast_bp.context_processor
def inject_functions():
    return dict(calculate_cost=calculate_cost)


@broadcast_bp.route("/list")
@login_required
def broadcast_list():
    """List all broadcasts with their details"""
    page = request.args.get("page", 1, type=int)
    pagination = Broadcast.query.paginate(page=page, per_page=50)
    broadcasts = pagination.items
    return render_template(
        "broadcast/broadcast-list.html", broadcasts=broadcasts, pagination=pagination
    )


@broadcast_bp.route("/create", methods=["GET", "POST"])
@login_required
def broadcast_create():
    """Create a new broadcast"""
    if request.method == "POST":
        # Get form data
        org_id = request.form.get("org_id")
        smi_name = request.form.get("smi_name")
        smi_rating = request.form.get("smi_rating")
        smi_male_proportion = request.form.get("smi_male_proportion")
        district_name = request.form.get("district_name")
        district_population = request.form.get("district_population")
        region_id = request.form.get("region_id")
        frequency = request.form.get("frequency")
        power = request.form.get("power")

        # Parse numeric fields
        try:
            smi_rating = float(smi_rating) if smi_rating else None
        except ValueError:
            smi_rating = None
        try:
            smi_male_proportion = (
                float(smi_male_proportion) if smi_male_proportion else None
            )
        except ValueError:
            smi_male_proportion = None
        try:
            district_population = (
                int(district_population) if district_population else None
            )
        except ValueError:
            district_population = None
        try:
            power = float(power) if power else None
        except ValueError:
            power = None

        new_broadcast = Broadcast(
            org_id=org_id,
            smi_name=smi_name,
            smi_rating=smi_rating,
            smi_male_proportion=smi_male_proportion,
            district_name=district_name,
            district_population=district_population,
            region_id=region_id,
            frequency=frequency,
            power=power,
        )

        db.session.add(new_broadcast)
        db.session.commit()
        return redirect(url_for("broadcast.broadcast_list"))
    else:
        # Show the form for creating a new broadcast
        organisations = Organisation.query.all()
        regions = Region.query.all()
        smis = [
            s[0] for s in db.session.query(Broadcast.smi_name).distinct().all() if s[0]
        ]
        districts = [
            d[0]
            for d in db.session.query(Broadcast.district_name).distinct().all()
            if d[0]
        ]
        return render_template(
            "broadcast/broadcast-create.html",
            organisations=organisations,
            regions=regions,
            smis=smis,
            districts=districts,
        )


@broadcast_bp.route("/<int:broadcast_id>/update", methods=["GET", "POST"])
@login_required
def broadcast_update(broadcast_id):
    """Update a broadcast by ID"""
    broadcast = Broadcast.query.get_or_404(broadcast_id)

    if request.method == "POST":
        # Update the broadcast (embedded fields)
        broadcast.org_id = request.form.get("org_id")
        broadcast.smi_name = request.form.get("smi_name")
        try:
            broadcast.smi_rating = (
                float(request.form.get("smi_rating"))
                if request.form.get("smi_rating")
                else None
            )
        except ValueError:
            broadcast.smi_rating = None
        try:
            broadcast.smi_male_proportion = (
                float(request.form.get("smi_male_proportion"))
                if request.form.get("smi_male_proportion")
                else None
            )
        except ValueError:
            broadcast.smi_male_proportion = None
        broadcast.district_name = request.form.get("district_name")
        try:
            broadcast.district_population = (
                int(request.form.get("district_population"))
                if request.form.get("district_population")
                else None
            )
        except ValueError:
            broadcast.district_population = None
        broadcast.frequency = request.form.get("frequency")
        try:
            broadcast.power = (
                float(request.form.get("power")) if request.form.get("power") else None
            )
        except ValueError:
            broadcast.power = None
        broadcast.region_id = request.form.get("region_id")
        db.session.commit()
        return redirect(url_for("broadcast.broadcast_list"))
    else:
        # Show the form for updating the broadcast
        organisations = Organisation.query.all()
        regions = Region.query.all()
        smis = [
            s[0] for s in db.session.query(Broadcast.smi_name).distinct().all() if s[0]
        ]
        districts = [
            d[0]
            for d in db.session.query(Broadcast.district_name).distinct().all()
            if d[0]
        ]
        return render_template(
            "broadcast/broadcast-update.html",
            broadcast=broadcast,
            organisations=organisations,
            regions=regions,
            smis=smis,
            districts=districts,
        )


@broadcast_bp.route("/<int:broadcast_id>/delete", methods=["POST"])
@login_required
def broadcast_delete(broadcast_id):
    """Delete a broadcast by ID"""
    broadcast = Broadcast.query.get_or_404(broadcast_id)
    db.session.delete(broadcast)
    db.session.commit()
    return redirect(url_for("broadcast.broadcast_list"))


@broadcast_bp.route("/upload_excel", methods=["POST"])
@login_required
def broadcast_upload_excel():
    """Upload broadcasts from an Excel file using pandas"""
    file = request.files.get("excel_file")
    if not file or file.filename == "":
        flash("Ошибка: Не выбран файл для загрузки", "error")
        return redirect(url_for("broadcast.broadcast_list"))

    filename = secure_filename(file.filename)
    try:
        # Read Excel file into DataFrame
        try:
            df = pd.read_excel(file, sheet_name="table")
        except ValueError:
            file.seek(0)
            df = pd.read_excel(file)
        required_columns = {
            "org_id",
            "region_id",
            "smi_name",
            "smi_rating",
            "smi_male_proportion",
            "district_name",
            "district_population",
            "frequency",
            "power",
        }
        if not required_columns.issubset(set(df.columns.tolist())):
            raise ValueError(
                "Некорректные названия столбцов в Excel файле. Ожидаются: org_id, region_id, smi_name, smi_rating, smi_male_proportion, district_name, district_population, frequency, power"
            )

        # drop empty rows if any
        df = df.dropna(how="all")

        def to_optional_float(value):
            if pd.isna(value):
                return None
            try:
                return float(value)
            except Exception:
                raise ValueError(f"Поле должно содержать только числовые значения: {value}")
        success_count = 0
        for _, row in df.iterrows():
            org_id = row.get("org_id")
            region_id = row.get("region_id")
            frequency = row.get("frequency")
            if pd.isna(org_id):
                log(logging.WARNING, "Обязательное поле org_id не должно быть пустым")
                continue
            if pd.isna(region_id):
                log(logging.WARNING, "Обязательное поле region_id не должно быть пустым")
                continue
            if pd.isna(frequency):
                log(logging.WARNING, "Обязательное поле frequency не должно быть пустым")
                continue

            try:
                org_id = int(org_id)
            except Exception:
                raise ValueError(f"org_id должен быть целым числом: {org_id}")
            try:
                region_id = int(region_id)
            except Exception:
                raise ValueError(f"region_id должен быть целым числом: {region_id}")

            org = Organisation.query.filter_by(id=org_id).first()
            if not org:
                raise ValueError(f"Не найдена организация с ID {org_id}")
            region = Region.query.filter_by(id=region_id).first()
            if not region:
                raise ValueError(f"Не найден регион с ID {region_id}")


            smi_rating = to_optional_float(row.get("smi_rating"))
            smi_male_proportion = to_optional_float(row.get("smi_male_proportion"))
            district_population = None
            if not pd.isna(row.get("district_population")):
                try:
                    district_population = int(row.get("district_population"))
                except Exception:
                    raise ValueError(
                        f"Поле district_population должно быть числовым: {row.get('district_population')}"
                    )
            power = to_optional_float(row.get("power"))

            broadcast = Broadcast(
                org_id=org.id,
                smi_name=row.get("smi_name"),
                smi_rating=smi_rating,
                smi_male_proportion=smi_male_proportion,
                district_name=row.get("district_name"),
                district_population=district_population,
                region_id=region.id,
                frequency=str(row.get("frequency")) if not pd.isna(row.get("frequency")) else None,
                power=power,
            )
            db.session.add(broadcast)
            success_count += 1

        db.session.commit()
        flash(f"Файл успешно загружен, импортировано {success_count} записей", "success")

    # catch specific ValueErrors for better user feedback
    except ValueError as e:
        error_msg = str(e)
        flash(error_msg, "error")

    # catch all other exceptions to prevent app crash and provide feedback
    except Exception as e:
        flash(str(e), "error")
        print(f"Exception: {e}")

    return redirect(url_for("broadcast.broadcast_list"))


@broadcast_bp.route("/download_excel")
@login_required
def broadcast_download_excel():
    """Return an Excel file containing all broadcasts"""
    broadcasts = Broadcast.query.all()
    rows = []
    for b in broadcasts:
        rows.append({
            "org_id": b.org_id,
            "org_name": b.org.name if b.org else "",
            "region_id": b.region_id,
            "smi_name": b.smi_name,
            "smi_rating": b.smi_rating,
            "smi_male_proportion": b.smi_male_proportion,
            "district_name": b.district_name,
            "district_population": b.district_population,
            "frequency": b.frequency,
            "power": b.power,
            "price": calculate_cost(b),
        })
    df = pd.DataFrame(rows, columns=[
        "org_id",
        "org_name",
        "region_id",
        "smi_name",
        "smi_rating",
        "smi_male_proportion",
        "district_name",
        "district_population",
        "frequency",
        "power",
        "price",
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="table")
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="broadcasts.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
