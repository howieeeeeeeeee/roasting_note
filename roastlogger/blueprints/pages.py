"""Server-rendered page routes."""

from __future__ import annotations

from datetime import datetime

from bson.objectid import ObjectId
from flask import Blueprint, Response, redirect, render_template, request, url_for

from models.roast_helpers import create_draft_roast
from roastlogger.database import get_beans_collection, get_roasts_collection
from roastlogger.routing import register_unprefixed_routes
from roastlogger.services.lifecycle import annotate_roast_lifecycle


blueprint = Blueprint("pages", __name__)


def favicon():
    return Response(status=204)


def index():
    roasts = list(get_roasts_collection().find({"archived": {"$ne": True}}))
    roasts.sort(
        key=lambda roast: roast.get("roast_start_time")
        or roast.get("roast_date")
        or datetime.min,
        reverse=True,
    )
    for roast in roasts:
        annotate_roast_lifecycle(roast)
        if roast.get("bean_id"):
            bean = get_beans_collection().find_one(
                {"_id": ObjectId(roast["bean_id"])}
            )
            roast["bean_name"] = bean["name"] if bean else "Unknown Bean"
            roast["bean_color"] = (
                bean.get("color", "#6B8E6F") if bean else "#6B8E6F"
            )
        else:
            roast["bean_name"] = "Not Set"
            roast["bean_color"] = "#6B8E6F"

        if roast.get("roast_start_time") and roast.get("roast_end_time"):
            duration = (
                roast["roast_end_time"] - roast["roast_start_time"]
            ).total_seconds()
            roast["total_duration_seconds"] = int(duration)
        if roast.get("key_timings") and roast.get("total_duration_seconds"):
            fc_start = None
            for timing in roast["key_timings"]:
                if "First Crack Start" in timing["event_name"]:
                    fc_start = timing["time_seconds"]
            if fc_start:
                roast["time_after_fc"] = (
                    roast["total_duration_seconds"] - fc_start
                )
    return render_template("index.html", roasts=roasts)


def beans_list():
    filter_out_of_stock = request.args.get("filter_out_of_stock", "true") == "true"
    sort_by = request.args.get("sort_by", "name")
    sort_order = request.args.get("sort_order", "asc")
    query = {"archived": {"$ne": True}}
    if filter_out_of_stock:
        query["stock_grams"] = {"$gt": 0}
    sort_field = {
        "name": "name",
        "price": "unit_price_per_kg",
        "date": "purchase_date",
        "stock": "stock_grams",
    }.get(sort_by, "name")
    beans = list(
        get_beans_collection().find(query).sort(
            sort_field,
            1 if sort_order == "asc" else -1,
        )
    )
    return render_template(
        "beans_list.html",
        beans=beans,
        filter_out_of_stock=filter_out_of_stock,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def beans_add_form():
    return render_template("beans_form.html", bean=None, is_edit=False)


def beans_detail(bean_id):
    bean = get_beans_collection().find_one(
        {"_id": ObjectId(bean_id), "archived": {"$ne": True}}
    )
    if not bean:
        return "Bean not found", 404
    roasts = list(
        get_roasts_collection()
        .find({"bean_id": ObjectId(bean_id), "archived": {"$ne": True}})
        .sort("roast_date", -1)
    )
    for roast in roasts:
        annotate_roast_lifecycle(roast)
        roast["bean_name"] = bean["name"]
        roast["bean_color"] = bean.get("color", "#6B8E6F")
        if roast.get("roast_start_time") and roast.get("roast_end_time"):
            duration = (
                roast["roast_end_time"] - roast["roast_start_time"]
            ).total_seconds()
            roast["total_duration_seconds"] = int(duration)
        if roast.get("key_timings") and roast.get("total_duration_seconds"):
            fc_start = None
            for timing in roast["key_timings"]:
                if "First Crack Start" in timing["event_name"]:
                    fc_start = timing["time_seconds"]
            if fc_start:
                roast["time_after_fc"] = (
                    roast["total_duration_seconds"] - fc_start
                )
    return render_template("beans_detail.html", bean=bean, roasts=roasts)


def beans_edit_form(bean_id):
    bean = get_beans_collection().find_one(
        {"_id": ObjectId(bean_id), "archived": {"$ne": True}}
    )
    if not bean:
        return "Bean not found", 404
    return render_template("beans_form.html", bean=bean, is_edit=True)


def roast_new():
    roast_id = create_draft_roast(get_roasts_collection())
    return redirect(url_for("roast_live", roast_id=roast_id))


def roast_live(roast_id):
    roast = get_roasts_collection().find_one(
        {"_id": ObjectId(roast_id), "archived": {"$ne": True}}
    )
    if not roast:
        return "Roast not found", 404
    annotate_roast_lifecycle(roast)
    beans = list(
        get_beans_collection().find({"archived": {"$ne": True}}).sort("name", 1)
    )
    return render_template("roast_live.html", roast=roast, beans=beans)


def roast_detail(roast_id):
    roast = get_roasts_collection().find_one(
        {"_id": ObjectId(roast_id), "archived": {"$ne": True}}
    )
    if not roast:
        return "Roast not found", 404
    if roast.get("bean_id"):
        bean = get_beans_collection().find_one(
            {"_id": ObjectId(roast["bean_id"])}
        )
        roast["bean_name"] = bean["name"] if bean else "Unknown Bean"
    else:
        roast["bean_name"] = "Not Set"
    if roast.get("roast_start_time") and roast.get("roast_end_time"):
        duration = (
            roast["roast_end_time"] - roast["roast_start_time"]
        ).total_seconds()
        roast["roast_duration_seconds"] = int(duration)
    return render_template("roast_detail.html", roast=roast)


def roast_edit_form(roast_id):
    roast = get_roasts_collection().find_one(
        {"_id": ObjectId(roast_id), "archived": {"$ne": True}}
    )
    if not roast:
        return "Roast not found", 404
    beans = list(
        get_beans_collection().find({"archived": {"$ne": True}}).sort("name", 1)
    )
    return render_template("roast_edit.html", roast=roast, beans=beans)


register_unprefixed_routes(
    blueprint,
    [
        ("/favicon.ico", "favicon", favicon, ["GET"]),
        ("/", "index", index, ["GET"]),
        ("/beans", "beans_list", beans_list, ["GET"]),
        ("/beans/add", "beans_add_form", beans_add_form, ["GET"]),
        ("/beans/detail/<bean_id>", "beans_detail", beans_detail, ["GET"]),
        ("/beans/edit/<bean_id>", "beans_edit_form", beans_edit_form, ["GET"]),
        ("/roast/new", "roast_new", roast_new, ["GET"]),
        ("/roast/live/<roast_id>", "roast_live", roast_live, ["GET"]),
        ("/roast/detail/<roast_id>", "roast_detail", roast_detail, ["GET"]),
        ("/roast/edit/<roast_id>", "roast_edit_form", roast_edit_form, ["GET"]),
    ],
)
