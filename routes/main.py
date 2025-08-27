from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db
from utils import generate_card
import os

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return redirect(url_for("auth.login"))

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", balance=current_user.balance)

@main_bp.route("/recharge", methods=["GET", "POST"])
@login_required
def recharge():
    if request.method == "POST":
        amount = int(request.form.get("amount"))
        if amount >= 50:
            current_user.balance += amount
            db.session.commit()
            flash("Recharge successful!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Minimum recharge is ₹50", "danger")
    return render_template("recharge.html")

@main_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    if request.method == "POST":
        if current_user.balance >= 30:
            name = request.form.get("name")
            father = request.form.get("father")
            dob = request.form.get("dob")
            address = request.form.get("address")

            front_img, back_img, pdf_file = generate_card(name, father, dob, address)

            current_user.balance -= 30
            db.session.commit()

            return render_template(
                "download.html",
                front=front_img,
                back=back_img,
                pdf=pdf_file
            )
        else:
            flash("Insufficient balance. Please recharge.", "danger")
            return redirect(url_for("main.recharge"))
    return render_template("generate.html")
